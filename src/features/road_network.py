"""Metric road-segment geometry for PathSnap."""
from __future__ import annotations
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, radians

@dataclass(frozen=True)
class MetricProjection:
    longitude_origin: float
    latitude_origin: float
    @classmethod
    def from_coordinates(cls, coords):
        if not coords:
            raise ValueError("At least one coordinate is required.")
        return cls(sum(p[0] for p in coords)/len(coords), sum(p[1] for p in coords)/len(coords))
    def project(self, longitude, latitude):
        if not isfinite(longitude) or not isfinite(latitude):
            raise ValueError("Coordinates must be finite.")
        r = 6_371_008.8
        return (radians(longitude-self.longitude_origin)*r*cos(radians(self.latitude_origin)),
                radians(latitude-self.latitude_origin)*r)

@dataclass(frozen=True)
class RoadSegment:
    arc_id: int
    from_node_id: int
    to_node_id: int
    start_xy: tuple[float, float]
    end_xy: tuple[float, float]
    length_m: float
    bearing_deg: float

@dataclass(frozen=True)
class RoadNetwork:
    projection: MetricProjection
    nodes_lonlat: tuple
    nodes_xy: tuple
    segments: tuple

def bearing_degrees(a, b):
    """Compass bearing clockwise from north."""
    return degrees(atan2(b[0]-a[0], b[1]-a[1])) % 360.0

def heading_difference(a, b):
    if a is None or b is None:
        return None
    return abs((a-b+180.0) % 360.0 - 180.0)

def point_to_segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    den = dx*dx + dy*dy
    if den == 0:
        return hypot(p[0]-a[0], p[1]-a[1])
    t = min(1.0, max(0.0, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
    return hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)

def build_road_network(nodes_lonlat, arcs):
    """Arc IDs are zero-based row positions in the .arcs file."""
    nodes = tuple((float(lon), float(lat)) for lon, lat in nodes_lonlat)
    if not nodes:
        raise ValueError("The node list is empty.")
    if any(not isfinite(lon) or not isfinite(lat) for lon, lat in nodes):
        raise ValueError("Node coordinates must be finite.")
    projection = MetricProjection.from_coordinates(nodes)
    xy = tuple(projection.project(*p) for p in nodes)
    segments = []
    for arc_id, arc in enumerate(arcs):
        if len(arc) != 2:
            raise ValueError(f"Arc {arc_id} must contain exactly two node IDs.")
        u, v = int(arc[0]), int(arc[1])
        if not (0 <= u < len(xy) and 0 <= v < len(xy)):
            raise ValueError(f"Arc {arc_id} references an out-of-range node ID.")
        a, b = xy[u], xy[v]
        segments.append(RoadSegment(arc_id, u, v, a, b,
            hypot(b[0]-a[0], b[1]-a[1]), bearing_degrees(a, b)))
    return RoadNetwork(projection, nodes, xy, tuple(segments))

def project_onto_segment(point, start, end):
    """Return closest projected point and its fraction along the segment."""
    dx, dy = end[0]-start[0], end[1]-start[1]
    den = dx*dx + dy*dy
    fraction = 0.0 if den == 0 else min(1.0, max(0.0, ((point[0]-start[0])*dx+(point[1]-start[1])*dy)/den))
    return (start[0]+fraction*dx, start[1]+fraction*dy), fraction
