"""Halaman Profil Puskesmas — radar overlay (vs rata-rata) + carousel per dimensi + rating Google Maps."""
import json
import streamlit as st
import streamlit.components.v1 as components

from lib.theme import setup, DIM_INFO, DIM_ORDER
from lib.data import load_profiles, load_gmaps_meta, compute_rankings

setup("Profil Puskesmas")


def build_data(prof: dict, meta: dict, rk: dict, pid: str) -> dict:
    dims = []
    for key in DIM_ORDER:
        d = prof["dimensi"].get(key)
        if not d:
            continue
        label, desc, short = DIM_INFO[key]
        rate = float(d["intensitas_rate"])
        n = int(d["n_reviews"])
        rr = rk["dim_rank"][key].get(pid, {})
        dims.append({
            "term": key, "label": label, "desc": desc, "short": short,
            "cukup": bool(d.get("cukup_dinilai", False)),
            "rate": rate, "n": n, "nc": round(rate * n),
            "pct_lebih": rr.get("pct_lebih_sering"),     # None bila tidak cukup dinilai
            "issues": [{"isu": s["isu"], "n": s["n_ulasan"], "quote": s.get("contoh_quote", "")}
                       for s in d.get("top_sub_issues", [])],
        })
    dim_avg = {d: round(rk["dim_avg"][d] * 100, 1) for d in DIM_ORDER}
    return {"nama": prof["nama"], "wilayah": prof["wilayah"], "dims": dims,
            "gmaps": meta, "dim_avg": dim_avg}


