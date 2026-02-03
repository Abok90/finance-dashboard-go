import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ================== CONFIG ==================
SHEET_ID = "1FP43Qlbqznlg57YpYwHECtwKf3i3Y9b6qHpjQ5WJXbQ"
GID_EXPENSES = "0"
GID_INCOME = "1950785482"

st.set_page_config(
    page_title="AIDA Finance",
    page_icon="💰",
    layout="centered"
)

# ================== CSS ==================
st.markdown("""
<style>
body { background-color: #0e1117; }

.card {
    background: #1c1f26;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    direction: rtl;
    text-align: right;
}

.card-title {
    font-size: 0.95rem;
    color: #9aa4b2;
    margin-bottom: 6px;
}

.card-value {
    font-size: 2.1rem;
    font-weight: 800;
    color: #ffffff;
}

.section-title {
    color: #ffffff;
    font-size: 1.2rem;
    margin: 22px 0 10px;
    font-weight: bold;
}

.stDataFrame {
    direction: rtl;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ================== HELPERS ==================
def clean_currency(val):
    if isinstance(val, str):
        for c in ["EGP", "ج.م", ",", "٬"]:
            val = val.replace(c, "")
        val = val.replace("٫", ".").strip()
        try:
            return float(val)
        except:
            return 0.0
    return val

@st.cache_data(ttl=300)
def load_data():
    exp = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}")
    inc = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}")

    def find_amount(df):
        for c in df.columns:
            if any(x in str(c).lower() for x in ["amount", "المبلغ", "egp", "ج"]):
                return c
        return None

    def find_date(df):
        for c in df.columns:
            if "date" in str(c).lower() or "تاريخ" in str(c):
                return c
        return None

    exp["المبلغ"] = exp[find_amount(exp)].apply(clean_currency)
    inc["المبلغ"] = inc[find_amount(inc)].apply(clean_currency)

    exp["التاريخ"] = pd.to_datetime(exp[find_date(exp)], errors="coerce")
    inc["التاريخ"] = pd.to_datetime(inc[find_date(inc)], errors="coerce")

    exp.dropna(subset=["التاريخ"], inplace=True)
    inc.dropna(subset=["التاريخ"], inplace=True)

    for df in (exp, inc):
        df["السنة"] = df["التاريخ"].dt.year
        df["الشهر"] = df["التاريخ"].dt.month
        df["اليوم"] = df["التاريخ"].dt.day

    return exp, inc

# ================== LOAD ==================
df_exp, df_inc = load_data()

# ================== FILTERS ==================
today = datetime.today()

years_available = sorted(set(df_exp["السنة"]) | set(df_inc["السنة"]))
default_year = max(years_available) if years_available else today.year

st.markdown("<div class='section-title'>🔍 التصفية</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    year = st.selectbox(
        "السنة",
        years_available,
        index=years_available.index(default_year)
    )
with c2:
    month = st.selectbox(
        "الشهر",
        list(range(1, 13)),
        index=today.month - 1
    )
with c3:
    day = st.selectbox("اليوم", ["الكل"] + list(range(1, 32)))

exp_f = df_exp[(df_exp["السنة"] == year) & (df_exp["الشهر"] == month)]
inc_f = df_inc[(df_inc["السنة"] == year) & (df_inc["الشهر"] == month)]

if day != "الكل":
    exp_f = exp_f[exp_f["اليوم"] == day]
    inc_f = inc_f[inc_f["اليوم"] == day]

# ================== SUMMARY ==================
st.markdown("<div class='section-title'>📊 ملخص سريع</div>", unsafe_allow_html=True)

total_inc = inc_f["المبلغ"].sum()
total_exp = exp_f["المبلغ"].sum()
net = total_inc - total_exp

st.markdown(f"""
<div class="card">
  <div class="card-title">إجمالي التحصيلات</div>
  <div class="card-value">{total_inc:,.0f} ج.م</div>
</div>

<div class="card">
  <div class="card-title">إجمالي المصروفات</div>
  <div class="card-value">{total_exp:,.0f} ج.م</div>
</div>

<div class="card">
  <div class="card-title">صافي الربح</div>
  <div class="card-value">{net:,.0f} ج.م</div>
</div>
""", unsafe_allow_html=True)

# ================== CHARTS ==================
st.markdown("<div class='section-title'>📉 تفاصيل المصروفات</div>", unsafe_allow_html=True)

if not exp_f.empty:
    g = exp_f.groupby(exp_f.columns[0])["المبلغ"].sum().reset_index()
    fig = px.bar(
        g,
        x="المبلغ",
        y=g.columns[0],
        orientation="h",
        height=420,
        text_auto=".2s",
        color_discrete_sequence=["#4fc3f7"]
    )
    fig.update_layout(
        xaxis_title="القيمة (ج.م)",
        yaxis_title="",
        font=dict(size=14, color="white"),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117"
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='section-title'>📈 تفاصيل التحصيلات</div>", unsafe_allow_html=True)

if not inc_f.empty:
    g = inc_f.groupby(inc_f.columns[0])["المبلغ"].sum().reset_index()
    fig = px.bar(
        g,
        x="المبلغ",
        y=g.columns[0],
        orientation="h",
        height=420,
        text_auto=".2s",
        color_discrete_sequence=["#00e676"]
    )
    fig.update_layout(
        xaxis_title="القيمة (ج.م)",
        yaxis_title="",
        font=dict(size=14, color="white"),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================== TABLES ==================
with st.expander("📄 تفاصيل المصروفات (جدول)"):
    st.dataframe(exp_f, use_container_width=True)

with st.expander("📄 تفاصيل التحصيلات (جدول)"):
    st.dataframe(inc_f, use_container_width=True)
