import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Page background */
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

/* ── KPI cards ── */
.kpi-wrap {
    background: #161b2e;
    border: 1px solid #ffffff18;
    border-radius: 12px;
    padding: 1.4rem 1rem;
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

/* ── Section labels ── */
.sec {
    font-size: 1rem; 
    font-weight: 600; 
    letter-spacing: 0.12em;
    text-transform: uppercase; 
    color: rgba(255,255,255,0.8) !important; /* Updated for visibility */
    margin: 2.2rem 0 0.9rem;
    display: flex; 
    align-items: center; 
    gap: 0.7rem;
}
.sec::after { 
    content: ''; 
    flex: 1; 
    height: 1px; 
    background: #ffffff0c; 
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stPlotlyChart"] > div { border-radius: 10px; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    for p in [
        "backend/new_clean_dataset.csv",
        "new_clean_dataset.csv",
        "../backend/new_clean_dataset.csv",
    ]:
        if os.path.exists(p):
            try:
                df = pd.read_csv(p)
                df["Date received"] = pd.to_datetime(
                    df["Date received"], errors="coerce"
                )
                df["Date sent to company"] = pd.to_datetime(
                    df["Date sent to company"], errors="coerce"
                )
                df["Days to respond"] = (
                    df["Date sent to company"] - df["Date received"]
                ).dt.days
                df["Narrative_Word_Count"] = (
                    df["Consumer complaint narrative"].str.split().str.len()
                )
                return df
            except Exception:
                continue
    return pd.DataFrame()


df = load_data()


CARD = "#161b2e"
GRID = "rgba(255,255,255,0.05)"
TMUT = "rgba(255,255,255,0.27)"
TMAIN = "rgba(255,255,255,0.80)"
PAL = [
    "#6c9fff",
    "#a78bfa",
    "#34d399",
    "#fbbf24",
    "#f87171",
    "#22d3ee",
    "#fb923c",
    "#86efac",
    "#e879f9",
    "#38bdf8",
]

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
st.markdown(
    """
<div class="hdr">
  <div class="hdr-eye">Consumer Complaints · EDA Dashboard</div>
  <h1>Complaint Intelligence Platform</h1>
  <p>Exploratory analysis across consumer complaints · 18 columns</p>
</div>
""",
    unsafe_allow_html=True,
)

if df.empty:
    st.error("Dataset not found — check file path.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total = len(df)
companies = df["Company"].nunique()
states = df["State"].nunique() if "State" in df.columns else 0
disputed_pct = (
    (df["Consumer disputed?"] == "Yes").mean() * 100
    if "Consumer disputed?" in df.columns
    else 0
)
# timely_pct     = (df["Timely response?"] == "Yes").mean() * 100  if "Timely response?" in df.columns else 0
products = df["Product"].nunique() if "Product" in df.columns else 0

KPI = [
    ("#6c9fff", f"{total:,}", "Total complaints"),
    ("#34d399", f"{companies:,}", "Companies involved"),
    ("#a78bfa", f"{states:,}", "States covered"),
    # ("#fbbf24", f"{timely_pct:.0f}%",    "Timely response rate"),
    ("#f87171", f"{disputed_pct:.1f}%", "Consumer disputed"),
    ("#22d3ee", f"{products:,}", "Product categories"),
]

cols = st.columns(6, gap="small")
for col, (color, val, lbl) in zip(cols, KPI):
    col.markdown(
        f"""
    <div class="kpi-wrap">
      <div class="kpi-stripe" style="background:{color}"></div>
      <div class="kpi-v" style="color:{color}">{val}</div>
      <div class="kpi-l">{lbl}</div>
    </div>""",
        unsafe_allow_html=True,
    )


#  SECTION 1 · Company & Issue
st.markdown(
    '<div class="sec">Company &amp; issue breakdown</div>', unsafe_allow_html=True
)
c1, c2 = st.columns([3, 2], gap="medium")

with c1:
    top = df["Company"].value_counts().head(10).reset_index()
    top.columns = ["Company", "Complaints"]
    top = top.sort_values("Complaints")
    fig = px.bar(
        top,
        x="Complaints",
        y="Company",
        orientation="h",
        color="Complaints",
        # count value added here
        text="Complaints",
        color_continuous_scale=[[0, "#1a2a50"], [1, "#6c9fff"]],
    )
    fig.update_traces(marker_line_width=0, textfont=dict(color="white"))
    S(fig, "Top 10 companies by complaint volume")
    fig.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    iss = df["Issue"].value_counts().head(8).reset_index()
    iss.columns = ["Issue", "Count"]
    iss["Label"] = iss["Issue"].apply(lambda x: x[:30] + "…" if len(x) > 30 else x)
    fig2 = px.pie(
        iss, names="Label", values="Count", hole=0.6, color_discrete_sequence=PAL
    )
    fig2.update_traces(
        textinfo="percent",
        textfont=dict(color="white", size=11),  # Updated this line
        marker_line=dict(color=CARD, width=2),
    )
    S(fig2, "Issue distribution (top 8)")
    fig2.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0)",
            itemwidth=30,
        ),
        margin=dict(l=4, r=4, t=40, b=150),
        height=450,
    )
    st.plotly_chart(fig2, use_container_width=True)


