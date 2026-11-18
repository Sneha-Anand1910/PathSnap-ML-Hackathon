"""Candidate generation using an efficient spatial grid."""
from collections import defaultdict
from dataclasses import dataclass
from math import floor
from .road_network import point_to_segment_distance, project_onto_segment

@dataclass(frozen=True)
class Candidate:
    arc_id: int
    distance_m: float
    projection_x_m: float
    projection_y_m: float
    along_arc_fraction: float

class SegmentGrid:
    def __init__(self, segments, cell_size_m=100.0):
        if cell_size_m <= 0: raise ValueError("cell_size_m must be positive.")
        self.cell_size_m=float(cell_size_m); self.cells=defaultdict(set)
        for i,s in enumerate(segments):
            for x in range(self._cell(min(s.start_xy[0],s.end_xy[0])),self._cell(max(s.start_xy[0],s.end_xy[0]))+1):
                for y in range(self._cell(min(s.start_xy[1],s.end_xy[1])),self._cell(max(s.start_xy[1],s.end_xy[1]))+1):
                    self.cells[x,y].add(i)
    def _cell(self,value): return floor(value/self.cell_size_m)
    def query(self,point,radius):
        result=set()
        for x in range(self._cell(point[0]-radius),self._cell(point[0]+radius)+1):
            for y in range(self._cell(point[1]-radius),self._cell(point[1]+radius)+1):
                result.update(self.cells.get((x,y),()))
        return sorted(result)

def generate_candidates(point_xy,network,radius_m=100.0,*,segment_grid=None,max_candidates=None):
    if radius_m<=0: raise ValueError("radius_m must be positive.")
    if max_candidates is not None and max_candidates<=0: raise ValueError("max_candidates must be positive.")
    grid=segment_grid or SegmentGrid(network.segments); found=[]
    for i in grid.query(point_xy,radius_m):
        s=network.segments[i]; projected,fraction=project_onto_segment(point_xy,s.start_xy,s.end_xy)
        distance=point_to_segment_distance(point_xy,s.start_xy,s.end_xy)
        if distance<=radius_m:
            found.append(Candidate(s.arc_id,distance,projected[0],projected[1],fraction))
    found.sort(key=lambda c:(c.distance_m,c.arc_id))
    return found if max_candidates is None else found[:max_candidates]
