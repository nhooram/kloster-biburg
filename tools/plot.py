import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
b=[x for x in json.load(open('church_lod2.json')) if x['id']=='DEBY_LOD2_5717218'][0]
CX,CY,Z0=709796,5408275,375.0
P=[(k,[(p[0]-CX,p[1]-CY,p[2]-Z0) for p in ps]) for k,ps in b['polys']]
fig=plt.figure(figsize=(16,8))
ax=fig.add_subplot(121)
for k,ps in P:
    if k=='RoofSurface':
        xs=[p[0] for p in ps];ys=[p[1] for p in ps]
        ax.fill(xs,ys,alpha=.3,edgecolor='k'); 
        for p in ps: ax.annotate(f"{p[2]:.1f}",(p[0],p[1]),fontsize=6)
ax.set_aspect('equal');ax.grid(True)
ax3=fig.add_subplot(122,projection='3d')
col={'RoofSurface':'#c55','WallSurface':'#ddd','GroundSurface':'#555'}
ax3.add_collection3d(Poly3DCollection([ps for k,ps in P],facecolors=[col[k] for k,ps in P],edgecolor='k',lw=.3))
ax3.set_xlim(-35,35);ax3.set_ylim(-35,35);ax3.set_zlim(0,45);ax3.view_init(25,-60);ax3.set_box_aspect((70,70,45))
plt.tight_layout();plt.savefig('lod2.png',dpi=110)
g=[ps for k,ps in P if k=='GroundSurface']
for ps in g: print('ground',[(round(p[0],2),round(p[1],2)) for p in ps])
