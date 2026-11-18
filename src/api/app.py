"""Laptop 1 API. Set PATHSNAP_EVAL_DATA_DIR to the trip-folder parent."""

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
from src.reconstruction.evaluation import evaluate_route
from src.reconstruction.hmm_viterbi import gps_step_distances, group_candidate_rows, viterbi_decode
from src.training.train_models import FEATURE_COLUMNS, SOURCE_COLUMNS


app = FastAPI(title="PathSnap Laptop 1 API")
TRIP_ID_PATTERN = re.compile(r"^[0-9]{8}$")
DATA_DIR = Path(os.getenv("PATHSNAP_EVAL_DATA_DIR", "data/evaluation"))
MODEL_PATH = Path(os.getenv("PATHSNAP_MODEL_PATH", "results/training/gradient-boosting/model.joblib"))
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


@app.get("/health")
def health():
    return {
        "status": "running",
        "model_available": MODEL_PATH.is_file(),
        "evaluation_data_available": DATA_DIR.is_dir(),
        "decoder_available": True,
    }


@app.get("/trips")
def trips():
    if not DATA_DIR.is_dir():
        raise HTTPException(503, "Evaluation dataset directory is unavailable")
    return {"trip_ids": sorted(
        folder.name for folder in DATA_DIR.iterdir()
        if folder.is_dir() and TRIP_ID_PATTERN.fullmatch(folder.name)
        and all((folder / f"{folder.name}.{suffix}").is_file()
                for suffix in ("track", "nodes", "arcs", "route"))
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
        try:
            network = build_road_network(nodes.itertuples(index=False, name=None),
                                         arcs.itertuples(index=False, name=None))
            observations = [GPSObservation(*row) for row in track.itertuples(index=False, name=None)]
            gps = extract_gps_features(observations, network.projection)
            points = [(row["x_m"], row["y_m"]) for row in gps]
            candidates = build_candidate_table(trip, include_labels=False)
        except (ValueError, TypeError, IndexError) as exc:
            raise HTTPException(422, "Trip geometry or GPS data is invalid") from exc
        if not network.segments:
            raise HTTPException(422, "Trip road network has no arcs")
        feature_frame = pd.DataFrame(candidates).rename(columns=SOURCE_COLUMNS)
        try:
            model = joblib.load(MODEL_PATH)
            probabilities = (
                model.predict_proba(feature_frame.loc[:, list(FEATURE_COLUMNS)])[
                    :, list(model.classes_).index(1)
                ] if candidates else []
            )
        except Exception as exc:
            logger.exception("prediction failed trip_id=%s", trip_id)
            raise HTTPException(500, "Model prediction failed") from exc

        try:
            by_observation = group_candidate_rows(candidates, probabilities, len(track))
            decoded = viterbi_decode(
                by_observation, network,
                observed_distances_m=gps_step_distances(points),
                projected_points_xy=points,
            )
            predicted = decoded.predicted_arc_ids
        except Exception as exc:
            logger.exception("decoder failed trip_id=%s", trip_id)
            raise HTTPException(500, "HMM/Viterbi decoding failed") from exc
        if len(predicted) != len(track) or any(arc_id is None for arc_id in predicted):
            raise HTTPException(500, "Decoder did not return one arc ID per GPS observation")

        # Reference data is read only after the prediction path is final.
        reference = _read_rows(folder / f"{trip_id}.route", ["arc_id"])
        try:
            expected = align_reference_route(
                points,
                reference["arc_id"].astype(int).tolist(), network,
            )
            metrics = evaluate_route(predicted, expected, network)
        except (ValueError, TypeError, IndexError) as exc:
            raise HTTPException(422, "Reference route cannot be evaluated") from exc
        result = {
            "trip_id": trip_id,
            "predicted_arc_ids": predicted,
            "accuracy": metrics["accuracy"],
            "accuracy_method": "per-observation agreement with server-side route alignment heuristic",
            "route_continuity": metrics["route_continuity"],
            "diagnostics": {
                "observations": len(track),
                "candidates": len(candidates),
                "empty_candidate_observations": len(decoded.empty_candidate_observations),
                "fallback_observations": len(decoded.fallback_observation_indices),
                "disconnected_transitions": decoded.disconnected_transition_count,
            },
        }
        logger.info("predict completed trip_id=%s observations=%s", trip_id, len(track))
        return result
    except HTTPException as exc:
        logger.warning("predict rejected trip_id=%s status=%s detail=%s", trip_id, exc.status_code, exc.detail)
        raise
