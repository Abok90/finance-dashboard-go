import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =====================================================
# 🔗 Google Sheets Config
# =====================================================
SHEET_ID = "1FP43Qlbqznlg57YpYwHECtwKf3i3Y9b6qHpjQ5WJXbQ"
GID_EXPENSES = "0"
GID_INCOME = "1950785482"

# =====================================================
# 📱 Page Config (Mobile First)
# =====================================================
st.set_page_config(
    page_title="AIDA Finance",
    page_icon="💰",
    layout="centered"
)

# =====================================================
# 🎨 CSS (Mobile Friendly)
# =====================================================
st.markdown("""
<style>
.main { background-color: #f4f6f9; }
h1, h2, h3 { text-align: right; font-family: 'Tajawal', sans-serif; }

.stMetric {
    background: #ffffff;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    text-align: right;
    direction: rtl;
}

.stDataFrame { direction: rtl; font-size: 0.85rem; }

@media (max-width: 768px) {
    h1 { font-size: 1.6rem; }
    h2 { font-size: 1.2rem; }
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 🧹 Currency Cleaner
# =====================================================
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

# =====================================================
# 📥 Load Data
# =====================================================
@st.cache_data(ttl=300)
def load_data():
    exp_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    inc_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    df_exp = pd.read_csv(exp_url)
    df_inc = pd.read_csv(inc_url)

    df_exp["المبلغ"] = df_exp["المبلغ"].apply(clean_currency)
    df_inc["المبلغ"] = df_inc["المبلغ"].apply(clean_currency)

    df_exp["التاريخ"] = pd.to_datetime(df_exp["التاريخ"])
    df_inc["التاريخ"] = pd.to_datetime(df_inc["التاريخ"])

    for df in [df_exp, df_inc]:
        df["السنة"] = df["التاريخ"].dt.year
        df["الشهر"] = df["التاريخ"].dt.month
        df["اليوم"] = df["التاريخ"].dt.day
        df["شهر"] = df["التاريخ"].dt.strftime("%Y-%m")

    return df_exp, df_inc

df_exp, df_inc = load_data()

# =====================================================
# 🔍 Filters (Top – Mobile UX)
# =====================================================
st.markdown("### 🔍 التصفية")

years = sorted(set(df_exp["السنة"]) | set(df_inc["السنة"]), reverse=True)
months = {
    1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
    7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
}

c1, c2, c3 = st.columns(3)
with c1:
    year = st.selectbox("السنة", years)
with c2:
    month = st.selectbox("الشهر", months.keys(), format_func=lambda x: months[x])
with c3:
    day = st.selectbox("اليوم", ["الكل"] + list(range(1,32)))

# =====================================================
# 🎯 Apply Filters
# =====================================================
exp_f = df_exp[(df_exp["السنة"]==year) & (df_exp["الشهر"]==month)]
inc_f = df_inc[(df_inc["السنة"]==year) & (df_inc["الشهر"]==month)]

if day != "الكل":
    exp_f = exp_f[exp_f["اليوم"]==day]
    inc_f = inc_f[inc_f["اليوم"]==day]

# =====================================================
# 📊 KPIs (Mobile Stack)
# =====================================================
st.markdown("## 📊 ملخص سريع")

total_exp = exp_f["المبلغ"].sum()
total_inc = inc_f["المبلغ"].sum()
net = total_inc - total_exp

st.metric("📥 التحصيلات", f"{total_inc:,.0f} ج.م")
st.metric("💸 المصروفات", f"{total_exp:,.0f} ج.م")
st.metric("💰 صافي الربح", f"{net:,.0f} ج.م")

# =====================================================
# 📉 Charts
# =====================================================
st.markdown("## 📉 التحليل")

if not exp_f.empty:
    exp_grp = exp_f.groupby("البند")["المبلغ"].sum().reset_index()
    fig1 = px.bar(
        exp_grp,
        x="المبلغ",
        y="البند",
        orientation="h",
        height=350,
        title="توزيع المصاريف"
    )
    fig1.update_layout(title=None)
    st.plotly_chart(fig1, use_container_width=True)

if not inc_f.empty:
    inc_grp = inc_f.groupby("النوع")["المبلغ"].sum().reset_index()
    fig2 = px.bar(
        inc_grp,
        x="المبلغ",
        y="النوع",
        orientation="h",
        height=350,
        title="مصادر الدخل",
        color_discrete_sequence=["#2ecc71"]
    )
    fig2.update_layout(title=None)
    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# 📄 Details (Advanced Mode)
# =====================================================
with st.expander("📄 تفاصيل المصاريف"):
    st.dataframe(exp_f, use_container_width=True)

with st.expander("📄 تفاصيل التحصيلات"):
    st.dataframe(inc_f, use_container_width=True)

# =====================================================
# 🔄 Refresh
# =====================================================
if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.experimental_rerun()
