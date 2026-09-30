import re, json
from xml.etree import ElementTree as ET
CX, CY = 709796, 5408275
ns = {'bldg':'http://www.opengis.net/citygml/building/2.0','gml':'http://www.opengis.net/gml','core':'http://www.opengis.net/citygml/2.0'}
out = []
for ev, el in ET.iterparse('lod2_708_5408.gml'):
    if el.tag.endswith('}Building') and el.tag.startswith('{http://www.opengis.net/citygml/building'):
        polys = []
        for surf in el.iter():
            kind = surf.tag.split('}')[1]
            if kind in ('RoofSurface','WallSurface','GroundSurface'):
                for pl in surf.iter('{http://www.opengis.net/gml}posList'):
                    v = list(map(float, pl.text.split()))
                    polys.append((kind, [v[i:i+3] for i in range(0, len(v), 3)]))
        pts = [p for _, ps in polys for p in ps]
        if pts:
            mx = sum(p[0] for p in pts)/len(pts); my = sum(p[1] for p in pts)/len(pts)
            if abs(mx-CX) < 80 and abs(my-CY) < 80:
                attrs = {c.tag.split('}')[1]: (c.text or '').strip() for c in el if c.text and c.text.strip()}
                gen = {a.get('name'): ''.join(a.itertext()).strip() for a in el.iter('{http://www.opengis.net/citygml/generics/2.0}stringAttribute')}
                out.append({'id': el.get('{http://www.opengis.net/gml}id'), 'c': (mx-CX, my-CY), 'attrs': attrs, 'gen': gen, 'polys': polys})
        el.clear()
json.dump(out, open('church_lod2.json', 'w'))
for b in out:
    zs = [p[2] for _, ps in b['polys'] for p in ps]
    print(b['id'], [round(x) for x in b['c']], b['attrs'], b['gen'], 'z', min(zs), max(zs), len(b['polys']))
