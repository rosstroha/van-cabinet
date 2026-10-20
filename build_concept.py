"""Rebuild a preliminary cabinet, STEP assemblies, panel list and review views."""
from pathlib import Path
import json, csv, itertools, math
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'concept'
DEFAULTS = dict(width=30.0, depth=18.0, height=33.0, plywood=0.5,
    top_thickness=0.75, rear_gap=0.875, left_clear=12.5,
    toe_kick_height=3.0, toe_kick_recess=2.0, water_entry_height=24.0,
    water_entry_from_wall=3.0, water_entry_diameter=1.5,
    dog_depth=12.0, dog_deck_z=18.0, dog_slide_space=0.75,
    toilet_travel=18.0, dog_travel=12.0, dog_weight_lb=45, person_weight_lb=200)
PFILE = ROOT / 'parameters.json'
if not PFILE.exists():
    PFILE.write_text(json.dumps(DEFAULTS, indent=2) + '\n')
p = json.loads(PFILE.read_text())
for key in DEFAULTS:
    if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]) or p[key] <= 0:
        raise ValueError(f'Invalid positive numeric parameter: {key}')
W,D,H,t = (p[k] for k in ('width','depth','height','plywood'))
assert W <= 30.125, 'Width exceeds side step limit'
assert H >= 30 and D >= 17.75, 'Rework vertical/operating clearances before shrinking further'
assert p['rear_gap'] >= .75, 'Insufficient C-pillar depth allowance'
xdiv=t+p['left_clear']; xr=xdiv+t; right=W-t-xr
assert p['left_clear'] >= 12.5 and right >= 15.5
front=D-t; rear=p['rear_gap']; topz=H-p['top_thickness']; reveal=.0625
toe_h=p['toe_kick_height']; kick_front=D-p['toe_kick_recess']
assert 0 < kick_front < front and toe_h >= 3
assert toe_h+.75+13.5 < p['dog_deck_z'], 'Toilet must clear dog platform'
OUT.mkdir(exist_ok=True)
parts=[]; env=[]
COLORS={'wood':(.77,.60,.38,1),'top':(.14,.18,.18,1),'hardware':(.35,.39,.42,1),
        'toilet':(.76,.83,.87,.60),'tank':(.30,.61,.68,.40),'sink':(.56,.66,.72,.5)}

def box(x,y,z,a,b,c):
    return cq.Workplane('XY').box(a*25.4,b*25.4,c*25.4,centered=False).translate((x*25.4,y*25.4,z*25.4)).val()

def add(name,x,y,z,a,b,c,kind='wood',moving='',panel=True):
    q=dict(name=name,shape=box(x,y,z,a,b,c),kind=kind,moving=moving,
           origin=(x,y,z),dims=(a,b,c),panel=panel)
    parts.append(q); return q

def envelope(name,x,y,z,a,b,c,kind,moving=''):
    q=dict(name=name,shape=box(x,y,z,a,b,c),kind=kind,moving=moving,
           origin=(x,y,z),dims=(a,b,c),panel=False)
    env.append(q); return q

def vent(part,xc,zc):
    # Round-ended diagonal slots based on the bed's photographed motif.
    cutter=None
    for j in range(9):
        length=.85 if j in (0,8) else 1.25
        q=(cq.Workplane('XZ').center((xc+(j-4)*.42)*25.4, zc*25.4)
            .slot2D(length*25.4,.125*25.4,45).extrude((t+.2)*25.4,both=True)
            .translate((0,(front+t/2)*25.4,0)).val())
        cutter=q if cutter is None else cutter.fuse(q)
    part['shape']=part['shape'].cut(cutter)

add('left_side',0,rear,0,t,front-rear,topz)
add('right_side',W-t,rear,0,t,front-rear,topz)
add('back',t,rear,0,W-2*t,t,topz)
add('divider',xdiv,rear+t,0,t,front-rear-t,topz)
# Continuous floor-supported sides and divider have matching front recesses.
for q in parts:
    if q['name'] in ('left_side','right_side','divider'):
        x=q['origin'][0]
        q['shape']=q['shape'].cut(box(x-.01,kick_front,-.01,t+.02,D-kick_front+.1,toe_h+.01))
