"""Render the computed route as a standalone SVG data diagram and CSV."""
from pathlib import Path
import json,base64,html,csv,math
OUT=Path('/workspace/route-preview')
r=json.loads((OUT/'route.json').read_text())
S=12.45;OX=70;OY=350;W=3626;H=4030

def xy(p):return OX+p['x']*S,OY+(279-p['y'])*S

def esc(s):return html.escape(str(s))
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
'<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#88ecdf"/></marker></defs>',
'<rect width="100%" height="100%" fill="#0e1622"/>',
'<g font-family="DejaVu Sans, sans-serif" fill="#eef6ff">',
'<text x="70" y="85" font-size="46" font-weight="bold">LOONG HAVEN · FIXED CAMERA PATH</text>',
'<text x="70" y="142" font-size="29" fill="#aec5d9">Start at Emerald Corner · follow the same 1 → 77 order every pass</text>',
f'<text x="70" y="193" font-size="27">77 camera checks cover all 86 known spawn spots · {r["bridge_click_count"]} extra camera selections between checks</text>',
'<text x="70" y="242" font-size="25" fill="#ffd792">DRAFT: no dragging in the screenshot model; automatic recentering and unlocked access need live verification.</text>',
'<circle cx="90" cy="298" r="18" fill="#162a3d" stroke="#c2fff6" stroke-width="3"/><text x="90" y="305" text-anchor="middle" font-size="20" font-weight="bold">8</text>',
'<text x="125" y="307" font-size="24">Numbered gem check</text>',
'<circle cx="560" cy="298" r="7" fill="#ff79dc"/><text x="585" y="307" font-size="24">Original spawn</text>',
'<circle cx="980" cy="298" r="13" fill="#0e1622" stroke="#ffbf65" stroke-width="4"/><text x="1005" y="307" font-size="24">B = extra camera click, not a gem</text>',
'<path d="M 1630 298 h 100" fill="none" stroke="#b8a5ff" stroke-width="5" stroke-dasharray="12 9"/><text x="1750" y="307" font-size="24">R = return to start for another pass</text>',
'</g>']
blob=base64.b64encode(Path('/workspace/test/loong_haven_default_atlas.png').read_bytes()).decode()
svg.append(f'<image x="{OX}" y="{OY}" width="3486" height="3486" xlink:href="data:image/png;base64,{blob}"/>')
svg.append(f'<rect x="{OX}" y="{OY}" width="3486" height="3486" fill="#07101a" opacity=".12"/>')
# All consecutive clicks are shown, including bridges that replace a drag.
for t in r['transitions']:
 a=r['stops'][t['from_number']-1];b=r['stops'][t['to_number']-1]
 chain=[a]+t['bridge']+[b]
 for p,q in zip(chain,chain[1:]):
  x,y=xy(p);u,v=xy(q);color='#ffc477' if t['bridge'] else '#72dfd1';dash=' stroke-dasharray="13 9"' if t['bridge'] else ''
  svg.append(f'<path d="M {x:.2f} {y:.2f} L {u:.2f} {v:.2f}" fill="none" stroke="#081522" stroke-width="12" opacity=".75"/>')
  svg.append(f'<path d="M {x:.2f} {y:.2f} L {u:.2f} {v:.2f}" fill="none" stroke="{color}" stroke-width="6" opacity=".9"{dash}/>')
  mx,my=(x+u)/2,(y+v)/2;angle=math.degrees(math.atan2(v-y,u-x))
  svg.append(f'<path d="M -9 -7 L 9 0 L -9 7 Z" transform="translate({mx:.2f},{my:.2f}) rotate({angle:.2f})" fill="{color}" stroke="#0e1622" stroke-width="2"/>')
# Loop return is explicitly separate from the first pass.
chain=[r['stops'][-1]]+r['loop_return_bridge']+[r['stops'][0]]
for p,q in zip(chain,chain[1:]):
 x,y=xy(p);u,v=xy(q)
 svg.append(f'<path d="M{x} {y} L{u} {v}" fill="none" stroke="#baa6ff" stroke-width="5" stroke-dasharray="12 10" opacity=".85"/>')
# Underlying original spawn dots, including all members of grouped checks.
for s in r['stops']:
 for a,b in s['spawn_spots']:
  x=OX+(a+.5)*S;y=OY+(279-b-.5)*S
  svg.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#ff79dc" stroke="#201323" stroke-width="2"/>')