HTML = r"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 *{box-sizing:border-box; margin:0; padding:0; font-family:'Inter',sans-serif;}
 body{ background:#eef1f4; color:#16202b; padding:2px; }
 .wrap{ max-width:820px; margin:0 auto; }

 .gcard{ background:#fff; border-radius:18px; padding:18px 24px; margin-bottom:14px; box-shadow:0 1px 3px rgba(16,32,48,.07); }
 .gcard-head{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:14px; }
 .pkm-name{ font-size:25px; font-weight:700; line-height:1.15; }
 .pkm-region{ font-size:13px; color:#64748b; margin-top:2px; }
 .gmaps-btn{ display:inline-flex; align-items:center; gap:6px; font-size:12.5px; font-weight:600;
       text-decoration:none; color:#185FA5; background:#eaf1f9; padding:8px 13px; border-radius:10px; white-space:nowrap; }
 .gmaps-btn:hover{ background:#dde9f6; }
 .rating-wrap{ display:flex; gap:26px; align-items:center; }
 .rating-big{ text-align:center; flex-shrink:0; }
 .rating-num{ font-size:40px; font-weight:700; line-height:1; }
 .rating-stars{ color:#e0a83a; font-size:15px; letter-spacing:1px; margin:3px 0; }
 .rating-count{ font-size:12px; color:#94a3b8; }
 .dist{ flex:1; min-width:0; }
 .dist-row{ display:flex; align-items:center; gap:9px; margin:3px 0; }
 .dist-lab{ font-size:12px; color:#64748b; width:26px; text-align:right; white-space:nowrap; }
 .dist-bg{ display:block; flex:1; height:8px; background:#eef1f4; border-radius:5px; overflow:hidden; }
 .dist-fill{ display:block; height:100%; background:#e0a83a; border-radius:5px; }
 .dist-n{ font-size:11.5px; color:#94a3b8; width:46px; text-align:right; }

 .top{ background:#fff; border-radius:18px; padding:18px 24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(16,32,48,.07); }
 .top-title{ font-size:16px; font-weight:600; color:#334155; margin-bottom:6px; }
 .radar-box{ height:330px; }
 .radar-cap{ font-size:12px; color:#94a3b8; margin-top:4px; line-height:1.5; text-align:center; }

 .tip{ display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px;
       border-radius:50%; background:#cdd5df; color:#fff; font-size:10px; font-weight:700; cursor:help; margin-left:6px; vertical-align:middle; }
 .gtip{ position:fixed; display:none; max-width:230px; background:#16202b; color:#e7ecf2; font-size:12px;
        line-height:1.5; padding:9px 12px; border-radius:9px; z-index:9999; box-shadow:0 8px 24px rgba(0,0,0,.25); pointer-events:none; }

 .caro-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
 .caro-head h3{ font-size:14px; font-weight:600; color:#475569; }
 .arrows button{ border:none; background:#fff; width:32px; height:32px; border-radius:9px; cursor:pointer;
       font-size:17px; color:#475569; box-shadow:0 1px 2px rgba(0,0,0,.1); margin-left:7px; }
 .arrows button:hover{ background:#f1f5f9; }
 .carousel{ display:flex; overflow-x:auto; scroll-snap-type:x mandatory; scrollbar-width:none; }
 .carousel::-webkit-scrollbar{ display:none; }
 .slide{ flex:0 0 100%; scroll-snap-align:center; padding:3px; }

 .card{ background:#fff; border-radius:18px; padding:20px 24px; box-shadow:0 1px 3px rgba(16,32,48,.07); }
 .card-head{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
 .dim-term{ font-size:21px; font-weight:700; letter-spacing:-.01em; }
 .dim-label{ font-size:13.5px; font-weight:600; color:#475569; margin-top:3px; }
 .dim-desc{ font-size:12.5px; color:#94a3b8; margin-top:1px; }
 .badge{ font-size:12.5px; font-weight:600; padding:5px 13px; border-radius:20px; white-space:nowrap; }

 .seg{ display:inline-flex; background:#eef1f4; border-radius:11px; padding:3px; margin:16px 0; }
 .seg-btn{ border:none; background:transparent; font-size:13px; font-weight:600; color:#64748b;
       padding:7px 17px; border-radius:9px; cursor:pointer; transition:all .15s; }
 .seg-btn.active{ background:#fff; color:#16202b; box-shadow:0 1px 2px rgba(0,0,0,.12); }

 .panes{ overflow:hidden; }
 .pane-track{ display:flex; width:200%; transition:transform .32s cubic-bezier(.4,0,.2,1); }
 .pane{ width:50%; flex-shrink:0; padding:2px 3px; max-height:360px; overflow-y:auto; }
 .pane::-webkit-scrollbar{ width:5px; } .pane::-webkit-scrollbar-thumb{ background:#dde3ea; border-radius:3px; }

 .score-row{ display:flex; align-items:center; gap:14px; cursor:default; }
 .bar-bg{ flex:1; height:13px; background:#eef1f4; border-radius:7px; overflow:hidden; }
 .bar-fill{ height:100%; border-radius:7px; transition:width .5s; }
 .score-num{ font-size:22px; font-weight:700; white-space:nowrap; }
 .peer{ font-size:13.5px; color:#475569; margin:15px 0 6px; line-height:1.6; }
 .issue{ display:flex; align-items:baseline; gap:10px; font-size:14px; padding:7px 0; border-top:1px solid #f1f5f9; }
 .issue:first-of-type{ border-top:none; margin-top:4px; }
 .issue .dot{ font-size:10px; } .issue .c{ margin-left:auto; font-size:12.5px; color:#94a3b8; white-space:nowrap; }
 .voice{ font-size:13.5px; color:#334155; font-style:italic; line-height:1.55; background:#f7f9fb;
         border-left:3px solid #cdd5df; border-radius:0 10px 10px 0; padding:11px 14px; margin-bottom:10px; }
 .voice .who{ font-style:normal; color:#94a3b8; font-size:11.5px; display:block; margin-top:5px; }
 .thin{ font-size:13.5px; color:#94a3b8; padding:18px 0; line-height:1.55; }
 .dots{ display:flex; justify-content:center; gap:7px; margin-top:14px; }
 .dot-nav{ width:7px; height:7px; border-radius:50%; background:#cbd5e1; cursor:pointer; transition:all .2s; }
 .dot-nav.active{ background:#0f766e; width:22px; border-radius:4px; }
 /* legend warna radar */
.severity-legend{
  display:flex;
  justify-content:center;
  gap:18px;
  margin-top:10px;
  flex-wrap:wrap;
  font-size:12px;
  color:#64748b;
}

.severity-legend .item{
  display:flex;
  align-items:center;
  gap:6px;
}

.sev-dot{
    width:10px;
    height:10px;
    border-radius:50%;
    display:inline-block;
    flex-shrink:0;
}

.radar-legend{
    display:flex;
    justify-content:center;
    gap:28px;
    margin:12px 0 10px;
    flex-wrap:wrap;
}

.radar-item{
    display:flex;
    align-items:center;
    gap:8px;
    font-size:12px;
    color:#475569;
}

.radar-line{
    position:relative;
    width:34px;
    height:2px;
    flex-shrink:0;
}

.radar-line::before{
    content:"";
    position:absolute;
    left:0;
    right:0;
    top:0;
    border-top:2px solid currentColor;
}

.radar-line.dashed::before{
    border-top-style:dashed;
}

.radar-line::after{
    content:"";
    position:absolute;
    width:8px;
    height:8px;
    border-radius:50%;
    background:currentColor;
    left:50%;
    top:50%;
    transform:translate(-50%,-50%);
}

</style></head>
<body><div class="wrap">
 <div class="gcard">
   <div class="gcard-head">
     <div><div class="pkm-name" id="pName"></div><div class="pkm-region" id="pRegion"></div></div>
     <a class="gmaps-btn" id="gmapsLink" target="_blank" rel="noopener">📍 Buka di Google Maps</a>
   </div>
   <div class="rating-wrap">
     <div class="rating-big"><div class="rating-num" id="ratingNum"></div>
       <div class="rating-stars" id="ratingStars"></div><div class="rating-count" id="ratingCount"></div></div>
     <div class="dist" id="dist"></div>
   </div>
 </div>

  <div class="top">
    <div class="top-title">Profil keluhan vs rata-rata kabupaten
      <span class="tip" data-tip="Makin ke tepi, makin sering aspek itu dikeluhkan (persentase ulasan).">?</span>
    </div>

    <div class="radar-box">
        <canvas id="radar"></canvas>
    </div>

    <div class="radar-legend" id="radarLegend"></div>

    <div class="severity-legend">
        <div class="item">
          <span class="sev-dot" style="background:#d05a4e"></span>
          <span>Sering dikeluhkan</span>
        </div>

        <div class="item">
          <span class="sev-dot" style="background:#c98a2b"></span>
          <span>Cukup sering dikeluhkan</span>
        </div>

        <div class="item">
          <span class="sev-dot" style="background:#2f9e6f"></span>
          <span>Jarang dikeluhkan</span>
        </div>
    </div>
  </div>

 <div class="caro-head"><h3>Geser untuk lihat tiap dimensi →</h3>
   <div class="arrows"><button id="prev">‹</button><button id="next">›</button></div></div>
 <div class="carousel" id="caro"></div>
 <div class="dots" id="dots"></div>
</div>

<script>
const DATA = __DATA__;
const gtip=document.createElement('div'); gtip.className='gtip'; document.body.appendChild(gtip);
document.addEventListener('mouseover', e=>{ const t=e.target.closest('[data-tip]'); if(!t) return;
  gtip.textContent=t.getAttribute('data-tip'); gtip.style.display='block';
  const r=t.getBoundingClientRect();
  let left=Math.max(8, Math.min(r.left+r.width/2-gtip.offsetWidth/2, window.innerWidth-gtip.offsetWidth-8));
  let top=r.top-gtip.offsetHeight-9; if(top<6) top=r.bottom+9;
  gtip.style.left=left+'px'; gtip.style.top=top+'px'; });
document.addEventListener('mouseout', e=>{ if(e.target.closest('[data-tip]')) gtip.style.display='none'; });

function level(rate){
  if(rate>=0.55) return ['#d05a4e','Sering dikeluhkan'];
  if(rate>=0.30) return ['#c98a2b','Cukup sering dikeluhkan'];
  if(rate>=0.12) return ['#2f9e6f','Sesekali dikeluhkan'];
  return ['#2f9e6f','Jarang dikeluhkan'];
}
const PCT_TIP="Semakin tinggi persentasenya, semakin sering aspek ini dikeluhkan dibanding puskesmas lain di wilayah yang sama.";

document.getElementById('pName').textContent='Puskesmas '+DATA.nama;
document.getElementById('pRegion').textContent=DATA.wilayah;

// kartu rating Google Maps (distribusi dinormalisasi ke TOTAL)
const G=DATA.gmaps, avg=G.avg;
document.getElementById('ratingNum').textContent=avg.toFixed(2).replace('.',',');
const full=Math.round(avg);
document.getElementById('ratingStars').textContent='★'.repeat(full)+'☆'.repeat(5-full);
document.getElementById('ratingCount').textContent=G.total.toLocaleString('id')+' ulasan';
if(G.url) document.getElementById('gmapsLink').href=G.url; else document.getElementById('gmapsLink').style.display='none';
const tot=G.total||1;
document.getElementById('dist').innerHTML=[5,4,3,2,1].map(s=>{
  const c=G.dist[s]||0, w=(c/tot*100);
  return `<div class="dist-row"><span class="dist-lab">${s} ★</span>
    <span class="dist-bg"><span class="dist-fill" style="width:${w}%"></span></span>
    <span class="dist-n">${c.toLocaleString('id')}</span></div>`; }).join('');

// radar OVERLAY: puskesmas ini vs rata-rata kabupaten
const dims=DATA.dims;
const pusk=dims.map(d=>Math.round(d.rate*100));
const avgArr=dims.map(d=>DATA.dim_avg[d.term]);
const maxv=Math.max(60, Math.ceil(Math.max(...pusk, ...avgArr)/10)*10);
new Chart(document.getElementById('radar'), { type:'radar',
  data:{
  labels:dims.map(d=>d.short),
  datasets:[
    {
      label:`Rata-rata puskesmas di ${DATA.wilayah}`,
      data:avgArr,
      borderColor:'#9aa7b4',
      borderWidth:1.5,
      borderDash:[5,4],
      pointRadius:0,
      fill:false
    },
    {
      label:`Puskesmas ${DATA.nama}`,
      data:pusk,
      backgroundColor:'rgba(208,90,78,.12)',
      borderColor:'#d05a4e',
      borderWidth:2.5,

      pointRadius:5,
      pointHoverRadius:6,
      pointBackgroundColor:dims.map(d=>level(d.rate)[0]),
      pointBorderColor:'#fff',
      pointBorderWidth:1.5,

      fill:true
    }
  ]
},
  options:{ layout:{padding:6},
    plugins:{ legend:{display:false, position:'bottom', labels:{font:{size:11, family:'Inter'}, usePointStyle:true, boxWidth:32, boxHeight:32, padding:16}},
      tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw}% ulasan mengeluh`}}},
    scales:{ r:{ suggestedMin:0, suggestedMax:maxv, ticks:{display:false}, grid:{color:'#e2e8f0'},
      angleLines:{color:'#e2e8f0'}, pointLabels:{font:{size:11, family:'Inter', weight:'600'}, color:'#334155'} }},
    maintainAspectRatio:false }});

document.getElementById("radarLegend").innerHTML = `
<div class="radar-item">
    <span class="radar-line dashed"
          style="color:#9aa7b4;border-color:#9aa7b4;"></span>
    <span>Rata-rata puskesmas di ${DATA.wilayah}</span>
</div>

<div class="radar-item">
    <span class="radar-line"
          style="color:#d05a4e;border-color:#d05a4e;"></span>
    <span>Puskesmas ${DATA.nama}</span>
</div>
`;    

// carousel
const caro=document.getElementById('caro');
dims.forEach(d=>{
  const [col,lvl]=level(d.rate);
  const pct=Math.max(5, Math.round(d.rate*100));
  let inner;
  if(!d.cukup){ inner=`<div class="thin">Belum banyak warga yang menyinggung hal ini (baru ${d.n} ulasan), jadi belum bisa disimpulkan.</div>`; }
  else{
    const issues=d.issues.map(s=>`<div class="issue"><span class="dot" style="color:${col}">●</span><span>${s.isu}</span><span class="c">${s.n} ulasan</span></div>`).join('');
    const quotes=d.issues.filter(s=>s.quote).map(s=>`<div class="voice">“${s.quote}”<span class="who">— soal ${s.isu}</span></div>`).join('')||`<div class="thin">Belum ada kutipan untuk aspek ini.</div>`;
    const peerLine=(d.pct_lebih!=null)
      ? `<div class="peer" style="color:${col}">Lebih banyak dikeluhkan dibanding <b>${d.pct_lebih}%</b> puskesmas di ${DATA.wilayah}
         <span class="tip" data-tip="${PCT_TIP}">?</span></div>` : '';
    inner=`<div class="seg"><button class="seg-btn active" data-p="0">Ringkasan</button><button class="seg-btn" data-p="1">Suara warga</button></div>
      <div class="panes"><div class="pane-track">
        <div class="pane">
          <div class="score-row" data-tip="${d.nc} dari ${d.n} ulasan menyebut keluhan ini">
            <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${col}"></div></div>
            <div class="score-num" style="color:${col}">${pct}%</div></div>
          ${peerLine}
          <div style="margin-top:6px">${issues}</div>
        </div>
        <div class="pane">${quotes}</div>
      </div></div>`;
  }
  caro.insertAdjacentHTML('beforeend', `<div class="slide"><div class="card">
    <div class="card-head"><div><div class="dim-term">${d.term}</div><div class="dim-label">${d.label}</div><div class="dim-desc">${d.desc}</div></div>
    ${d.cukup?`<div class="badge" style="color:${col}; background:${col}1a">${lvl}</div>`:''}</div>${inner}</div></div>`);
});
caro.addEventListener('click', e=>{ const b=e.target.closest('.seg-btn'); if(!b) return;
  const seg=b.parentElement, track=seg.parentElement.querySelector('.pane-track');
  seg.querySelectorAll('.seg-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active');
  track.style.transform=b.dataset.p==='1'?'translateX(-50%)':'translateX(0)'; });
const dotsEl=document.getElementById('dots');
dims.forEach((_,i)=>{ const dot=document.createElement('div'); dot.className='dot-nav'+(i===0?' active':'');
  dot.onclick=()=>caro.scrollTo({left:i*caro.clientWidth, behavior:'smooth'}); dotsEl.appendChild(dot); });
function curIdx(){ return Math.round(caro.scrollLeft/caro.clientWidth); }
caro.addEventListener('scroll', ()=>{ const i=curIdx(); [...dotsEl.children].forEach((d,j)=>d.classList.toggle('active', j===i)); });
document.getElementById('prev').onclick=()=>caro.scrollTo({left:(curIdx()-1)*caro.clientWidth,behavior:'smooth'});
document.getElementById('next').onclick=()=>caro.scrollTo({left:(curIdx()+1)*caro.clientWidth,behavior:'smooth'});
</script></body></html>
"""

# ---------------------------------------------------------------------------
profiles = load_profiles()
gmaps_meta = load_gmaps_meta()
rankings = compute_rankings()

st.markdown("<div class='page-title'>Profil Puskesmas</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Apa yang paling sering dikeluhkan warga, dirangkum dari "
            "ulasan mereka di Google Maps.</div>", unsafe_allow_html=True)

by_region = {}
for pid, p in profiles.items():
    by_region.setdefault(p["wilayah"], []).append(pid)

c1, c2 = st.columns([1, 1.4])
region = c1.selectbox("Wilayah", sorted(by_region.keys()))
opts = sorted(by_region[region], key=lambda x: profiles[x]["nama"])
pid = c2.selectbox("Puskesmas", opts, format_func=lambda x: profiles[x]["nama"])

data = build_data(profiles[pid],
                  gmaps_meta.get(pid, {"avg": 0, "total": 0, "dist": {}, "url": ""}),
                  rankings, pid)
components.html(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)),
                height=1250, scrolling=False)