add('tank_base',t,rear+t,toe_h,p['left_clear'],front-rear-t,t)
add('toe_kick_left_panel',t,kick_front-t,0,p['left_clear'],t,toe_h)
# This recessed, lift-off panel travels with the toilet sled and conceals its rollers.
add('toilet_kick_panel',xr,kick_front-t,reveal,right,t,toe_h-reveal,moving='toilet')
add('countertop',0,0,topz,W,D,p['top_thickness'],'top')
for side,x,a in [('left',t,p['left_clear']),('right',xr,right)]:
    for label,z in [('low',toe_h-2.5),('high',topz-3)]:
        add(f'mount_rail_{side}_{label}',x,rear+t,z,a,.5,2.5)
leftface=xdiv+t/2-reveal
q=add('tank_access_door',reveal,front,toe_h+reveal,leftface-reveal,t,25.875-toe_h-reveal)
vent(q,6.5,22.8); vent(q,6.5,4)
add('sink_service_front',reveal,front,26,leftface-reveal,t,topz-reveal-26)
rfx=xdiv+t/2+reveal; rfw=W-reveal-rfx
q=add('toilet_hinged_door',rfx,front,toe_h+reveal,rfw,t,17.875-toe_h-reveal,moving='door')
vent(q,xr+right/2,13.5)
slide=p['dog_slide_space']; deckw=right-2*slide; dogz=p['dog_deck_z']; dy=front-p['dog_depth']
add('dog_deck',xr+slide,dy,dogz,deckw,p['dog_depth'],.75,moving='dog')
add('dog_front',rfx,front,dogz,rfw,t,2,moving='dog')
for name,x in [('left',xr),('right',W-t-slide)]:
    add(f'dog_slide_{name}_clearance',x,dy,dogz-2.5,slide,p['dog_depth'],3,'hardware',panel=False)
for index,z in enumerate((20.125,24.125)):
    add(f'drawer_{index+1}_front',rfx,front,z,rfw,t,3.875)
    bx=xr+.625; bw=right-1.25; by=4.5; bz=z+.5
    add(f'drawer_{index+1}_bottom',bx,by,bz,bw,12,.5)
    for lab,xx in [('left',bx),('right',bx+bw-.5)]:
        add(f'drawer_{index+1}_{lab}',xx,by,bz+.5,.5,12,2)
    add(f'drawer_{index+1}_back',bx+.5,by,bz+.5,bw-1,.5,2)
add('upper_fixed_front',rfx,front,28.125,rfw,t,topz-reveal-28.125)
# Independent flat sled. No cabinet floor under the toilet bay.
sledx=xr+.5; sledw=right-1
add('toilet_sled',sledx,2,toe_h,sledw,15.5,.75,moving='toilet')
for xx in (sledx+1,sledx+sledw-1):
    for yy in (3.5,13.5):
        wheel=(cq.Workplane('YZ').circle(toe_h/2*25.4).extrude(.6*25.4)
            .translate(((xx-.3)*25.4,yy*25.4,toe_h/2*25.4)).val())
        parts.append(dict(name=f'floor_roller_{xx}_{yy}',shape=wheel,kind='hardware',moving='toilet',panel=False,origin=(xx-.3,yy-toe_h/2,0),dims=(.6,toe_h,toe_h)))
add('tank_carrier',t+.25,2.75,toe_h+t,p['left_clear']-.5,7.25,.1,'hardware',panel=False)
envelope('toilet_335_reserved_envelope',xr+(right-13.46)/2,2,toe_h+.75,13.46,15.03,13.5,'toilet','toilet')
envelope('COMET_19L_reserved_envelope',t+(p['left_clear']-280/25.4)/2,3,toe_h+t+.1,280/25.4,170/25.4,475/25.4,'tank')
envelope('VA930_sink_reserved_envelope',t+(p['left_clear']-280/25.4)/2,2.125,H-145/25.4,280/25.4,380/25.4,145/25.4,'sink')
# Bed is RIGHT when viewed from the front. Route above the tank and behind drawers.
service_cuts=[]
for name,x in [('right_side',W-t),('divider',xdiv)]:
    q=next(q for q in parts if q['name']==name)
    hole=(cq.Workplane('YZ').center(p['water_entry_from_wall']*25.4,p['water_entry_height']*25.4)
        .circle(p['water_entry_diameter']/2*25.4).extrude((t+.2)*25.4,both=True)
        .translate(((x+t/2)*25.4,0,0)).val())
    before=q['shape'].Volume()
    q['shape']=q['shape'].cut(hole)
    removed=(before-q['shape'].Volume())/25.4**3
    assert removed > .1, f'Water passage did not cut {name}'
    service_cuts.append(dict(part=name,removed_volume_in3=round(removed,6)))