# SECTION 2 · Product & Sub-product
st.markdown(
    '<div class="sec">Product &amp; sub-product analysis</div>', unsafe_allow_html=True
)
c3, c4 = st.columns([2, 3], gap="medium")

with c3:
    prod = df["Product"].value_counts().reset_index()
    prod.columns = ["Product", "Count"]
    prod = prod.sort_values("Count")
    fig3 = px.bar(
        prod,
        x="Count",
        y="Product",
        orientation="h",
        color="Count",
        text="Count",
        color_continuous_scale=[[0, "#0d2b20"], [1, "#34d399"]],
    )
    fig3.update_traces(
        marker_line_width=0,
        # textposition='outside',
        textfont=dict(color="white"),
    )
    S(fig3, "Complaints by product category")
    fig3.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig3, use_container_width=True)


with c4:
    if "Sub-product" in df.columns:
        subprod = df["Sub-product"].replace("", pd.NA).dropna()
        subprod = subprod.value_counts().head(10).reset_index()
        subprod.columns = ["Sub-product", "Count"]
        subprod = subprod.sort_values("Count")
        subprod["Label"] = subprod["Sub-product"].apply(
            lambda x: x[:32] + "…" if len(x) > 32 else x
        )
        fig4 = px.bar(
            subprod,
            x="Count",
            y="Label",
            orientation="h",
            color="Count",
            text="Count",  # Add this
            color_continuous_scale=[[0, "#1a0d2b"], [1, "#a78bfa"]],
        )
        fig4.update_traces(
            marker_line_width=0,
            # textposition='outside',
            textfont=dict(color="white"),
        )
        S(fig4, "Top 10 sub-products")
        fig4.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig4, use_container_width=True)


# ── SECTION 3 · Sub-issue & Company Response ──────────────────────────────────
st.markdown(
    '<div class="sec">Sub-issue &amp; company response</div>', unsafe_allow_html=True
)
c5, c6 = st.columns([3, 2], gap="medium")

with c5:
    if "Sub-issue" in df.columns:
        subiss = df["Sub-issue"].replace("", pd.NA).dropna()
        subiss = subiss.value_counts().head(10).reset_index()
        subiss.columns = ["Sub-issue", "Count"]
        subiss = subiss.sort_values("Count")
        subiss["Label"] = subiss["Sub-issue"].apply(
            lambda x: x[:34] + "…" if len(x) > 34 else x
        )
        fig5 = px.bar(
            subiss,
            x="Count",
            y="Label",
            orientation="h",
            color="Count",
            text="Count",  # Add this
            color_continuous_scale=[[0, "#2a1f0a"], [1, "#fbbf24"]],
        )
        fig5.update_traces(
            marker_line_width=0,
            # textposition='outside',
            textfont=dict(color="white"),
        )
        S(fig5, "Top 10 sub-issues")
        fig5.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig5, use_container_width=True)

