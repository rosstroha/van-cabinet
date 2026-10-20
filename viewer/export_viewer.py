"""Rebuild the cabinet concept and export actual CAD geometry for the browser."""
from pathlib import Path
import hashlib
import json
import math
import runpy

VIEWER = Path(__file__).resolve().parent
ROOT = VIEWER.parent
OUTPUT = VIEWER / 'dist' / 'model.json'
MM = 25.4

def point(v):
    return [round(a / MM, 6) for a in (v.x, v.y, v.z)]

def mesh_record(record, positioned):
    shape = positioned(record, False)
    vertices, triangles = shape.tessellate(0.3, 0.1)
    positions = [v for vertex in vertices for v in point(vertex)]
    indices = [int(i) for tri in triangles for i in tri]
    if not positions or not indices or not all(math.isfinite(v) for v in positions):
        raise ValueError('Invalid geometry: ' + record['name'])
    if min(indices) < 0 or max(indices) >= len(vertices):
        raise ValueError('Invalid indices: ' + record['name'])
    edges = []
    for edge in shape.Edges():
        points, _ = edge.sample(2 if edge.geomType() == 'LINE' else 0.2)
        if edge.IsClosed() and points:
            points.append(points[0])
        for a, b in zip(points, points[1:]):
            edges.extend(point(a)); edges.extend(point(b))
    bounds = shape.BoundingBox()
    lo = [bounds.xmin, bounds.ymin, bounds.zmin]
    hi = [bounds.xmax, bounds.ymax, bounds.zmax]
    return dict(name=record['name'], kind=record['kind'], panel=bool(record['panel']),
        moving=record['moving'], positions=positions, indices=indices, edges=edges,
        center=[round((a+b)/(2*MM),6) for a,b in zip(lo,hi)],
        size=[round((b-a)/MM,6) for a,b in zip(lo,hi)])

def main():
    model = runpy.run_path(str(ROOT / 'build_concept.py'))
    records = [mesh_record(p, model['positioned']) for p in model['parts'] + model['env']]
    if any(v <= 0 for part in records for v in part['size']):
        raise ValueError('Invalid part bounds')
    revision = hashlib.sha256((ROOT/'build_concept.py').read_bytes() + (ROOT/'parameters.json').read_bytes()).hexdigest()[:12]
    payload = dict(schemaVersion=1, modelRevision=revision, units='inches',
        dimensions=[model[k] for k in ('W','D','H')], parameters=model['p'],
        coordinates=dict(x='right',y='front toward wall',z='up',frontY=0), parts=records)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(OUTPUT.relative_to(ROOT)),revision=revision,parts=len(records),
        triangles=sum(len(p['indices'])//3 for p in records),bytes=OUTPUT.stat().st_size),indent=2))

if __name__ == '__main__':
    main()
