import streamlit as st
import pandas as pd
import plotly.express as px
import os


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Page background — near black */
.stApp { background: #080a12 !important; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1440px; }

/* ── Header ── */
.hdr {
    background: #ffffff08;
    border: 1px solid #ffffff14;
    border-radius: 14px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 2rem;
}
.hdr-eye {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: #6c9fff; margin-bottom: 0.45rem;
}
.hdr h1 {
    font-size: 1.6rem; font-weight: 700; color: #ffffff;
    margin: 0 0 0.2rem; letter-spacing: -0.025em;
}
.hdr p { font-size: 0.84rem; color: #ffffff50; margin: 0; }

/* ── KPI cards — clearly elevated above page bg ── */
.kpi-wrap {
    background: #161b2e;
    border: 1px solid #ffffff18;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.kpi-stripe {
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 12px 12px 0 0;
}
.kpi-v {
    font-size: 2rem; font-weight: 700; color: #ffffff;
    line-height: 1; letter-spacing: -0.04em; margin-bottom: 0.35rem;
}
.kpi-l {
    font-size: 0.7rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.1em; color: #ffffff45;
}

/* ── Section labels ── */
.sec {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #ffffff30;
    margin: 2.2rem 0 0.9rem;
    display: flex; align-items: center; gap: 0.7rem;
}
.sec::after { content: ''; flex: 1; height: 1px; background: #ffffff0c; }

/* ── Chart card wrappers ── */
.chart-card {
    background: #161b2e;
    border: 1px solid #ffffff14;
    border-radius: 12px;
    padding: 1rem 1rem 0.5rem;
    margin-bottom: 0.5rem;
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stPlotlyChart"] > div { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    for p in [
        "backend/consumer_complaints_clean_5000.csv",
        "consumer_complaints_clean_5000.csv",
        "../backend/consumer_complaints_clean_5000.csv",
    ]:
        if os.path.exists(p):
            try:
                df = pd.read_csv(p)
                df["Date received"]        = pd.to_datetime(df["Date received"],        errors="coerce")
                df["Date sent to company"] = pd.to_datetime(df["Date sent to company"], errors="coerce")
                df["Days to respond"]      = (df["Date sent to company"] - df["Date received"]).dt.days
                df["Narrative_Word_Count"] = df["Consumer complaint narrative"].str.split().str.len()
                return df
            except Exception:
                continue
    return pd.DataFrame()

df = load_data()

# ── Chart theme ───────────────────────────────────────────────────────────────
# Cards are #161b2e — charts must match that, not the page bg
CARD   = "#161b2e"
GRID   = "rgba(255,255,255,0.05)"
TMUT   = "rgba(255,255,255,0.27)"
TMAIN  = "rgba(255,255,255,0.80)"
PAL    = ["#6c9fff","#a78bfa","#34d399","#fbbf24","#f87171","#22d3ee","#fb923c","#86efac"]

BASE = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(family="Inter", color=TMUT, size=12),
    margin=dict(l=4, r=4, t=40, b=4),
    title=dict(font=dict(color=TMAIN, size=13, family="Inter"), x=0.01, y=0.97),
    xaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(size=11, color=TMUT)),
    yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(size=11, color=TMUT)),
    coloraxis_showscale=False,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TMUT, size=11)),
)

def S(fig, title="", **kw):
    fig.update_layout(**BASE, title_text=title, **kw)
    return fig

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <div class="hdr-eye">Consumer Complaints · EDA Dashboard</div>
  <h1>Complaint Intelligence Platform</h1>
  <p>Exploratory analysis across 5,000 consumer complaints · 10 columns</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.error("Dataset not found — check file path.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total      = len(df)
companies  = df["Company"].nunique()
timely_pct = (df["Timely response?"] == "Yes").mean() * 100
closed_pct = df["Company response to consumer"].str.startswith("Closed").mean() * 100
KPI = [
    ("#6c9fff", f"{total:,}",         "Total complaints"),
    ("#34d399", f"{companies:,}",     "Companies involved"),
    ("#a78bfa", f"{timely_pct:.0f}%", "Timely response rate"),
    ("#fbbf24", f"{closed_pct:.0f}%", "Cases closed"),
]

cols = st.columns(4, gap="small")
for col, (color, val, lbl) in zip(cols, KPI):
    col.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi-stripe" style="background:{color}"></div>
      <div class="kpi-v" style="color:{color}">{val}</div>
      <div class="kpi-l">{lbl}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 · Company & Issue
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Company &amp; issue breakdown</div>', unsafe_allow_html=True)
c1, c2 = st.columns([3, 2], gap="medium")

with c1:
    top = df["Company"].value_counts().head(10).reset_index()
    top.columns = ["Company", "Complaints"]
    top = top.sort_values("Complaints")
    fig = px.bar(top, x="Complaints", y="Company", orientation="h",
                 color="Complaints",
                 color_continuous_scale=[[0,"#1a2a50"],[1,"#6c9fff"]])
    fig.update_traces(marker_line_width=0)
    S(fig, "Top 10 companies by complaint volume")
    fig.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    iss = df["Issue"].value_counts().head(8).reset_index()
    iss.columns = ["Issue", "Count"]
    iss["Label"] = iss["Issue"].apply(lambda x: x[:30]+"…" if len(x)>30 else x)
    fig2 = px.pie(iss, names="Label", values="Count", hole=0.6,
                  color_discrete_sequence=PAL)
    fig2.update_traces(textinfo="percent", textfont_size=11,
                       marker_line=dict(color=CARD, width=2))
    S(fig2, "Issue distribution (top 8)")
    fig2.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.05,
                    xanchor="center", x=0.5,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)", itemwidth=30),
        margin=dict(l=4, r=4, t=40, b=110), height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 · Product & Response
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Product &amp; response analysis</div>', unsafe_allow_html=True)
c3, c4 = st.columns([2, 3], gap="medium")