with c6:
    resp = df["Company response to consumer"].value_counts().reset_index()
    resp.columns = ["Response", "Count"]
    resp["Response"] = resp["Response"].apply(
        lambda x: x[:28] + "…" if len(x) > 28 else x
    )
    fig6 = px.bar(
        resp,
        x="Count",
        y="Response",
        orientation="h",
        text="Count",  # Add this
        color_discrete_sequence=["#a78bfa"],
    )
    fig6.update_traces(marker_line_width=0, textfont=dict(color="white"))  # Add this
    S(fig6, "Company response types")
    fig6.update_layout(yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig6, use_container_width=True)


# ── SECTION 4 · Geographic (State) ────────────────────────────────────────────
st.markdown(
    '<div class="sec">Geographic distribution by state</div>', unsafe_allow_html=True
)
c7, c8 = st.columns([3, 2], gap="medium")

with c7:
    if "State" in df.columns:
        state_counts = (
            df["State"].replace("", pd.NA).dropna().value_counts().reset_index()
        )
        state_counts.columns = ["State", "Complaints"]
        fig7 = px.choropleth(
            state_counts,
            locations="State",
            locationmode="USA-states",
            color="Complaints",
            scope="usa",
            color_continuous_scale=[[0, "#0d1f18"], [0.5, "#0e5c40"], [1, "#34d399"]],
        )
        fig7.update_layout(
            paper_bgcolor=CARD,
            plot_bgcolor=CARD,
            geo=dict(
                bgcolor=CARD,
                lakecolor=CARD,
                landcolor="#0d1a10",
                showlakes=True,
                showland=True,
                # ← fixed: rgba() instead of 8-digit hex
                coastlinecolor="rgba(255,255,255,0.08)",
                countrycolor="rgba(255,255,255,0.08)",
                subunitcolor="rgba(255,255,255,0.12)",
            ),
            margin=dict(l=0, r=0, t=40, b=0),
            title=dict(
                text="Complaints by  State", font=dict(color=TMAIN, size=13), x=0.01
            ),
            coloraxis_colorbar=dict(tickfont=dict(color=TMUT), title=""),
            height=340,
        )
        st.plotly_chart(fig7, use_container_width=True)

with c8:
    if "State" in df.columns:
        top_states = (
            df["State"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .head(15)
            .reset_index()
        )
        top_states.columns = ["State", "Complaints"]
        top_states = top_states.sort_values("Complaints")

        fig8 = px.bar(
            top_states,
            x="Complaints",
            y="State",
            orientation="h",
            color="Complaints",
            text="Complaints",  # Add this
            color_continuous_scale=[[0, "#0d1a10"], [1, "#34d399"]],
        )

        fig8.update_traces(
            marker_line_width=0, textfont=dict(color="white"), textposition="outside"
        )

        S(fig8, "Top 15 states by complaint volume")
        fig8.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig8, use_container_width=True)


# ── SECTION 7 · Timeliness ────────────────────────────────────────────────────
st.markdown(
    '<div class="sec">Timeliness &amp; dispute analysis</div>', unsafe_allow_html=True
)
c13, c14 = st.columns([3, 2], gap="medium")

with c13:
    grp = (
        df.groupby(["Company response to consumer", "Timely response?"])
        .size()
        .reset_index(name="Count")
    )
    grp["Response"] = grp["Company response to consumer"].apply(
        lambda x: x[:26] + "…" if len(x) > 26 else x
    )
    fig13 = px.bar(
        grp,
        x="Count",
        y="Response",
        color="Timely response?",
        text="Count",  # Add this
        orientation="h",
        barmode="stack",
        color_discrete_map={"Yes": "#34d399", "No": "#f87171"},
    )
    fig13.update_traces(
        marker_line_width=0,
        textposition="outside",  # Positions text inside the segments
        textfont=dict(color="white"),  # Makes text visible against the bar colors
    )
    S(fig13, "Timely vs late responses by resolution type")
    fig13.update_layout(yaxis_title=None, xaxis_title=None, legend_title_text="Timely?")
    st.plotly_chart(fig13, use_container_width=True)

