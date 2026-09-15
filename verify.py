# -*- coding: utf-8 -*-
"""Runtime-verify a school page: syntax, orphan element refs, render, interactions."""
import re, io, sys, subprocess, os

STUB = '''var _e={};
function el(i){if(!_e[i])_e[i]={innerHTML:'',textContent:'',value:'',style:{},
  classList:{add(){},remove(){},toggle(){}},querySelector(){return null}};return _e[i];}
global.document={getElementById:el,querySelectorAll(){return[]},
  querySelector(){return{style:{},classList:{add(){},remove(){},toggle(){}}}},
  addEventListener(){},documentElement:{style:{}}};
global.window={addEventListener(){}};
global.alert=function(m){console.log('ALERT:',m)};
global.gtag=undefined;
global.L={map(){return{setView(){return this},distance(){return 0},addLayer(){},removeLayer(){}}},
  tileLayer(){return{addTo(){}}},
  marker(){return{bindPopup(){return this},addTo(){return this},openPopup(){}}},
  divIcon(){},circleMarker(){return{addTo(){return this},bindPopup(){return this},openPopup(){}}}};
'''

def verify(path):
    name = os.path.basename(path)
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    h = io.open(path, encoding='utf-8').read()
    blocks = re.findall(r'<script>(.*?)</script>', h, re.S)
    js = next(b for b in blocks if 'const S = [' in b)          # app logic
    ana = next((b for b in blocks if '進階流量統計模組' in h and 'session_summary' in b), None)

    # 1. orphan getElementById refs
    ids = set(re.findall(r"getElementById\('([^']+)'\)", js))
    missing = sorted(i for i in ids if f'id="{i}"' not in h)
    print(f"getElementById refs : {len(ids)}")
    print(f"orphan elements     : {missing or 'none'}   {'✗ WILL CRASH' if missing else '✓'}")

    # 2. syntax
    io.open('_t.js','w',encoding='utf-8').write(js)
    r = subprocess.run(['node','--check','_t.js'],capture_output=True,text=True)
    print(f"app syntax          : {'✓ OK' if r.returncode==0 else '✗ '+r.stderr.strip()[:200]}")
    if r.returncode: return
    if ana:
        io.open('_a.js','w',encoding='utf-8').write(ana)
        ra = subprocess.run(['node','--check','_a.js'],capture_output=True,text=True)
        print(f"analytics syntax    : {'✓ OK' if ra.returncode==0 else '✗ '+ra.stderr.strip()[:200]}")
    else:
        print("analytics syntax    : (not present)")

    # 3. data integrity
    S = re.search(r'const S = \[.*?\n\];', h, re.S).group()
    P = re.search(r'const PROFILES = \{.*?\n\};', h, re.S).group()
    sids = re.findall(r"\{id:'([^']+)'", S)
    pids = set(re.findall(r'^  (\w+):\s*\{type:', P, re.M))
    nop  = [i for i in sids if i not in pids]
    coords = re.findall(r'lat:\s*([\d.]+)\s*,\s*lng:\s*([\d.]+)', S)
    oob = [c for c in coords if not (22.1<float(c[0])<22.6 and 113.8<float(c[1])<114.5)]
    dupe = [i for i in set(sids) if sids.count(i)>1]
    print(f"schools / profiles  : {len(sids)} / {len(pids)}   no-profile: {nop or 'none'}")
    print(f"duplicate ids       : {dupe or 'none'}")
    print(f"coords in HK bounds : {len(coords)-len(oob)}/{len(coords)}   {'✗ '+str(oob) if oob else '✓'}")
    tels = re.findall(r"tel:'([^']*)'", S)
    badtel = [t for t in tels if len(t.replace(' ',''))!=8]
    print(f"malformed tel       : {badtel or 'none'}")

    # 4. runtime render + interactions
    body = re.sub(r'\(function initProtection\(\).*?\}\)\(\);','',js,flags=re.S)
    tail = f'''
var g=_e['schoolGrid'].innerHTML;
var n=(g.match(/class="school-card/g)||[]).length;
console.log('cards rendered      : '+n+' / '+S.length+'   '+(n===S.length?'\\u2713':'\\u2717'));
console.log('resultCount         : '+_e['resultCount'].textContent);
var nets=[...new Set(S.map(s=>s.net))];
nets.forEach(function(nv){{ setFilter('net',String(nv),{{classList:{{add(){{}}}}}});
  console.log('  filter net='+nv+'        : '+_e['resultCount'].textContent); }});
setFilter('net','all',{{classList:{{add(){{}}}}}});
['happy','balanced','academic'].forEach(function(t){{ setFilter('type',t,{{classList:{{add(){{}}}}}});
  console.log('  filter '+t.padEnd(9)+'  : '+_e['resultCount'].textContent); }});
setFilter('type','all',{{classList:{{add(){{}}}}}});
toggleCompare(S[0].id); toggleCompare(S[1].id); openCompare();
console.log('compare modal       : '+_e['compareBody'].innerHTML.length+' chars '+(_e['compareBody'].innerHTML.length>200?'\\u2713':'\\u2717'));
var bad=0; S.forEach(function(s){{ try{{ openDetail(s.id); if(_e['detailBody'].innerHTML.length<300) bad++; }}catch(e){{ console.log('  detail FAIL '+s.id+': '+e.message); bad++; }} }});
console.log('detail modal (all)  : '+(S.length-bad)+'/'+S.length+' '+(bad?'\\u2717':'\\u2713'));
try{{ initMap(); console.log('initMap()           : \\u2713'); }}catch(e){{ console.log('initMap()           : \\u2717 '+e.message); }}
'''
    io.open('_r.js','w',encoding='utf-8').write(STUB+body+tail)
    r = subprocess.run(['node','_r.js'],capture_output=True,text=True)
    print(r.stdout.rstrip())
    if r.returncode:
        print("✗ RUNTIME ERROR:\n"+r.stderr.strip()[:600])

for f in sys.argv[1:]:
    verify(f)
