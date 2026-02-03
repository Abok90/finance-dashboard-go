import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =====================================================
# 🔗 Google Sheets Settings
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
# 📥 Load Data (SAFE – no KeyError)
# =====================================================
@st.cache_data(ttl=300)
def load_data():
    exp_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    inc_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    df_exp = pd.read_csv(exp_url)
    df_inc = pd.read_csv(inc_url)

    # -------- detect amount column --------
    def detect_amount_col(df):
        for col in df.columns:
            c = str(col).lower()
            if any(k in c for k in ["المبلغ", "amount", "egp", "ج"]):
                return col
        return None

    exp_amount_col = detect_amount_col(df_exp)
    inc_amount_col = detect_amount_col(df_inc)

    if exp_amount_col is None or inc_amount_col is None:
        st.error("❌ لم يتم العثور على عمود المبلغ في Google Sheet")
        st.write("أعمدة المصاريف:", list(df_exp.columns))
        st.write("أعمدة التحصيلات:", list(df_inc.columns))
        st.stop()

    # -------- clean currency --------
    df_exp[exp_amount_col] = df_exp[exp_amount_col].apply(clean_currency)
    df_inc[inc_amount_col] = df_inc[inc_amount_col].apply(clean_currency)

    # -------- unify column name --------
    df_exp.rename(columns={exp_amount_col: "المبلغ"}, inplace=True)
    df_inc.rename(columns={inc_amount_col: "المبلغ"}, inplace=True)

    # -------- detect date column --------
    def detect_date_col(df):
        for col in df.columns:
            if "تاريخ" in str(col) or "date" in str(col).lower():
                return col
        return None

    exp_date_col = detect_date_col(df_exp)
    inc_date_col = detect_date_col(df_inc)

    if exp_date_col is None or inc_date_col is None:
        st.error("❌ لم يتم العثور على عمود التاريخ")
        st.stop()

    df_exp["التاريخ"] = pd.to_datetime(df_exp[exp_date_col], errors="coerce")
    df_inc["التاريخ"] = pd.to_datetime(df_inc[inc_date_col], errors="coerce")

    df_exp.dropna(subset=["التاريخ"], inplace=True)
    df_inc.dropna(subset=["التاريخ"], inplace=True)

    for df in (df_exp, df_inc):
        df["السنة"] = df["التاريخ"].dt.year
        df["الشهر"] = df["التاريخ"].dt.month
        df["اليوم"] = df["التاريخ"].dt.day
        df["شهر"] = df["التاريخ"].dt.strftime("%Y-%m")

    return df_exp, df_inc

# =====================================================
# ▶️ Run
# =====================================================
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
    day = st.selectbox("اليوم", ["الكل"] + list(range(1, 32)))

# =====================================================
# 🎯 Apply Filters
# =====================================================
exp_f = df_exp[(df_exp["السنة"] == year) & (df_exp["الشهر"] == month)]
inc_f = df_inc[(df_inc["السنة"] == year) & (df_inc["الشهر"] == month)]

if day != "الكل":
    exp_f = exp_f[exp_f["اليوم"] == day]
    inc_f = inc_f[inc_f["اليوم"] == day]

# =====================================================
# 📊 KPIs
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
    exp_grp = exp_f.groupby(exp_f.columns[0])["المبلغ"].sum().reset_index()
    fig1 = px.bar(
        exp_grp,
        x="المبلغ",
        y=exp_grp.columns[0],
        orientation="h",
        height=350
    )
    fig1.update_layout(title=None)
    st.plotly_chart(fig1, use_container_width=True)

if not inc_f.empty:
    inc_grp = inc_f.groupby(inc_f.columns[0])["المبلغ"].sum().reset_index()
    fig2 = px.bar(
        inc_grp,
        x="المبلغ",
        y=inc_grp.columns[0],
        orientation="h",
        height=350,
        color_discrete_sequence=["#2ecc71"]
    )
    fig2.update_layout(title=None)
    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# 📄 Tables
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
    st.rerun()