# B / R markers: visibly distinct from numbered gem checks.
for p in [p for t in r['transitions'] for p in t['bridge']]+r['loop_return_bridge']:
 x,y=xy(p);is_return=p['label'].startswith('R');color='#baa6ff' if is_return else '#ffc477'
 lx,ly=x+20,y-15
 if min(math.dist((x,y),xy(s)) for s in r['stops'])<55:
  lx,ly=x+85,y+45
  svg.append(f'<path d="M{x+12} {y+10} L{lx-8} {ly-8}" stroke="{color}" stroke-width="3"/>')
 svg.append(f'<g><title>{p["label"]}: camera selection only ({p["x"]:.2f},{p["y"]:.2f})</title><circle cx="{x}" cy="{y}" r="13" fill="#0e1622" stroke="{color}" stroke-width="4"/><text x="{lx}" y="{ly}" font-family="DejaVu Sans" font-size="22" font-weight="bold" fill="{color}" stroke="#07111c" stroke-width="5" paint-order="stroke">{p["label"]}</text></g>')
labels=[list(xy(s)) for s in r['stops']]
for _ in range(40):
 for i in range(len(labels)):
  for j in range(i):
   dx=labels[i][0]-labels[j][0];dy=labels[i][1]-labels[j][1];d=math.hypot(dx,dy)
   if d<60:
    ux,uy=(dx/d,dy/d) if d else (1.,0.)
    shift=(60-d)/2
    labels[i][0]+=ux*shift;labels[i][1]+=uy*shift;labels[j][0]-=ux*shift;labels[j][1]-=uy*shift
for s,(x,y) in zip(r['stops'],labels):
 px,py=xy(s)
 if math.hypot(x-px,y-py)>5:
  svg.append(f'<path d="M{px} {py} L{x} {y}" stroke="#ffffff" stroke-width="3"/><circle cx="{px}" cy="{py}" r="4" fill="#ffffff"/>')
 fill='#174b3c' if s['number']==1 else '#162a3d';stroke='#8dffc6' if s['number']==1 else '#dcfff9'
 title=f'{s["number"]}. {s["zone"]} — camera ({s["x"]:.2f},{s["y"]:.2f}); spawn spots '+str(s['spawn_spots'])
 svg.append(f'<g><title>{esc(title)}</title><circle cx="{x}" cy="{y}" r="23" fill="{fill}" stroke="#07111c" stroke-width="8"/><circle cx="{x}" cy="{y}" r="23" fill="{fill}" stroke="{stroke}" stroke-width="3"/><text x="{x}" y="{y+9}" text-anchor="middle" font-family="DejaVu Sans" font-size="26" font-weight="bold" fill="#ffffff">{s["number"]}</text></g>')
x,y=xy(r['stops'][0]);svg.append(f'<text x="{x-170}" y="{y+77}" font-family="DejaVu Sans" font-size="30" font-weight="bold" fill="#8dffc6" stroke="#07111c" stroke-width="7" paint-order="stroke">START · EMERALD CORNER</text>')
svg.extend(['<g font-family="DejaVu Sans" fill="#c2d0df" font-size="24">',
f'<text x="70" y="3895">At a number: select camera → close map → inspect → reopen. At B/R: select camera → close/reopen to recenter.</text>',
f'<text x="70" y="3940">After 77: {r["loop_return_extra_clicks"]} return camera selection(s), then back to 1. The same order can be saved for every pass.</text>',
'<text x="70" y="3985">Full-map draft includes locations that may be locked on your account. Skipping them may require a different connecting click.</text>',
'</g></svg>'])
(OUT/'LoongLens-Numbered-Camera-Path.svg').write_text(''.join(svg))
with (OUT/'LoongLens-Camera-Order.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['Order','Zone','Camera X','Camera Y','Original gem coordinates','Extra camera clicks before this check'])
 for s in r['stops']:
  t=next((t for t in r['transitions'] if t['to_number']==s['number']),None)
  writer.writerow([s['number'],s['zone'],f'{s["x"]:.2f}',f'{s["y"]:.2f}','; '.join(f'{x},{y}' for x,y in s['spawn_spots']),'; '.join(f'{p["label"]} ({p["x"]},{p["y"]})' for p in t['bridge']) if t else 'Start'])
print(OUT/'LoongLens-Numbered-Camera-Path.svg')