def positioned(q,deployed):
    shape=q['shape']
    if deployed and q['moving']=='door':
        shape=shape.rotate(((W-reveal)*25.4,D*25.4,0),((W-reveal)*25.4,D*25.4,25.4),-90)
    elif deployed and q['moving'] in ('toilet','dog'):
        shape=shape.translate((0,p[q['moving']+'_travel']*25.4,0))
    # Fusion coordinates: x increases right, y increases toward the wall.
    return shape.mirror('XZ').translate((0,D*25.4,0))

for deployed,label in [(False,'stowed'),(True,'deployed')]:
    for include_env,suffix in [(False,''),(True,'_clearance')]:
        asm=cq.Assembly(name='van_cabinet_'+label+suffix)
        for q in parts+(env if include_env else []):
            asm.add(positioned(q,deployed),name=q['name'],color=cq.Color(*COLORS[q['kind']]))
        asm.export(str(OUT/f'cabinet_{label}{suffix}.step'))
# Clearance export includes deliberate sink/countertop overlap: no cutout approved yet.
checks=[]
for q in parts+env:
    checks.append(dict(name=q['name'],valid=q['shape'].isValid(),solids=len(q['shape'].Solids())))
assert all(q['valid'] and q['solids']==1 for q in checks)
wood=[q for q in parts if q['panel']]
clashes=[]
for a,b in itertools.combinations(parts,2):
    vol=a['shape'].intersect(b['shape']).Volume()/25.4**3
    if vol > .00001:
        clashes.append(dict(a=a['name'],b=b['name'],volume_in3=round(vol,6)))
component_clashes=[]
for a in env:
    for b in parts:
        vol=a['shape'].intersect(b['shape']).Volume()/25.4**3
        if vol > .00001:
            component_clashes.append(dict(a=a['name'],b=b['name'],volume_in3=round(vol,6),intentional=b['name']=='countertop' and a['kind']=='sink'))
deployed_clashes=[]
for a,b in itertools.combinations(parts,2):
    vol=positioned(a,True).intersect(positioned(b,True)).Volume()/25.4**3
    if vol > .00001:
        deployed_clashes.append(dict(a=a['name'],b=b['name'],volume_in3=round(vol,6)))
