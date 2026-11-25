"""
06_build_plotly_dashboard.py - Track A, Task 5: interactive Plotly dashboard.
Builds ONE standalone HTML file (data embedded, Plotly.js loaded from the Plotly CDN,
so an internet connection is needed when the file is opened).
Embedded stocks: the 10 selected stocks + the 50 most-traded other full-history stocks
(by average close x volume), so the file stays ~5 MB. Overview KPIs cover all 505 symbols.
"""
import json
import numpy as np
import pandas as pd
import sp500_utils as u

df = pd.read_csv(u.PROCESSED / "sp500_clean_full.csv", parse_dates=["date"])
summ = pd.read_csv(u.PROCESSED / "symbol_summary.csv")
full = summ[(summ.history_status == "Full period") & (summ.trading_days == 1007)]

dv = df.assign(dv=df.close * df.volume).groupby("symbol")["dv"].mean()
extra = [s for s in dv.loc[full.symbol].sort_values(ascending=False).index if s not in u.SELECTED][:50]
embed = u.SELECTED + extra
dates = sorted(df.date.unique())
date_str = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in dates]


def arr(s, nd=4):
    return [None if pd.isna(x) else round(float(x), nd) for x in s]


stocks = {}
for s in embed:
    d = df[df.symbol == s].set_index("date").reindex(dates)
    stocks[s] = dict(o=arr(d.open), h=arr(d.high), l=arr(d.low), c=arr(d.close), v=[None if pd.isna(x) else int(x) for x in d.volume],
                     r=arr(d.daily_return_clean_pct, 3), m5=arr(d.ma_5, 3), m20=arr(d.ma_20, 3), m50=arr(d.ma_50, 3),
                     rv=arr(d.rolling_vol_20, 3))

