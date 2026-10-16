"""Offline camera-route diagram. Does not modify Loong Lens or send input."""
import sys,json,math,random,heapq,time
from pathlib import Path
sys.path.insert(0,'/workspace/test')
import numpy as np
from camera_patrol import build_plan,load_spawns,playable_ground,camera_click_clear
ROOT=Path('/workspace/test');OUT=Path('/workspace/route-preview')
plan=build_plan(load_spawns(json.loads((ROOT/'loong_haven_map_data.json').read_text())))
views=plan.views
points=np.array([(v.x,v.y) for v in views])
start=next(i for i,v in enumerate(views) if v.near_zone=='Emerald Corner')
# Nominal camera recenter inferred from the supplied screenshot. A live
# implementation must re-recognise the actual map; this is a drawing model.
SCALE=12.45

def fits(a,b):
 sx=285+(b[0]-a[0])*SCALE;sy=530-(b[1]-a[1])*SCALE
 return 32<=sx<=510 and 150<=sy<=800 and not(sx>=420 and sy<=250)

length=np.linalg.norm(points[:,None,:]-points[None,:,:],axis=2)
hops=np.zeros((len(views),len(views)),int)
for i,a in enumerate(points):
 for j,b in enumerate(points):
  if i==j:continue
  for k in range(1,40):
   if fits(a,a+(b-a)/k):hops[i,j]=k;break
  assert hops[i,j]
cost=hops*10000+length
n=len(views)

def score(route):return sum(cost[a,b] for a,b in zip(route,route[1:]+route[:1]))

def improve(route):
 current=score(route)
 for iteration in range(80):
  best=current;change=None
  prefix=[0.]
  for k in range(n-1):prefix.append(prefix[-1]+cost[route[k+1],route[k]]-cost[route[k],route[k+1]])
  for i in range(2,n-1):
   a,b=route[i-1],route[i]
   for j in range(i+1,n):
    c=route[j]
    delta=cost[a,c]-cost[a,b]+prefix[j]-prefix[i]
    d=route[(j+1)%n];delta+=cost[b,d]-cost[c,d]
    if current+delta<best-1e-8:best=current+delta;change=(i,j)
  if change is None:break
  i,j=change;route[i:j+1]=route[i:j+1][::-1];current=best
 return route,current

rng=random.Random(17);candidates=[]
# Start from several reproducible greedy and perturbed orders. All start at
# the same Emerald Corner camera target; this is not an optimality proof.
second=next(i for i,v in enumerate(views) if v.near_zone=='Loong Haven I')
for attempt in range(20):
 route=[start,second];left=set(range(n))-{start,second}
 while left:
  ranked=sorted(left,key=lambda j:(cost[route[-1],j],j))
  k=0 if attempt==0 or len(ranked)<2 or rng.random()<.88 else rng.randrange(min(3,len(ranked)))
  j=ranked[k];route.append(j);left.remove(j)
 route,value=improve(route)
 candidates.append((value,route))
value,order=min(candidates,key=lambda item:item[0])
ground=playable_ground()
# Bridge cameras are allowed only on the bundled playable terrain and outside
# the known portal's hit box. A local lattice is enough for these short gaps.

def walkable(p):
 x,y=p
 return 0<=x<280 and 0<=y<280 and ground[int(y),int(x)] and camera_click_clear(x,y)

