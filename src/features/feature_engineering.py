"""GPS motion and candidate-level feature extraction."""
from dataclasses import dataclass
from math import hypot,isfinite
from .candidate_generation import Candidate
from .road_network import bearing_degrees,heading_difference

@dataclass(frozen=True)
class GPSObservation:
    longitude: float
    latitude: float
    timestamp_s: float

def extract_gps_features(observations,projection):
    rows=[]; prev_xy=prev_t=None
    for i,o in enumerate(observations):
        if any(not isfinite(float(v)) for v in (o.longitude,o.latitude,o.timestamp_s)):
            raise ValueError(f"GPS observation {i} is non-finite.")
        xy=projection.project(o.longitude,o.latitude); gap=None if prev_t is None else o.timestamp_s-prev_t
        speed=heading=None
        if prev_xy is not None and gap is not None and gap>0:
            dx,dy=xy[0]-prev_xy[0],xy[1]-prev_xy[1]; d=hypot(dx,dy); speed=d/gap
            if d>0.01: heading=bearing_degrees(prev_xy,xy)
        rows.append({"gps_idx":i,"longitude":o.longitude,"latitude":o.latitude,
            "timestamp_s":o.timestamp_s,"x_m":xy[0],"y_m":xy[1],
            "time_gap_s":gap,"speed_mps":speed,"heading_deg":heading})
        prev_xy,prev_t=xy,o.timestamp_s
    return rows

def engineer_candidate_features(gps_row,candidate,segment):
    return {"observation_idx":gps_row["gps_idx"],"candidate_arc_id":candidate.arc_id,
        "distance_m":candidate.distance_m,"projection_x_m":candidate.projection_x_m,
        "projection_y_m":candidate.projection_y_m,"along_arc_fraction":candidate.along_arc_fraction,
        "speed_mps":gps_row["speed_mps"],
        "bearing_difference":heading_difference(gps_row["heading_deg"],segment.bearing_deg),
        "gps_heading_deg":gps_row["heading_deg"],"road_bearing_deg":segment.bearing_deg,
        "road_length_m":segment.length_m,"time_gap_s":gps_row["time_gap_s"],
        "from_node_id":segment.from_node_id,"to_node_id":segment.to_node_id}
