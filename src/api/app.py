"""Laptop 1 API. Set PATHSNAP_EVAL_DATA_DIR and PATHSNAP_DECODER before use."""

import importlib
import logging
import os
import re
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.features.create_training_data import align_reference_route, build_candidate_table
from src.features.feature_engineering import GPSObservation, extract_gps_features
from src.features.road_network import build_road_network
from src.training.train_models import FEATURE_COLUMNS, SOURCE_COLUMNS


app = FastAPI(title="PathSnap Laptop 1 API")
TRIP_ID_PATTERN = re.compile(r"^[0-9]{8}$")
DATA_DIR = Path(os.getenv("PATHSNAP_EVAL_DATA_DIR", "data/evaluation"))
MODEL_PATH = Path(os.getenv("PATHSNAP_MODEL_PATH", "results/training/gradient-boosting/model.joblib"))
DECODER_SPEC = os.getenv("PATHSNAP_DECODER", "")
LOG_PATH = Path(os.getenv("PATHSNAP_API_LOG", "results/api/requests.log"))

logger = logging.getLogger("pathsnap.api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


@app.middleware("http")
async def log_request(request, call_next):
    try:
        response = await call_next(request)
        logger.info("request method=%s path=%s status=%s", request.method, request.url.path,
                    response.status_code)
        return response
    except Exception:
        logger.exception("request failed method=%s path=%s", request.method, request.url.path)
        raise


class PredictRequest(BaseModel):
    trip_id: str


def _trip_folder(trip_id):
    if not TRIP_ID_PATTERN.fullmatch(trip_id):
        raise HTTPException(400, "trip_id must be an eight-digit string")
    folder = DATA_DIR / trip_id
    if not folder.is_dir():
        raise HTTPException(404, "Evaluation trip not found")
    return folder


def _read_rows(path, columns):
    if not path.is_file():
        raise HTTPException(404, f"Missing trip file: {path.name}")
    try:
        frame = pd.read_csv(path, sep=r"\s+", header=None, names=columns)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise HTTPException(422, f"Invalid trip file: {path.name}") from exc
    if frame.empty or frame.isna().any().any():
        raise HTTPException(422, f"Empty or incomplete trip file: {path.name}")
    return frame


def _decoder():
    """Configured callable: decode(candidates_by_observation) -> one arc ID per observation."""
    if not DECODER_SPEC:
        raise HTTPException(503, "HMM/Viterbi decoder integration pending")
    try:
        module_name, function_name = DECODER_SPEC.split(":", 1)
        decoder = getattr(importlib.import_module(module_name), function_name)
        if not callable(decoder):
            raise TypeError("Decoder is not callable")
        return decoder
    except (ValueError, ImportError, AttributeError, TypeError) as exc:
        raise HTTPException(503, "Configured HMM/Viterbi decoder is unavailable") from exc


@app.get("/health")
def health():
    return {
        "status": "running",
        "model_available": MODEL_PATH.is_file(),
        "evaluation_data_available": DATA_DIR.is_dir(),
        "decoder_configured": bool(DECODER_SPEC),
    }


@app.get("/trips")
def trips():
    if not DATA_DIR.is_dir():
        raise HTTPException(503, "Evaluation dataset directory is unavailable")
    return {"trip_ids": sorted(
        folder.name for folder in DATA_DIR.iterdir()
        if folder.is_dir() and TRIP_ID_PATTERN.fullmatch(folder.name)
        and all((folder / f"{folder.name}.{suffix}").is_file()
                for suffix in ("track", "nodes", "arcs"))
    )}


@app.post("/predict")
def predict(request: PredictRequest):
    trip_id = request.trip_id
    logger.info("predict requested trip_id=%s", trip_id)
    try:
        folder = _trip_folder(trip_id)
        track = _read_rows(folder / f"{trip_id}.track", ["longitude", "latitude", "timestamp"])
        nodes = _read_rows(folder / f"{trip_id}.nodes", ["longitude", "latitude"])
        arcs = _read_rows(folder / f"{trip_id}.arcs", ["from_node", "to_node"])
        if not MODEL_PATH.is_file():
            raise HTTPException(503, "Trained model is unavailable")
        # No reference file is opened or passed to feature engineering here.
        trip = {"trip_id": trip_id, "track": track, "nodes": nodes, "arcs": arcs, "route": []}
        candidates = build_candidate_table(trip, include_labels=False)
        if not candidates:
            raise HTTPException(422, "No road candidates generated for this trip")
        feature_frame = pd.DataFrame(candidates).rename(columns=SOURCE_COLUMNS)
        try:
            model = joblib.load(MODEL_PATH)
            probabilities = model.predict_proba(feature_frame.loc[:, list(FEATURE_COLUMNS)])
            class_one = list(model.classes_).index(1)
        except Exception as exc:
            logger.exception("prediction failed trip_id=%s", trip_id)
            raise HTTPException(500, "Model prediction failed") from exc

        by_observation = [[] for _ in range(len(track))]
        for candidate, probability in zip(candidates, probabilities[:, class_one]):
            by_observation[int(candidate["observation_idx"])].append({
                "arc_id": int(candidate["candidate_arc_id"]),
                "probability": float(probability),
                "from_node_id": int(candidate["from_node_id"]),
                "to_node_id": int(candidate["to_node_id"]),
                "road_length_m": float(candidate["road_length_m"]),
                "along_arc_fraction": float(candidate["along_arc_fraction"]),
            })
        if any(not row for row in by_observation):
            raise HTTPException(422, "Some GPS observations have no road candidates")

        # Decoder input contains candidates and probabilities only; no reference data.
        decoder = _decoder()
        try:
            predicted = [int(arc_id) for arc_id in decoder(by_observation)]
        except Exception as exc:
            logger.exception("decoder failed trip_id=%s", trip_id)
            raise HTTPException(500, "HMM/Viterbi decoding failed") from exc
        if len(predicted) != len(by_observation) or any(
            arc_id not in {candidate["arc_id"] for candidate in row}
            for arc_id, row in zip(predicted, by_observation)
        ):
            raise HTTPException(500, "Decoder returned invalid arc IDs or path length")

        # Reference data is read only after the prediction path is final.
        reference = _read_rows(folder / f"{trip_id}.route", ["arc_id"])
        try:
            network = build_road_network(nodes.itertuples(index=False, name=None),
                                         arcs.itertuples(index=False, name=None))
            observations = [GPSObservation(*row) for row in track.itertuples(index=False, name=None)]
            gps = extract_gps_features(observations, network.projection)
            expected = align_reference_route(
                [(row["x_m"], row["y_m"]) for row in gps],
                reference["arc_id"].astype(int).tolist(), network,
            )
        except (ValueError, TypeError, IndexError) as exc:
            raise HTTPException(422, "Reference route cannot be evaluated") from exc
        segments = {segment.arc_id: segment for segment in network.segments}
        connected = sum(
            left == right or segments[left].to_node_id == segments[right].from_node_id
            for left, right in zip(predicted, predicted[1:])
        )
        transitions = max(0, len(predicted) - 1)
        result = {
            "trip_id": trip_id,
            "predicted_arc_ids": predicted,
            "accuracy": sum(a == b for a, b in zip(predicted, expected)) / len(expected),
            "accuracy_method": "per-observation agreement with server-side route alignment heuristic",
            "route_continuity": {
                "connected_transitions": connected,
                "total_transitions": transitions,
                "fraction": connected / transitions if transitions else 1.0,
            },
            "diagnostics": {
                "observations": len(track),
                "candidates": len(candidates),
                "decoder": DECODER_SPEC,
            },
        }
        logger.info("predict completed trip_id=%s observations=%s", trip_id, len(track))
        return result
    except HTTPException as exc:
        logger.warning("predict rejected trip_id=%s status=%s detail=%s", trip_id, exc.status_code, exc.detail)
        raise