# with c14:
#     if "Consumer disputed?" in df.columns:
#         disp = (
#             df.groupby("Product")["Consumer disputed?"]
#             .apply(lambda x: (x == "Yes").sum() / len(x) * 100)
#             .reset_index(name="Disputed %")
#         )
#         disp = disp.sort_values("Disputed %")
#         disp["Product"] = disp["Product"].apply(
#             lambda x: x[:24] + "…" if len(x) > 24 else x
#         )
#         fig14 = px.bar(
#             disp,
#             x="Disputed %",
#             y="Product",
#             orientation="h",
#             color="Disputed %",
#             color_continuous_scale=[[0, "#2a1515"], [0.5, "#f87171"], [1, "#fbbf24"]],
#         )
#         fig14.update_traces(marker_line_width=0)
#         S(fig14, "Consumer dispute rate by product (%)")
#         fig14.update_layout(yaxis_title=None, xaxis_title=None)
#         st.plotly_chart(fig14, use_container_width=True)


# ── SECTION 8 · Timely response rate by product ────────────────────────────────
# st.markdown('<div class="sec">Timely response rate by product</div>', unsafe_allow_html=True)
# tp = (df.groupby("Product")["Timely response?"]
#         .apply(lambda x: (x=="Yes").mean()*100)
#         .reset_index(name="Timely %"))
# tp = tp.sort_values("Timely %")
# tp["Product"] = tp["Product"].apply(lambda x: x[:24]+"…" if len(x)>24 else x)
# fig15 = px.bar(tp, x="Timely %", y="Product", orientation="h",
#                color="Timely %",
#                color_continuous_scale=[[0,"#2a1515"],[0.5,"#a78bfa"],[1,"#34d399"]])
# fig15.update_traces(marker_line_width=0)
# S(fig15, "Timely response rate by product (%)")
# fig15.update_layout(yaxis_title=None, xaxis_title=None)
# st.plotly_chart(fig15, use_container_width=True)


# ── SECTION 9 · Daily trend ───────────────────────────────────────────────────
st.markdown('<div class="sec">Complaint volume over time</div>', unsafe_allow_html=True)
daily = df.groupby("Date received").size().reset_index(name="Complaints")
fig16 = px.line(
    daily, x="Date received", y="Complaints", color_discrete_sequence=["#34d399"]
)
fig16.update_traces(line_width=2, fill="tozeroy", fillcolor="rgba(52,211,153,0.08)")
S(fig16, "Daily incoming complaints")
fig16.update_layout(
    xaxis_title=None, yaxis_title=None, hovermode="x unified", height=240
)
st.plotly_chart(fig16, use_container_width=True)


# ── SECTION 10 · Operational bottlenecks heatmap ─────────────────────────────
st.markdown('<div class="sec">Operational bottlenecks</div>', unsafe_allow_html=True)
top5c = df["Company"].value_counts().head(5).index
top5p = df["Product"].value_counts().head(5).index
sub = df[df["Company"].isin(top5c) & df["Product"].isin(top5p)]
heat = pd.crosstab(sub["Company"], sub["Product"])
heat.index = [r[:24] + "…" if len(r) > 24 else r for r in heat.index]
heat.columns = [c[:18] + "…" if len(c) > 18 else c for c in heat.columns]
fig17 = px.imshow(
    heat,
    color_continuous_scale=[[0, "#0d1f18"], [0.5, "#0e5c40"], [1, "#34d399"]],
    text_auto=True,
    aspect="auto",
)
fig17.update_traces(textfont=dict(size=12, color="#ffffff"))
S(fig17, "Top 5 companies × top 5 products — complaint count")
fig17.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    coloraxis_showscale=False,
    xaxis=dict(tickangle=-30, tickfont=dict(size=10, color=TMUT)),
    yaxis=dict(tickfont=dict(size=10, color=TMUT)),
    height=340,
)
st.plotly_chart(fig17, use_container_width=True)