yr = df.groupby("year").size()
td = summ.trading_days.tolist()
data = dict(
    dates=date_str, stocks=stocks, selected=u.SELECTED,
    kpi=dict(symbols=int(df.symbol.nunique()), records=int(len(df)), start=date_str[0], end=date_str[-1],
             full=int((summ.history_status == "Full period").sum()), partial=int((summ.history_status != "Full period").sum())),
    records_by_year={str(k): int(v) for k, v in yr.items()},
    trading_days=td,
    summary={r.symbol: dict(ret=round(r.adj_period_return_pct, 2), vol=round(r.annualised_volatility_pct, 2)) for r in summ.itertuples()
             if r.symbol in embed},
)

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>S&P 500 Market Intelligence Dashboard 2014-2017</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
:root{--bg:#f5f7fa;--card:#fff;--ink:#1d2733;--mut:#5c6b7a;--acc:#2a6f97;--line:#dde3ea}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
header{background:#14324a;color:#fff;padding:14px 22px}header h1{margin:0;font-size:20px}header p{margin:4px 0 0;font-size:12px;opacity:.8}
.layout{display:flex;gap:16px;padding:16px}aside{width:240px;flex:none;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;height:fit-content;position:sticky;top:12px}
aside label{display:block;font-size:12px;font-weight:600;color:var(--mut);margin:10px 0 4px}aside select,aside input{width:100%;font-size:13px;padding:5px;border:1px solid var(--line);border-radius:5px}
aside select{height:230px}button{background:var(--acc);color:#fff;border:0;border-radius:5px;padding:7px 10px;font-size:12px;cursor:pointer;margin:6px 4px 0 0}
main{flex:1;min-width:0}nav{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}nav button{background:#fff;color:var(--ink);border:1px solid var(--line);padding:8px 14px;margin:0}nav button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.page{display:none}.page.on{display:block}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:12px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}.kpi b{display:block;font-size:22px;color:var(--acc)}.kpi span{font-size:12px;color:var(--mut)}
.wide{grid-column:1/-1}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:5px 8px;border-bottom:1px solid var(--line);text-align:right}th:first-child,td:first-child{text-align:left}th{background:#eef2f6}
.note{font-size:12px;color:var(--mut);margin:8px 2px}@media(max-width:900px){.layout{flex-direction:column}aside{width:auto;position:static}.grid{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
</style></head><body>
<header><h1>S&amp;P 500 Market Intelligence Dashboard</h1><p>Historical daily prices 2 Jan 2014 - 29 Dec 2017 &middot; AnalystLab Africa Week 6 &middot; Historical performance only - not investment advice, not current market data</p></header>
<div class="layout">
<aside>
 <label>Stock symbols (Ctrl/Cmd-click for several)</label><select id="sym" multiple></select>
 <div><button onclick="pick('sel')">Selected 10</button><button onclick="pick('tech')">Tech</button><button onclick="pick('all')">All 60</button></div>
 <label>Start date</label><input type="date" id="d0"><label>End date</label><input type="date" id="d1">
 <label>Moving-average stock (pages 2)</label><select id="maSym" style="height:auto"></select>
 <div><button onclick="render()">Apply filters</button><button onclick="resetAll()">Reset</button></div>
 <p class="note">Dashboard embeds 60 stocks (the 10 selected + the 50 most-traded full-history stocks). Page 1 KPIs cover all 505 symbols. Returns exclude 13 flagged non-market events.</p>
</aside>
<main>
<nav id="nav"></nav>
<section class="page on" id="p0"><div class="kpis" id="k0"></div><div class="grid">
 <div class="card"><div id="c0a"></div></div><div class="card"><div id="c0b"></div></div>
 <div class="card"><div id="c0c"></div></div><div class="card"><div id="c0d"></div></div></div>
 <p class="note">General market overview: 483 of 505 symbols have a full-period history; 22 are partial (listed or removed during the period, e.g. APTV 18 days). Prices are as supplied (currency not stated, USD assumed; adjustment for splits/dividends cannot be verified).</p></section>
<section class="page" id="p1"><div class="grid">
 <div class="card wide"><div id="c1a"></div></div><div class="card"><div id="c1b"></div></div><div class="card"><div id="c1c"></div></div>
 <div class="card"><div id="c1d"></div></div><div class="card"><div id="c1e"></div></div></div></section>
<section class="page" id="p2"><div class="grid">
 <div class="card wide"><div id="c2a"></div></div><div class="card"><div id="c2b"></div></div><div class="card"><div id="c2c"></div></div>
 <div class="card"><div id="c2d"></div></div><div class="card"><div id="c2e"></div></div><div class="card wide" id="t2"></div></div></section>
<section class="page" id="p3"><div class="kpis" id="k3"></div><div class="grid">
 <div class="card wide"><div id="c3a"></div></div><div class="card"><div id="c3b"></div></div><div class="card"><div id="c3c"></div></div>
 <div class="card wide"><div id="c3d"></div></div><div class="card wide" id="t3"></div></div>
 <p class="note">Volume = number of shares traded (not money value). Zero-volume placeholder rows are excluded.</p></section>
</main></div>
<script>
const D = __DATA__;
const PAL=["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"];
const PAGES=["Market Overview","Stock Price Performance","Returns & Volatility","Trading Volume Analysis"];
const syms=Object.keys(D.stocks), N=D.dates.length, color=s=>PAL[syms.indexOf(s)%10];
const TECH=["AAPL","MSFT","AMZN","GOOGL","NFLX","NVDA"];
const $=id=>document.getElementById(id);
const LAY=(t,y)=>({title:{text:t,font:{size:14}},margin:{l:55,r:15,t:40,b:40},legend:{orientation:"h",y:-0.2},yaxis:{title:y||""},hovermode:"x unified",font:{family:"Segoe UI,Arial"}});
const CFG={responsive:true,displaylogo:false};
let page=0;
const fmt=(x,d=2)=>x==null||isNaN(x)?"-":Number(x).toLocaleString(undefined,{maximumFractionDigits:d,minimumFractionDigits:d});
const mean=a=>{a=a.filter(x=>x!=null);return a.length?a.reduce((p,c)=>p+c,0)/a.length:null};
const sd=a=>{a=a.filter(x=>x!=null);if(a.length<2)return null;const m=mean(a);return Math.sqrt(a.reduce((p,c)=>p+(c-m)**2,0)/(a.length-1))};
function init(){
 $("nav").innerHTML=PAGES.map((p,i)=>`<button class="${i?'':'on'}" onclick="go(${i})">Page ${i+1}: ${p}</button>`).join("");
 $("sym").innerHTML=syms.map(s=>`<option value="${s}" ${D.selected.slice(0,5).includes(s)?'selected':''}>${s}${D.selected.includes(s)?' *':''}</option>`).join("");
 $("maSym").innerHTML=syms.map(s=>`<option>${s}</option>`).join("");
 $("d0").value=D.dates[0];$("d1").value=D.dates[N-1];$("d0").min=$("d1").min=D.dates[0];$("d0").max=$("d1").max=D.dates[N-1];
 $("sym").onchange=$("d0").onchange=$("d1").onchange=$("maSym").onchange=render;render();
}
function go(i){page=i;document.querySelectorAll(".page").forEach((e,j)=>e.classList.toggle("on",i==j));document.querySelectorAll("#nav button").forEach((e,j)=>e.classList.toggle("on",i==j));render()}
function pick(k){[...$("sym").options].forEach(o=>o.selected=k=="all"||(k=="sel"&&D.selected.includes(o.value))||(k=="tech"&&TECH.includes(o.value)));render()}
function resetAll(){$("d0").value=D.dates[0];$("d1").value=D.dates[N-1];pick("sel")}
function state(){let S=[...$("sym").selectedOptions].map(o=>o.value);if(!S.length)S=["AAPL"];
 let a=D.dates.findIndex(d=>d>=$("d0").value);if(a<0)a=0;let b=N-1;while(b>0&&D.dates[b]>$("d1").value)b--;if(b<a)b=a;
 return {S,a,b,X:D.dates.slice(a,b+1),sl:(s,k)=>D.stocks[s][k].slice(a,b+1),ma:$("maSym").value||S[0]}}
function render(){const st=state();[p0,p1,p2,p3][page](st)}
function p0(st){
 const K=D.kpi, avgs=st.S.map(s=>mean(st.sl(s,"c")));
 $("k0").innerHTML=[["Total stock symbols",K.symbols],["Total trading records",K.records.toLocaleString()],["Date range",K.start+" to "+K.end],
  ["Avg close - selected stocks","$"+fmt(mean(avgs))],["Full / partial histories",K.full+" / "+K.partial]].map(x=>`<div class="kpi"><b>${x[1]}</b><span>${x[0]}</span></div>`).join("");
 const yrs=Object.keys(D.records_by_year);
 Plotly.react("c0a",[{x:yrs,y:yrs.map(y=>D.records_by_year[y]),type:"bar",marker:{color:"#2a6f97"},text:yrs.map(y=>D.records_by_year[y].toLocaleString()),textposition:"outside"}],LAY("Trading records per year"),CFG);
 Plotly.react("c0b",[{labels:["Full-period history","Partial history"],values:[K.full,K.partial],type:"pie",hole:.55,marker:{colors:["#2a6f97","#e69f00"]}}],{...LAY("Symbol distribution by history completeness"),legend:{orientation:"h"}},CFG);
 Plotly.react("c0c",[{x:D.trading_days,type:"histogram",nbinsx:40,marker:{color:"#2a6f97"}}],{...LAY("Distribution of trading days per symbol (1,007 = complete)"),xaxis:{title:"Trading days"},yaxis:{title:"Symbols"}},CFG);
 Plotly.react("c0d",[{x:st.S,y:avgs,type:"bar",marker:{color:st.S.map(color)}}],LAY("Average closing price - selected stocks and date range","USD (assumed)"),CFG);
}
function p1(st){
 Plotly.react("c1a",st.S.map(s=>({x:st.X,y:st.sl(s,"c"),name:s,mode:"lines",line:{color:color(s),width:1.5}})),LAY("Closing price trend","Close"),CFG);
 const m=st.ma; Plotly.react("c1b",[{x:st.X,open:st.sl(m,"o"),high:st.sl(m,"h"),low:st.sl(m,"l"),close:st.sl(m,"c"),type:"candlestick",name:m,increasing:{line:{color:"#2d936c"}},decreasing:{line:{color:"#c0392b"}}}],{...LAY("Open / high / low / close - "+m),xaxis:{rangeslider:{visible:false}}},CFG);
 Plotly.react("c1c",["o","h","l","c"].map((k,i)=>({x:st.S,y:st.S.map(s=>mean(st.sl(s,k))),type:"bar",name:["Open","High","Low","Close"][i],marker:{color:["#e69f00","#2d936c","#c0392b","#2a6f97"][i]}})),{...LAY("Average open, high, low, close by stock"),barmode:"group"},CFG);
 Plotly.react("c1d",st.S.map(s=>({x:st.X,y:st.sl(s,"h").map((h,i)=>h==null||st.sl(s,"l")[i]==null?null:+(h-st.sl(s,"l")[i]).toFixed(3)),name:s,mode:"lines",line:{color:color(s),width:1}})),LAY("Daily trading range (high - low)","USD"),CFG);
 Plotly.react("c1e",[["c","Close","#9aa5b1"],["m5","MA 5","#e69f00"],["m20","MA 20","#2a6f97"],["m50","MA 50","#c0392b"]].map(t=>({x:st.X,y:st.sl(m,t[0]),name:t[1],mode:"lines",line:{color:t[2],width:t[0]=="c"?1:1.6}})),LAY("Moving averages - "+m,"Price"),CFG);
}
function p2(st){
 Plotly.react("c2a",st.S.map(s=>({x:st.X,y:st.sl(s,"r"),name:s,mode:"lines",line:{color:color(s),width:1}})),LAY("Daily percentage returns","%"),CFG);
 Plotly.react("c2b",[{x:st.S,y:st.S.map(s=>mean(st.sl(s,"r"))),type:"bar",marker:{color:st.S.map(color)}}],LAY("Average daily return (%)","%"),CFG);
 Plotly.react("c2c",st.S.map(s=>({x:st.sl(s,"r").filter(v=>v!=null),type:"histogram",name:s,opacity:.6,xbins:{start:-8,end:8,size:.5},marker:{color:color(s)}})),{...LAY("Return distribution"),barmode:"overlay",xaxis:{title:"Daily return (%)"},hovermode:"closest"},CFG);
 const vol=st.S.map(s=>sd(st.sl(s,"r"))*Math.sqrt(252));
 Plotly.react("c2d",[{x:st.S,y:vol,type:"bar",marker:{color:st.S.map(color)}}],LAY("Historical volatility (annualised %)","%"),CFG);
 Plotly.react("c2e",st.S.map(s=>({x:st.X,y:st.sl(s,"rv").map(v=>v==null?null:v*Math.sqrt(252)),name:s,mode:"lines",line:{color:color(s),width:1.2}})),LAY("Rolling 20-day volatility (annualised %)","%"),CFG);
 let rows=st.S.map(s=>{const c=st.sl(s,"c").filter(v=>v!=null),r=st.sl(s,"r");return `<tr><td>${s}</td><td>${fmt(mean(r),3)}</td><td>${fmt(sd(r),3)}</td><td>${fmt(sd(r)*Math.sqrt(252),1)}</td><td>${fmt((c[c.length-1]/c[0]-1)*100,1)}</td><td>${fmt(Math.min(...r.filter(v=>v!=null)),2)}</td><td>${fmt(Math.max(...r.filter(v=>v!=null)),2)}</td></tr>`}).join("");
 $("t2").innerHTML=`<table><tr><th>Symbol</th><th>Mean daily return %</th><th>Daily volatility %</th><th>Annualised vol %</th><th>Price return in range %</th><th>Worst day %</th><th>Best day %</th></tr>${rows}</table>`;
}
function p3(st){
 const allv=[];st.S.forEach(s=>st.sl(s,"v").forEach((v,i)=>{if(v)allv.push([s,st.X[i],v])}));allv.sort((a,b)=>b[2]-a[2]);
 const lo=[...allv].reverse().slice(0,5), hi=allv.slice(0,5);
 $("k3").innerHTML=[["Avg daily volume (shares)",fmt(mean(allv.map(x=>x[2])),0)],["Highest volume observation",hi[0]?fmt(hi[0][2],0)+" ("+hi[0][0]+")":"-"],["Lowest non-zero volume",lo[0]?fmt(lo[0][2],0)+" ("+lo[0][0]+")":"-"],["Symbols selected",st.S.length],["Trading days in range",st.X.length]].map(x=>`<div class="kpi"><b>${x[1]}</b><span>${x[0]}</span></div>`).join("");
 Plotly.react("c3a",st.S.map(s=>{const g={};st.sl(s,"v").forEach((v,i)=>{if(v){const k=st.X[i].slice(0,7);(g[k]=g[k]||[]).push(v)}});const ks=Object.keys(g);return {x:ks.map(k=>k+"-01"),y:ks.map(k=>mean(g[k])),name:s,mode:"lines",line:{color:color(s),width:1.6}}}),LAY("Trading volume trend (monthly average shares)","Shares"),CFG);
 Plotly.react("c3b",[{x:st.S,y:st.S.map(s=>mean(st.sl(s,"v"))),type:"bar",marker:{color:st.S.map(color)}}],LAY("Average trading volume","Shares"),CFG);
 Plotly.react("c3c",st.S.map(s=>{const r=st.sl(s,"r"),v=st.sl(s,"v"),x=[],y=[];r.forEach((q,i)=>{if(q!=null&&v[i]){x.push(v[i]/1e6);y.push(Math.abs(q))}});return {x,y,name:s,mode:"markers",type:"scatter",marker:{size:4,opacity:.5,color:color(s)}}}),{...LAY("Volume vs size of daily price move"),xaxis:{title:"Volume (million shares, log)",type:"log"},yaxis:{title:"|Daily return| %"},hovermode:"closest"},CFG);
 Plotly.react("c3d",[{x:st.S,y:st.S.map(s=>Math.max(...st.sl(s,"v").filter(v=>v))),type:"bar",name:"Highest",marker:{color:"#2a6f97"}},{x:st.S,y:st.S.map(s=>Math.min(...st.sl(s,"v").filter(v=>v))),type:"bar",name:"Lowest (non-zero)",marker:{color:"#e69f00"}}],{...LAY("Highest and lowest volume observation by stock","Shares"),barmode:"group",yaxis:{type:"log",title:"Shares (log)"}},CFG);
 $("t3").innerHTML=`<table><tr><th colspan="3">Top 5 highest-volume observations</th><th colspan="3">Top 5 lowest non-zero volume observations</th></tr><tr><th>Symbol</th><th>Date</th><th>Volume</th><th>Symbol</th><th>Date</th><th>Volume</th></tr>`+hi.map((h,i)=>`<tr><td>${h[0]}</td><td>${h[1]}</td><td>${fmt(h[2],0)}</td><td>${lo[i][0]}</td><td>${lo[i][1]}</td><td>${fmt(lo[i][2],0)}</td></tr>`).join("")+`</table>`;
}
init();
</script></body></html>
"""
out = u.ROOT / "05_Plotly_Dashboard" / "SP500_Interactive_Dashboard.html"
out.write_text(HTML.replace("__DATA__", json.dumps(data, separators=(",", ":"))), encoding="utf-8")
print("written", out, round(out.stat().st_size / 1e6, 2), "MB; stocks embedded:", len(embed))