def bridge(a,b):
 a=tuple(a);b=tuple(b)
 if fits(a,b):return []
 x0=max(0,int(min(a[0],b[0])-22));x1=min(279,int(max(a[0],b[0])+23))
 y0=max(0,int(min(a[1],b[1])-25));y1=min(279,int(max(a[1],b[1])+26))
 # 2-tile lattice plus exact endpoints. A* uses one cost unit per camera
 # recenter; a small distance term chooses the shortest among equal-hop paths.
 nodes=[a,b]+[(x+.5,y+.5) for x in range(x0,x1+1,2) for y in range(y0,y1+1,2)
                if walkable((x+.5,y+.5))]
 middle=((a[0]+b[0])/2,(a[1]+b[1])/2)
 options=[p for p in nodes[2:] if fits(a,p) and fits(p,b)]
 if options:return [min(options,key=lambda p:math.dist(p,middle))]
 arr=np.array(nodes);best={0:0.};prev={};queue=[(0.,0)]
 while queue:
  val,i=heapq.heappop(queue)
  if val>best[i]+1e-8:continue
  if i==1:
   ids=[1]
   while ids[-1]!=0:ids.append(prev[ids[-1]])
   return [nodes[k] for k in ids[::-1][1:-1]]
  sx=285+(arr[:,0]-arr[i,0])*SCALE;sy=530-(arr[:,1]-arr[i,1])*SCALE
  neighbors=np.flatnonzero((sx>=32)&(sx<=510)&(sy>=150)&(sy<=800)&~((sx>=420)&(sy<=250)))
  for j in neighbors:
   j=int(j)
   if j==i:continue
   nv=val+10000+float(np.linalg.norm(arr[j]-arr[i]))
   if nv<best.get(j,float('inf'))-1e-8:
    best[j]=nv;prev[j]=i;heapq.heappush(queue,(nv,j))
 raise RuntimeError(('No playable bridge',a,b))

stops=[];transitions=[];bridge_number=0
for number,idx in enumerate(order,1):
 v=views[idx]
 stops.append(dict(number=number,original_index=idx,zone=v.near_zone,x=v.x,y=v.y,
                   spawn_spots=[list(c) for c in sorted(v.cells)]))
 if number>1:
  prior=views[order[number-2]]
  extra=bridge((prior.x,prior.y),(v.x,v.y))
  extra_stops=[]
  for x,y in extra:
   bridge_number+=1;extra_stops.append(dict(label=f'B{bridge_number}',x=x,y=y))
  transitions.append(dict(from_number=number-1,to_number=number,bridge=extra_stops))
# Loop wrap is a separate, potentially long transition; never hide it behind
# a false direct connection from the last marker to Emerald Corner.
a=views[order[-1]];b=views[start]
loop=bridge((a.x,a.y),(b.x,b.y))
for i,(x,y) in enumerate(loop,1):
 pass
result=dict(title='Loong Haven fixed camera path — draft',start_zone='Emerald Corner',
       default_zoom_scale=12.45,camera_recenter_model=[285,530],
       clickable_reference_bounds=[32,510,150,800],assumed_recenter_uncertainty_px=[0,0],
       known_spawn_count=len(plan.cells),check_count=len(stops),bridge_click_count=bridge_number,
       loop_return_extra_clicks=len(loop),
       notes=['A camera diagram, not an updated EXE or a live-tested route.',
              'Numbers are grouped camera checks; pink dots are the original 86 spawn locations.',
              'B markers are extra camera selections, followed by close/reopen, without a gem inspection.',
              'Account-specific locked areas are unknown and may break a bridge.',
              'Recentring must be re-recognised after each close/reopen; nominal geometry is not a substitute for screenshot verification.'],
       stops=stops,transitions=transitions,
       loop_return_bridge=[dict(label=f'R{i}',x=x,y=y) for i,(x,y) in enumerate(loop,1)])
# Verify all 86 originals exactly once, and every consecutive planned click
# against the nominal screenshot model and existing HUD exclusion.
assert len({s['original_index'] for s in stops})==77
assert len({tuple(c) for s in stops for c in s['spawn_spots']})==86
for t in transitions:
 a=stops[t['from_number']-1];b=stops[t['to_number']-1]
 chain=[(a['x'],a['y'])]+[(p['x'],p['y']) for p in t['bridge']]+[(b['x'],b['y'])]
 for p,q in zip(chain,chain[1:]):
  assert fits(p,q)
 for p in t['bridge']:assert walkable((p['x'],p['y']))
for a,b in zip([points[order[-1]]]+loop,loop+[points[start]]):assert fits(a,b)
(OUT/'route.json').write_text(json.dumps(result,indent=2))
print('Fixed route:',len(stops),'checks;',bridge_number,'extra camera clicks; loop return:',len(loop),'extra cameras',flush=True)
print('First five:',[(s['number'],s['zone'],round(s['x'],1),round(s['y'],1)) for s in stops[:5]])
print('Gaps:',[(t['from_number'],t['to_number'],len(t['bridge'])) for t in transitions if t['bridge']])
