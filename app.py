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
# 📱 Page Config
# =====================================================
st.set_page_config(
    page_title="AIDA Finance Dashboard",
    page_icon="💰",
    layout="centered"
)

# =====================================================
# 🎨 CSS (Readable on Mobile)
# =====================================================
st.markdown("""
<style>
.main { background-color: #f4f6f9; }

.card {
    background: white;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    text-align: right;
    direction: rtl;
}

.card-title {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-bottom: 6px;
}

.card-value {
    font-size: 1.6rem;
    font-weight: bold;
    color: #2c3e50;
}

h1, h2, h3 {
    text-align: right;
    font-family: 'Tajawal', sans-serif;
}

.stDataFrame {
    direction: rtl;
    font-size: 0.85rem;
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
# 📥 Load Data (SAFE)
# =====================================================
@st.cache_data(ttl=300)
def load_data():
    exp_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    inc_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    df_exp = pd.read_csv(exp_url)
    df_inc = pd.read_csv(inc_url)

    def detect_amount(df):
        for col in df.columns:
            c = str(col).lower()
            if any(k in c for k in ["المبلغ", "amount", "egp", "ج"]):
                return col
        return None

    exp_amount = detect_amount(df_exp)
    inc_amount = detect_amount(df_inc)

    df_exp[exp_amount] = df_exp[exp_amount].apply(clean_currency)
    df_inc[inc_amount] = df_inc[inc_amount].apply(clean_currency)

    df_exp.rename(columns={exp_amount: "المبلغ"}, inplace=True)
    df_inc.rename(columns={inc_amount: "المبلغ"}, inplace=True)

    def detect_date(df):
        for col in df.columns:
            if "تاريخ" in str(col) or "date" in str(col).lower():
                return col
        return None

    df_exp["التاريخ"] = pd.to_datetime(df_exp[detect_date(df_exp)], errors="coerce")
    df_inc["التاريخ"] = pd.to_datetime(df_inc[detect_date(df_inc)], errors="coerce")

    df_exp.dropna(subset=["التاريخ"], inplace=True)
    df_inc.dropna(subset=["التاريخ"], inplace=True)

    for df in (df_exp, df_inc):
        df["السنة"] = df["التاريخ"].dt.year
        df["الشهر"] = df["التاريخ"].dt.month
        df["اليوم"] = df["التاريخ"].dt.day

    return df_exp, df_inc

# =====================================================
# ▶️ RUN
# =====================================================
df_exp, df_inc = load_data()

# =====================================================
# 🔍 Filters (Default = Current Month)
# =====================================================
today = datetime.today()

years = sorted(set(df_exp["السنة"]) | set(df_inc["السنة"]))
months = {
    1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
    7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
}

st.markdown("### 🔍 التصفية")

c1, c2, c3 = st.columns(3)
with c1:
    year = st.selectbox("السنة", years, index=years.index(today.year))
with c2:
    month = st.selectbox(
        "الشهر",
        list(months.keys()),
        format_func=lambda x: months[x],
        index=today.month - 1
    )
with c3:
    day = st.selectbox("اليوم", ["الكل"] + list(range(1, 32)))

exp_f = df_exp[(df_exp["السنة"] == year) & (df_exp["الشهر"] == month)]
inc_f = df_inc[(df_inc["السنة"] == year) & (df_inc["الشهر"] == month)]

if day != "الكل":
    exp_f = exp_f[exp_f["اليوم"] == day]
    inc_f = inc_f[inc_f["اليوم"] == day]

# =====================================================
# 📊 Quick Summary (CLEAR)
# =====================================================
st.markdown("## 📊 الملخص السريع")

total_exp = exp_f["المبلغ"].sum()
total_inc = inc_f["المبلغ"].sum()
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

# =====================================================
# 📉 Charts (واضحة ومفهومة)
# =====================================================
st.markdown("## 📉 التحليل المالي")

if not exp_f.empty:
    st.subheader("🔻 توزيع المصروفات حسب البند")
    exp_grp = exp_f.groupby(exp_f.columns[0])["المبلغ"].sum().reset_index()
    fig1 = px.bar(
        exp_grp,
        x="المبلغ",
        y=exp_grp.columns[0],
        orientation="h",
        height=350
    )
    st.plotly_chart(fig1, use_container_width=True)

if not inc_f.empty:
    st.subheader("🟢 توزيع التحصيلات حسب المصدر")
    inc_grp = inc_f.groupby(inc_f.columns[0])["المبلغ"].sum().reset_index()
    fig2 = px.bar(
        inc_grp,
        x="المبلغ",
        y=inc_grp.columns[0],
        orientation="h",
        color_discrete_sequence=["#2ecc71"],
        height=350
    )
    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# 📄 Tables
# =====================================================
with st.expander("📄 تفاصيل المصروفات"):
    st.dataframe(exp_f, use_container_width=True)

with st.expander("📄 تفاصيل التحصيلات"):
    st.dataframe(inc_f, use_container_width=True)

# =====================================================
# 🔄 Refresh
# =====================================================
if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