assert not clashes, f'Stowed part clashes: {clashes}'
assert not deployed_clashes, f'Deployed part clashes: {deployed_clashes}'
assert all(q['intentional'] for q in component_clashes), 'Unexpected component clash'
report=dict(status='preliminary_geometry_only',outer_inches=[W,D,H],max_width_inches=30.125,
    width_margin_inches=30.125-W,dog_deck_inches=[deckw,p['dog_depth'],.75],right_clear_inches=right,
    rear_gap_inches=rear,c_pillar_depth_inches=.625,solid_checks=checks,
    toe_kick_inches=dict(height=toe_h,recess=p['toe_kick_recess']),
    cabinet_has_feet=False,carcass_floor_z_inches=0,
    water_entry=dict(side='right',height=p['water_entry_height'],from_wall=p['water_entry_from_wall'],diameter=p['water_entry_diameter'],cuts=service_cuts),
    parts_fit_48_in_stock=all(sorted(q['dims'])[-2]<=48 for q in wood),
    parts_fit_48_by_48_in_stock=all(max(q['dims'])<=48 for q in wood),
    stowed_part_intersections=clashes,deployed_part_intersections=deployed_clashes,component_intersections=component_clashes,
    caveats=['No structural rating or full motion/hinge/plumbing verification',
    'Sink overlaps uncut countertop intentionally; final template required',
    'Floor rollers, slide envelopes and mounting rails are provisional',
    'Clearance envelopes omit fittings and moving lids',
    'Depth 18 inches is provisional; confirm against actual finished van'])
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
with (OUT/'panel_list.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['part','length_in','width_in','thickness_in','status'])
    for q in wood:
        dims=sorted(q['dims'],reverse=True); w.writerow([q['name'],*dims,'concept_only_no_joinery'])
# Review render: hide service fronts for an internal view. Sink shown as a reserved envelope.
fig=plt.figure(figsize=(16,8),facecolor='#f5f3ec')
for index,deployed in enumerate((False,True)):
    ax=fig.add_subplot(1,2,index+1,projection='3d',facecolor='#f5f3ec')
    hidden={'back','left_side','tank_access_door','sink_service_front'} if deployed else set()
    for q in parts+env:
        if q['name'] in hidden: continue
        shape=positioned(q,deployed)
        if q['name']=='countertop':
            shape=shape.cut(positioned(env[-1],deployed))
        if q['kind']=='sink':
            x,y,z=q['origin']; a,b,c=q['dims']
            shape=box(x,y,z,a,b,c).cut(box(x+.06,y+.06,z+.06,a-.12,b-.12,c+.1)).mirror('XZ').translate((0,D*25.4,0))
        if not deployed and q in env and q['kind']!='sink': continue
        vs,ts=shape.tessellate(.7, .2)
        coords=[(v.x/25.4,v.y/25.4,v.z/25.4) for v in vs]
        faces=[[coords[k] for k in tri] for tri in ts]
        rgba=COLORS[q['kind']]
        import numpy as np
        triangles=np.asarray(faces)
        norms=np.cross(triangles[:,1]-triangles[:,0], triangles[:,2]-triangles[:,0])
        lengths=np.linalg.norm(norms,axis=1)
        norms=norms/np.maximum(lengths[:,None],1e-12)
        light=np.array([-.35,.5,.85]); light=light/np.linalg.norm(light)
        brightness=.58+.42*np.maximum(0,norms@light)
        facecolors=brightness[:,None]*np.asarray(rgba[:3])[None,:]
        poly=Poly3DCollection(faces,facecolor=facecolors,alpha=rgba[3],edgecolor='none',linewidth=0,antialiased=False)
        ax.add_collection3d(poly)
    ax.set(xlim=(0,W+1),ylim=(-p['toilet_travel']-1,D),zlim=(0,H+1),xlabel='Width (in)',ylabel='Depth / extension (in)',zlabel='Height (in)')
    ax.set_box_aspect((W,D+p['toilet_travel'],H)); ax.view_init(elev=24,azim=-65)
    ax.set_title('STOWED | sink left, toilet right' if not deployed else 'EXTENDED | service panels hidden',fontsize=13,pad=15)
fig.suptitle(f'VAN CABINET CONCEPT 01 | {W:g} W x {D:g} D x {H:g} H inches',fontsize=17)
fig.text(.5,.025,'Provisional components and hardware. Sink illustrated for review; STEP countertop remains uncut. No validated load rating.',ha='center',fontsize=10)
fig.savefig(OUT/'review.png',dpi=160,bbox_inches='tight'); plt.close(fig)
# Vector front review, with component outlines visible through doors.
S=14; ox=70; oy=540
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="660" viewBox="0 0 1000 660">','<rect width="1000" height="660" fill="#f5f3ec"/>','<g font-family="sans-serif" fill="#243337">',f'<text x="50" y="38" font-size="22">Cabinet concept | {W:g} W x {D:g} D x {H:g} H inches</text>']
for q in parts:
    if q['name'] in ('countertop','tank_access_door','sink_service_front','toilet_hinged_door','dog_front','drawer_1_front','drawer_2_front','upper_fixed_front','toe_kick_left_panel','toilet_kick_panel'):
        x,y,z=q['origin']; a,b,c=q['dims']
        svg.append(f'<rect x="{ox+x*S}" y="{oy-(z+c)*S}" width="{a*S}" height="{c*S}" fill="{("#334446" if q["kind"]=="top" else "#d8bc91")}" stroke="#6c604f"/>')
for q in env:
    x,y,z=q['origin']; a,b,c=q['dims']
    svg.append(f'<rect x="{ox+x*S}" y="{oy-(z+c)*S}" width="{a*S}" height="{c*S}" fill="none" stroke="#26758a" stroke-dasharray="5 4"/>')
for i,line in enumerate(['FRONT VIEW: sink LEFT','Left clear bay: 12.5 in',f'Right clear bay: {right:g} in',f'Dog platform: {deckw:g} W x {p["dog_depth"]:g} D in','Toilet door opens separately','Toilet tray rolls on van floor',f'Toe kick: {toe_h:g} H x {p["toe_kick_recess"]:g} recess', 'Water entry: RIGHT, beside bed', 'Rear gap: 0.875 in for C-pillar','18 in depth remains provisional','Plywood: 0.5 in; top: 0.75 in','Review PNG for vent-slot detail','No production cutouts / joinery yet']):
    svg.append(f'<text x="555" y="{100+i*28}" font-size="17">{line}</text>')
svg.extend(['<text x="65" y="602" font-size="16">Dashed outlines reserve component space. Load targets: dog 45 lb; seated person 200 lb.</text>','<text x="65" y="630" font-size="16">Geometry checks do not establish physical fit, safe load capacity or mounting strength.</text>','</g></svg>'])
(OUT/'review.svg').write_text('\n'.join(svg))
print(json.dumps({k:report[k] for k in ('outer_inches','dog_deck_inches','parts_fit_48_in_stock','stowed_part_intersections','component_intersections')},indent=2))
print('Saved STEP assemblies, review.png, review.svg, panel_list.csv and validation.json to concept/.')

# Flat layout sheet avoids tessellation seams in the perspective mesh preview.
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.transforms import Affine2D
fig, axes=plt.subplots(1,2,figsize=(13,8),facecolor='#f5f3ec')
for ax,inside in zip(axes,(False,True)):
    ax.set_facecolor('#f5f3ec'); ax.set_aspect('equal')
    ax.set_xlim(-1,W+1); ax.set_ylim(-1,H+2)
    ax.set_xlabel('Width (inches)'); ax.set_ylabel('Height (inches)')
    ax.set_title('INTERIOR | front panels removed' if inside else 'FRONT | sink left, toilet right',fontsize=14)
    ax.add_patch(Rectangle((0,toe_h),W,topz-toe_h,facecolor='#e4d1ae',edgecolor='#786b55'))
    for q in parts:
        x,y,z=q['origin']; a,b,c=q['dims']
        is_front=q['name'] in ('countertop','tank_access_door','sink_service_front','toilet_hinged_door','dog_front','drawer_1_front','drawer_2_front','upper_fixed_front','toe_kick_left_panel','toilet_kick_panel')
        if not inside and is_front:
            ax.add_patch(Rectangle((x,z),a,c,facecolor=('#263638' if q['kind']=='top' else '#cfb080'),edgecolor='#69583e',linewidth=.7))
        if inside and q['name'] in ('divider','left_side','right_side','tank_base','toilet_sled','dog_deck','countertop'):
            ax.add_patch(Rectangle((x,z),a,c,facecolor=('#263638' if q['kind']=='top' else '#b79561'),edgecolor='#69583e',linewidth=.7))
    if inside:
        for q in env:
            x,y,z=q['origin']; a,b,c=q['dims']
            ax.add_patch(Rectangle((x,z),a,c,facecolor='#6aa8b2',edgecolor='#2d6773',alpha=.5))
            label={'tank':'19 L greywater\ncandidate','toilet':'Toilet envelope\non floor sled','sink':'Sink envelope'}[q['kind']]
            ax.text(x+a/2,z+c/2,label,ha='center',va='center',fontsize=10)
        ax.text(xr+right/2,dogz+1.5,f'{deckw:g} x {p["dog_depth"]:g} in dog deck',ha='center',fontsize=10)
        ax.text(xr+right/2,25,'Storage drawers',ha='center',fontsize=11)
    else:
        for xc,zc in ((6.5,22.8),(6.5,4),(xr+right/2,13.5)):
            for j in range(9):
                length=.85 if j in (0,8) else 1.25
                cx=xc+(j-4)*.42; width=.125
                slot=FancyBboxPatch((cx-length/2,zc-width/2),length,width,
                    boxstyle=f'round,pad=0,rounding_size={width/2}',facecolor='#293537',edgecolor='none')
                slot.set_transform(Affine2D().rotate_deg_around(cx,zc,45)+ax.transData)
                ax.add_patch(slot)
        for x,z,label in ((6.5,28.5,'Sink on left'),(6.5,15,'Greywater access'),(xr+right/2,7.5,'Toilet access'),(xr+right/2,19,'Dog platform'),(xr+right/2,22,'Drawer'),(xr+right/2,26,'Drawer')):
            ax.text(x,z,label,ha='center',va='center',fontsize=10)
    ax.grid(False)
fig.suptitle(f'VAN CABINET | {W:g} W x {D:g} D x {H:g} H inches',fontsize=19)
fig.text(.5,.035,'Concept 01: 18 inch depth and components provisional. Load targets: 45 lb dog, 200 lb seated person. Structure unvalidated.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.13,1,.94))
fig.savefig(OUT/'layout.png',dpi=180,bbox_inches='tight'); plt.close(fig)
# CAD-generated vector perspective uses exact geometry and rounded vent edges.
compound=cq.Compound.makeCompound([positioned(q,False) for q in parts])
cq.exporters.export(compound,str(OUT/'isometric.svg'),opt={'projectionDir':(1,-2,1.3),'showHidden':False,'width':1000,'height':1000})
