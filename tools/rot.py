import json, math
b=[x for x in json.load(open('church_lod2.json')) if x['id']=='DEBY_LOD2_5717218'][0]
CX,CY,Z0=709796,5408275,375.0
a=math.atan2(-7.03+15.16, 1.28+23.96); print('axis deg', math.degrees(a))
c,s=math.cos(-a),math.sin(-a)
def T(p): x,y=p[0]-CX,p[1]-CY; return (round(x*c-y*s,2), round(x*s+y*c,2), round(p[2]-Z0,2))
P=[(k,[T(p) for p in ps]) for k,ps in b['polys']]
json.dump(P,open('church_local.json','w'))
for k,ps in P:
    if k!='WallSurface': print(k, ps[:-1] if len(ps)<12 else f'{len(ps)} pts x[{min(p[0] for p in ps)},{max(p[0] for p in ps)}] y[{min(p[1] for p in ps)},{max(p[1] for p in ps)}] z[{min(p[2] for p in ps)},{max(p[2] for p in ps)}]')
