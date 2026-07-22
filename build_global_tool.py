#!/usr/bin/env python3
"""Generate the multi-country web tool (docs/index.html). Lazy-loads one country's
JSON at a time from docs/data/<iso>.json; index.json drives the country selector."""
import json
CH = json.dumps(json.load(open("chapter_names.json")), ensure_ascii=False, separators=(",",":"))
REPO = "https://github.com/ihelfrich/import-localization-atlas"

HTML = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Import Localization Atlas: any country vs China</title>
<meta name="description" content="Interactive classification of any country's imports from China by dependence, complexity, and localization priority. By Dr. Ian Helfrich.">
<style>
:root{--bg:#f5f7fa;--card:#fff;--ink:#16202e;--mut:#5a6472;--line:#e2e7ee;--navy:#1F3864;
 --A:#2E7D32;--B:#E8A200;--C:#2E6FB5;--D:#9AA3AD;--red:#C00000;--focus:#0b64d6}
@media(prefers-color-scheme:dark){:root{--bg:#0e1420;--card:#161e2b;--ink:#e9edf3;--mut:#9aa6b6;
 --line:#293345;--navy:#8fb4f0;--A:#5cba61;--B:#f0b93a;--C:#5b9be0;--D:#8b95a3;--focus:#5aa0ff}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--focus)}:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
.wrap{max-width:1200px;margin:0 auto;padding:26px 20px 70px}
header h1{font-size:25px;margin:0 0 6px;color:var(--navy);line-height:1.2}
.sub{color:var(--mut);margin:0 0 6px;font-size:14px}
.picker{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0 18px}
.picker select{padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font-size:15px;font-weight:600}
.links{font-size:13px;margin:2px 0 0}.links a{margin-right:14px;text-decoration:none;font-weight:600}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .k{font-size:24px;font-weight:700;color:var(--navy)}.card .l{font-size:12px;color:var(--mut);margin-top:2px}
.grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:18px}
@media(max-width:880px){.grid{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:18px}
.panel h2{font-size:16px;margin:0 0 3px}.panel .note{color:var(--mut);font-size:12.5px;margin:0 0 14px}
.controls{display:grid;grid-template-columns:1fr 1fr;gap:14px 24px}
@media(max-width:560px){.controls{grid-template-columns:1fr}}
.ctl label{display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:3px}
.ctl label .v{color:var(--navy);font-variant-numeric:tabular-nums}
input[type=range]{width:100%;accent-color:var(--navy)}
.btn{background:var(--navy);color:#fff;border:0;border-radius:8px;padding:8px 14px;font-weight:600;cursor:pointer;font-size:13px}
canvas{width:100%;height:auto;display:block;border-radius:8px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin-top:10px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px;vertical-align:middle}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.tools input,.tools select{padding:6px 9px;border:1px solid var(--line);border-radius:7px;background:var(--card);color:var(--ink);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
th{position:sticky;top:0;background:var(--card);color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.03em;cursor:pointer;user-select:none}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums}
.tblwrap{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:8px}
.mono{font-family:ui-monospace,Menlo,monospace}
.qA{color:var(--A);font-weight:700}.qB{color:var(--B);font-weight:700}.qC{color:var(--C);font-weight:700}.qD{color:var(--D)}
.bars .row{display:grid;grid-template-columns:210px 1fr 92px;gap:10px;align-items:center;margin:4px 0;font-size:12px}
.bars .lab{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track{background:var(--line);border-radius:5px;height:14px;overflow:hidden}.fill{height:100%;border-radius:5px}
.val{color:var(--mut);text-align:right;white-space:nowrap}
.scope{background:linear-gradient(0deg,rgba(192,0,0,.05),rgba(192,0,0,.05));border-left:3px solid var(--red)}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--bg);padding:6px 9px;border-radius:6px;font-size:12px;opacity:0;transition:opacity .1s;max-width:260px;z-index:9}
.foot{color:var(--mut);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:14px}
</style></head><body><div class="wrap">
<header>
<h1 id="title">Import Localization Atlas</h1>
<p class="sub">Classify any country's imports from China by dependence, economic complexity, and localization priority. Pick a country, then move the weight sliders to re-rank products live. Data: CEPII BACI (HS 2022, 2022-2023) and the OEC Product Complexity Index.</p>
<div class="picker"><label for="country" style="font-weight:600">Importer:</label>
<select id="country" aria-label="Choose importing country"></select>
<span class="mut" id="loading" style="color:var(--mut);font-size:13px"></span></div>
<p class="links"><a href="REPO_URL">Code and methodology</a><span style="color:var(--mut)">Prepared by Dr. Ian Helfrich</span></p>
</header>

<div class="cards" id="kpis" aria-live="polite"></div>

<div class="panel">
<h2>Scoring weights and thresholds</h2>
<p class="note">The composite score is a weighted blend of three normalized indicators (0-100), re-scaled to sum to one. Thresholds set the quadrant boundaries. Indicators are normalized within the selected country's import basket.</p>
<div class="controls">
  <div class="ctl"><label for="wD">Import dependence <span class="v" id="wDv"></span></label><input type="range" id="wD" min="0" max="100" value="42"></div>
  <div class="ctl"><label for="wS">Import scale <span class="v" id="wSv"></span></label><input type="range" id="wS" min="0" max="100" value="25"></div>
  <div class="ctl"><label for="wC">Economic complexity <span class="v" id="wCv"></span></label><input type="range" id="wC" min="0" max="100" value="33"></div>
  <div class="ctl"><label for="eThr">Exposure threshold <span class="v" id="eThrv"></span></label><input type="range" id="eThr" min="0" max="100" value="60"></div>
  <div class="ctl"><label for="cThr">Complexity threshold <span class="v" id="cThrv"></span></label><input type="range" id="cThr" min="0" max="100" value="60"></div>
  <div class="ctl" style="align-self:end"><button class="btn" id="reset" type="button">Reset defaults</button></div>
</div>
</div>

<div class="grid">
<div class="panel">
<h2>The decision map</h2>
<p class="note">Each product by China exposure (horizontal) and economic complexity (vertical); size is import value. Upper-right (green) is the localize quadrant. Hover a point for detail.</p>
<canvas id="scatter" width="720" height="520" role="img" aria-label="Scatter of products by China exposure and economic complexity, colored by quadrant. The accessible ranking is the table to the right."></canvas>
<div class="legend">
 <span><i class="dot" style="background:var(--A)"></i>A Localize <span id="nA"></span></span>
 <span><i class="dot" style="background:var(--B)"></i>B Diversify <span id="nB"></span></span>
 <span><i class="dot" style="background:var(--C)"></i>C Watch <span id="nC"></span></span>
 <span><i class="dot" style="background:var(--D)"></i>D Low <span id="nD"></span></span>
</div>
</div>

<div class="panel">
<h2>Ranked products <span class="note" id="tblcount" style="font-weight:400"></span></h2>
<div class="tools">
 <input id="search" type="search" placeholder="Search product or HS6" aria-label="Search products">
 <select id="chsel" aria-label="Filter by HS2 chapter"><option value="">All chapters</option></select>
 <select id="qsel" aria-label="Filter by quadrant"><option value="">All quadrants</option><option value="A">A Localize</option><option value="B">B Diversify</option><option value="C">C Watch</option><option value="D">D Low</option></select>
</div>
<div class="tblwrap"><table id="tbl"><thead><tr>
 <th data-k="rank" class="num">#</th><th data-k="hs6">HS6</th><th data-k="name">Product</th>
 <th data-k="Mchina" class="num">China $m</th><th data-k="D" class="num">Dep%</th>
 <th data-k="PCI" class="num">PCI</th><th data-k="cps" class="num">CPS</th><th data-k="q">Q</th>
</tr></thead><tbody id="tbody"></tbody></table></div>
</div>
</div>

<div class="panel">
<h2>Sector dependence: top chapters by China import value</h2>
<p class="note">Red marks chapters that are also at least 50 percent China-dependent for this country.</p>
<div class="bars" id="bars"></div>
</div>

<div class="panel scope">
<h2>Scope and honesty note</h2>
<p class="note" style="margin:0">Scores rest on the dimensions computable from hard public data: import dependence, scale, and economic complexity. Three dimensions of the full framework (domestic value added, ESG, policy alignment) need country-specific data and are left as documented inputs, not fabricated. Treat the localize shortlist as a first screen, not a finished investment list.</p>
</div>

<p class="foot">Data: CEPII BACI (Etalab 2.0 licence), HS 2022, 2022-2023 average, and the Observatory of Economic Complexity Product Complexity Index. Only countries with at least 200 million dollars of imports from China are included. Runs entirely in your browser. Method and tool by Dr. Ian Helfrich. &copy; 2026 Ian Helfrich.</p>
</div>
<div class="tip" id="tip" role="status"></div>
<script>
const CHNAME=__CH__;
const QC={A:'',B:'',C:'',D:''};function refreshQC(){for(const k in QC)QC[k]=getComputedStyle(document.documentElement).getPropertyValue('--'+k);}refreshQC();
let PROD=[], COMP=[], INDEX=[];
const S={wD:42,wS:25,wC:33,eThr:60,cThr:60,sortK:'cps',sortDir:1,q:'',ch:'',search:'',iso:'',name:''};
function norm(){const s=S.wD+S.wS+S.wC||1;return[S.wD/s,S.wS/s,S.wC/s];}
// record: 0 hs6,1 name,2 ch,3 Mchina$m,4 D%,5 PCI,6 zD,7 zS,8 zC,9 EXP,10 SOPH,11 mat
function compute(){const[wd,ws,wc]=norm();COMP=PROD.map(p=>{
 const zD=p[6],zS=p[7],zC=p[8];let num=0,den=0;
 if(zD!=null){num+=wd*zD;den+=wd;}if(zS!=null){num+=ws*zS;den+=ws;}if(zC!=null){num+=wc*zC;den+=wc;}
 const cps=den>0?num/den:null;
 const hiE=p[9]!=null&&p[9]>=S.eThr,hiC=p[10]!=null&&p[10]>=S.cThr;
 const q=hiE&&hiC?'A':hiE&&!hiC?'B':!hiE&&hiC?'C':'D';
 return{hs6:p[0],name:p[1],ch:p[2],Mchina:p[3],D:p[4],PCI:p[5],EXP:p[9],SOPH:p[10],mat:p[11],cps,q};});}
function fmt(x,d){return x==null?'-':x.toFixed(d);}
function kpis(){const tot=PROD.reduce((a,p)=>a+(p[3]||0),0)/1000;
 const A=COMP.filter(c=>c.q==='A'),short=A.filter(c=>c.mat);
 const shortVal=short.reduce((a,c)=>a+c.Mchina,0)/1000;const cnt={A:0,B:0,C:0,D:0};COMP.forEach(c=>cnt[c.q]++);
 document.getElementById('kpis').innerHTML=[
  ['$'+tot.toFixed(1)+'b',S.name+' imports from China'],
  [PROD.length.toLocaleString(),'HS6 products'],
  [cnt.A.toLocaleString(),'in Localize quadrant (A)'],
  [short.length.toLocaleString(),'shortlist (>$5m, $'+shortVal.toFixed(1)+'b)'],
 ].map(c=>`<div class="card"><div class="k">${c[0]}</div><div class="l">${c[1]}</div></div>`).join('');
 nA.textContent='('+cnt.A+')';nB.textContent='('+cnt.B+')';nC.textContent='('+cnt.C+')';nD.textContent='('+cnt.D+')';}
const cv=document.getElementById('scatter'),ctx=cv.getContext('2d');
const PADL=54,PADR=18,PADT=20,PADB=44,W=720,H=520;
const sx=v=>PADL+(v/100)*(W-PADL-PADR),sy=v=>H-PADB-(v/100)*(H-PADT-PADB);
function scatter(){ctx.clearRect(0,0,W,H);const cs=getComputedStyle(document.documentElement);
 ctx.strokeStyle=cs.getPropertyValue('--line');ctx.setLineDash([4,4]);ctx.beginPath();
 ctx.moveTo(sx(S.eThr),PADT);ctx.lineTo(sx(S.eThr),H-PADB);ctx.moveTo(PADL,sy(S.cThr));ctx.lineTo(W-PADR,sy(S.cThr));ctx.stroke();ctx.setLineDash([]);
 const order={D:0,C:1,B:2,A:3};
 COMP.slice().sort((a,b)=>order[a.q]-order[b.q]).forEach(c=>{if(c.EXP==null||c.SOPH==null)return;
  const r=1.4+2.4*Math.min(1,Math.max(0,Math.log10(Math.max(c.Mchina,0.01))+1)/4);
  ctx.globalAlpha=c.q==='A'?.85:.32;ctx.fillStyle=QC[c.q].trim();
  ctx.beginPath();ctx.arc(sx(c.EXP),sy(c.SOPH),c.q==='A'?r*1.3:r,0,7);ctx.fill();});
 ctx.globalAlpha=1;ctx.fillStyle=cs.getPropertyValue('--mut');ctx.font='12px sans-serif';ctx.textAlign='center';
 ctx.fillText('China exposure  →',W/2,H-12);ctx.save();ctx.translate(14,H/2);ctx.rotate(-Math.PI/2);ctx.fillText('Economic complexity  →',0,0);ctx.restore();
 ctx.fillStyle=QC.A.trim();ctx.fillText('A LOCALIZE',sx(82),sy(96));ctx.fillStyle=QC.B.trim();ctx.fillText('B DIVERSIFY',sx(82),sy(6));
 ctx.fillStyle=QC.C.trim();ctx.fillText('C WATCH',sx(16),sy(96));ctx.fillStyle=QC.D.trim();ctx.fillText('D LOW',sx(14),sy(6));}
function tableData(){let rows=COMP.filter(c=>c.cps!=null);
 if(S.q)rows=rows.filter(c=>c.q===S.q);if(S.ch)rows=rows.filter(c=>c.ch===S.ch);
 if(S.search){const q=S.search.toLowerCase();rows=rows.filter(c=>c.name.toLowerCase().includes(q)||c.hs6.includes(q));}
 rows.sort((a,b)=>{let A,B;if(S.sortK==='rank'||S.sortK==='cps'){A=a.cps;B=b.cps;}
  else if(S.sortK==='name'){A=a.name;B=b.name;}else if(S.sortK==='hs6'){A=a.hs6;B=b.hs6;}else if(S.sortK==='q'){A=a.q;B=b.q;}else{A=a[S.sortK];B=b[S.sortK];}
  return (A<B?-1:A>B?1:0)*(S.sortK==='cps'||S.sortK==='rank'?-1:1)*S.sortDir;});return rows;}
function table(){const rows=tableData();document.getElementById('tblcount').textContent='('+rows.length+' shown)';
 document.getElementById('tbody').innerHTML=rows.slice(0,60).map((c,i)=>
  `<tr><td class="num">${i+1}</td><td class="mono">${c.hs6}</td><td>${c.name.replace(/</g,'&lt;')}</td>
   <td class="num">${fmt(c.Mchina,1)}</td><td class="num">${fmt(c.D,0)}%</td><td class="num">${fmt(c.PCI,2)}</td>
   <td class="num"><b>${fmt(c.cps,1)}</b></td><td class="q${c.q}">${c.q}</td></tr>`).join('');}
function bars(){const agg={};PROD.forEach(p=>{const ch=p[2];const mc=p[3]||0;const mw=p[4]>0?mc/(p[4]/100):mc;
  if(!agg[ch])agg[ch]={c:0,w:0};agg[ch].c+=mc;agg[ch].w+=mw;});
 const arr=Object.entries(agg).map(([ch,o])=>({ch,c:o.c/1000,share:o.w>0?100*o.c/o.w:0})).sort((a,b)=>b.c-a.c).slice(0,12);
 const mx=Math.max(...arr.map(a=>a.c),0.01);
 document.getElementById('bars').innerHTML=arr.map(a=>{const col=a.share>=50?'var(--red)':'var(--navy)';
  return `<div class="row"><div class="lab">${a.ch} ${(CHNAME[a.ch]||'').slice(0,32)}</div>
   <div class="track"><div class="fill" style="width:${100*a.c/mx}%;background:${col}"></div></div>
   <div class="val">$${a.c.toFixed(1)}b &middot; ${a.share.toFixed(0)}%</div></div>`;}).join('');}
function refreshAll(){compute();kpis();scatter();table();bars();
 const chs=[...new Set(PROD.map(p=>p[2]))].sort();const sel=document.getElementById('chsel');
 sel.innerHTML='<option value="">All chapters</option>'+chs.map(c=>`<option value="${c}">${c} ${(CHNAME[c]||'').slice(0,30)}</option>`).join('');}
async function loadCountry(iso){document.getElementById('loading').textContent='loading...';
 const r=await fetch('data/'+iso+'.json');PROD=await r.json();
 const meta=INDEX.find(d=>d.iso===iso)||{};S.iso=iso;S.name=meta.name||iso;
 document.getElementById('title').textContent='Import Localization Atlas: '+S.name+' and China';
 document.getElementById('loading').textContent='';refreshAll();}
function bindSlider(id,key){const el=document.getElementById(id),v=document.getElementById(id+'v');
 const setw=()=>{wDv.textContent=Math.round(norm()[0]*100)+'%';wSv.textContent=Math.round(norm()[1]*100)+'%';wCv.textContent=Math.round(norm()[2]*100)+'%';};
 if(key.startsWith('w'))setw();else v.textContent=el.value+' / 100';
 el.addEventListener('input',()=>{S[key]=+el.value;if(key.startsWith('w'))setw();else v.textContent=el.value+' / 100';requestAnimationFrame(refreshAll);});}
['wD','wS','wC','eThr','cThr'].forEach(id=>bindSlider(id,id));
document.getElementById('reset').onclick=()=>{const d={wD:42,wS:25,wC:33,eThr:60,cThr:60};
 for(const k in d){S[k]=d[k];document.getElementById(k).value=d[k];}
 wDv.textContent='42%';wSv.textContent='25%';wCv.textContent='33%';eThrv.textContent='60 / 100';cThrv.textContent='60 / 100';refreshAll();};
document.getElementById('search').addEventListener('input',e=>{S.search=e.target.value;table();});
document.getElementById('chsel').addEventListener('change',e=>{S.ch=e.target.value;table();});
document.getElementById('qsel').addEventListener('change',e=>{S.q=e.target.value;table();});
document.querySelectorAll('#tbl th').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;if(S.sortK===k)S.sortDir*=-1;else{S.sortK=k;S.sortDir=1;}table();}));
document.getElementById('country').addEventListener('change',e=>loadCountry(e.target.value));
const tip=document.getElementById('tip');
cv.addEventListener('mousemove',e=>{const rect=cv.getBoundingClientRect();const mx=(e.clientX-rect.left)*(W/rect.width),my=(e.clientY-rect.top)*(H/rect.height);
 let best=null,bd=1e9;COMP.forEach(c=>{if(c.EXP==null||c.SOPH==null)return;const dx=sx(c.EXP)-mx,dy=sy(c.SOPH)-my,d=dx*dx+dy*dy;if(d<bd){bd=d;best=c;}});
 if(best&&bd<120){tip.style.opacity=1;tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';
  tip.innerHTML=`<b>${best.hs6}</b> ${best.name}<br>$${fmt(best.Mchina,1)}m &middot; dep ${fmt(best.D,0)}% &middot; PCI ${fmt(best.PCI,2)} &middot; CPS ${fmt(best.cps,1)} &middot; Q${best.q}`;}
 else tip.style.opacity=0;});
cv.addEventListener('mouseleave',()=>tip.style.opacity=0);
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',()=>{refreshQC();scatter();});
// init: load country index, populate dropdown, default to Saudi Arabia if present
(async()=>{INDEX=await (await fetch('index.json')).json();
 const sel=document.getElementById('country');
 sel.innerHTML=INDEX.map(d=>`<option value="${d.iso}">${d.name} ($${d.china_bn.toFixed(0)}b)</option>`).join('');
 const def=INDEX.find(d=>d.iso==='SAU')?'SAU':INDEX[0].iso;sel.value=def;loadCountry(def);})();
</script></body></html>"""
HTML = HTML.replace("__CH__", CH).replace("REPO_URL", REPO)
open("docs/index.html","w").write(HTML)
print("wrote docs/index.html (%.0f KB)" % (len(HTML)/1024))