with c3:
    resp = df["Company response to consumer"].value_counts().reset_index()
    resp.columns = ["Response", "Count"]
    resp["Response"] = resp["Response"].apply(lambda x: x[:28]+"…" if len(x)>28 else x)
    fig3 = px.bar(resp, x="Count", y="Response", orientation="h",
                  color_discrete_sequence=["#a78bfa"])
    fig3.update_traces(marker_line_width=0)
    S(fig3, "Company response types")
    fig3.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    prod = df["Product"].value_counts().reset_index()
    prod.columns = ["Product", "Count"]
    prod = prod.sort_values("Count")
    fig4 = px.bar(prod, x="Count", y="Product", orientation="h",
                  color="Count",
                  color_continuous_scale=[[0,"#0d2b20"],[1,"#34d399"]])
    fig4.update_traces(marker_line_width=0)
    S(fig4, "Complaints by product category")
    fig4.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 · Submission channel & Response speed
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Submission channel &amp; response speed</div>', unsafe_allow_html=True)
c5, c6 = st.columns([1, 2], gap="medium")

with c5:
    via = df["Submitted via"].value_counts().reset_index()
    via.columns = ["Channel", "Count"]
    fig5 = px.bar(via, x="Count", y="Channel", orientation="h",
                  color="Count",
                  color_continuous_scale=[[0,"#2a1f0a"],[1,"#fbbf24"]])
    fig5.update_traces(marker_line_width=0)
    S(fig5, "Complaints by submission channel")
    fig5.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    dd = df["Days to respond"].dropna()
    dd = dd[dd >= 0]
    fig6 = px.histogram(dd, nbins=40, color_discrete_sequence=["#fbbf24"])
    med = int(dd.median())
    fig6.add_vline(x=med, line_dash="dash", line_color="#6c9fff", line_width=1.5,
                   annotation_text=f"Median: {med}d",
                   annotation_font_color="#6c9fff", annotation_font_size=11)
    fig6.update_traces(marker_line_width=0)
    S(fig6, "Days from complaint received → sent to company")
    fig6.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
    st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 · Timeliness
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Timeliness by response type &amp; product</div>', unsafe_allow_html=True)
c7, c8 = st.columns([3, 2], gap="medium")

with c7:
    grp = (df.groupby(["Company response to consumer","Timely response?"])
             .size().reset_index(name="Count"))
    grp["Response"] = grp["Company response to consumer"].apply(
        lambda x: x[:26]+"…" if len(x)>26 else x)
    fig7 = px.bar(grp, x="Count", y="Response", color="Timely response?",
                  orientation="h", barmode="stack",
                  color_discrete_map={"Yes":"#34d399","No":"#f87171"})
    fig7.update_traces(marker_line_width=0)
    S(fig7, "Timely vs late responses by resolution type")
    fig7.update_layout(yaxis_title=None, xaxis_title=None, legend_title_text="Timely?")
    st.plotly_chart(fig7, use_container_width=True)

with c8:
    tp = (df.groupby("Product")["Timely response?"]
            .apply(lambda x: (x=="Yes").mean()*100)
            .reset_index(name="Timely %"))
    tp = tp.sort_values("Timely %")
    tp["Product"] = tp["Product"].apply(lambda x: x[:24]+"…" if len(x)>24 else x)
    fig8 = px.bar(tp, x="Timely %", y="Product", orientation="h",
                  color="Timely %",
                  color_continuous_scale=[[0,"#2a1515"],[0.5,"#a78bfa"],[1,"#34d399"]])
    fig8.update_traces(marker_line_width=0)
    S(fig8, "Timely response rate by product (%)")
    fig8.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig8, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 · Daily trend (full width)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Complaint volume over time</div>', unsafe_allow_html=True)
daily = df.groupby("Date received").size().reset_index(name="Complaints")
fig9 = px.line(daily, x="Date received", y="Complaints",
               color_discrete_sequence=["#34d399"])
fig9.update_traces(line_width=2, fill="tozeroy", fillcolor="rgba(52,211,153,0.08)")
S(fig9, "Daily incoming complaints")
fig9.update_layout(xaxis_title=None, yaxis_title=None,
                   hovermode="x unified", height=240)
st.plotly_chart(fig9, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 · Operational bottlenecks heatmap
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Operational bottlenecks</div>', unsafe_allow_html=True)
top5c = df["Company"].value_counts().head(5).index
top5p = df["Product"].value_counts().head(5).index
sub   = df[df["Company"].isin(top5c) & df["Product"].isin(top5p)]
heat  = pd.crosstab(sub["Company"], sub["Product"])
heat.index   = [r[:24]+"…" if len(r)>24 else r for r in heat.index]
heat.columns = [c[:18]+"…" if len(c)>18 else c for c in heat.columns]
fig11 = px.imshow(heat,
                  color_continuous_scale=[[0,"#0d1f18"],[0.5,"#0e5c40"],[1,"#34d399"]],
                  text_auto=True, aspect="auto")
fig11.update_traces(textfont=dict(size=12, color="#ffffff"))
S(fig11, "Top 5 companies × top 5 products — complaint count")
fig11.update_layout(
    xaxis_title=None, yaxis_title=None,
    coloraxis_showscale=False,
    xaxis=dict(tickangle=-30, tickfont=dict(size=10, color=TMUT)),
    yaxis=dict(tickfont=dict(size=10, color=TMUT)),
    height=340,
)
st.plotly_chart(fig11, use_container_width=True)

