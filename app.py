import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------
# ⚙️ إعدادات الربط بجوجل شيت
# ---------------------------------------------------------
SHEET_ID = "1FP43Qlbqznlg57YpYwHECtwKf3i3Y9b6qHpjQ5WJXbQ"
GID_EXPENSES = "0"
GID_INCOME = "1950785482"
# ---------------------------------------------------------

st.set_page_config(
    page_title="داشبورد عايدة",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيق CSS
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3, h4 { font-family: 'Tajawal', sans-serif; text-align: right; color: #2c3e50; }
    div[data-testid="stMetricLabel"] { text-align: right; direction: rtl; font-weight: bold; font-size: 1.1rem;}
    div[data-testid="stMetricValue"] { text-align: right; direction: rtl; }
    .stDataFrame { direction: rtl; }
    div[data-testid="stSelectbox"] label { text-align: right; direction: rtl; font-weight: bold;}
    /* تحسين شكل الجدول التجميعي */
    .dataframe { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# دالة تنظيف العملة
def clean_currency(val):
    if isinstance(val, str):
        val = val.replace('EGP', '').strip()
        val = val.replace('٬', '') 
        val = val.replace('٫', '.')
        val = val.replace(',', '') 
        try:
            return float(val)
        except:
            return 0.0
    return val

# تحميل البيانات
@st.cache_data(ttl=300)
def load_data():
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    try:
        df_exp = pd.read_csv(url_exp)
        df_inc = pd.read_csv(url_inc)
    except:
        st.error("⚠️ خطأ في الاتصال بجوجل شيت")
        st.stop()

    # معالجة المصاريف
    col_money_exp = 'المبلغ (جم)' if 'المبلغ (جم)' in df_exp.columns else df_exp.columns[4]
    df_exp[col_money_exp] = df_exp[col_money_exp].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce')
    df_exp = df_exp.dropna(subset=['التاريخ'])
    df_exp['السنة'] = df_exp['التاريخ'].dt.year
    df_exp['الشهر'] = df_exp['التاريخ'].dt.month
    df_exp['اليوم'] = df_exp['التاريخ'].dt.day
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    df_exp = df_exp.rename(columns={col_money_exp: 'المبلغ (جم)'})

    # معالجة الدخل
    col_money_inc = 'المبلغ المحصل (جم)' if 'المبلغ المحصل (جم)' in df_inc.columns else df_inc.columns[3]
    df_inc[col_money_inc] = df_inc[col_money_inc].apply(clean_currency)
    df_inc['التاريخ'] = pd.to_datetime(df_inc['التاريخ'], errors='coerce')
    df_inc = df_inc.dropna(subset=['التاريخ'])
    df_inc['السنة'] = df_inc['التاريخ'].dt.year
    df_inc['الشهر'] = df_inc['التاريخ'].dt.month
    df_inc['اليوم'] = df_inc['التاريخ'].dt.day
    df_inc['الشهر_سنة'] = df_inc['التاريخ'].dt.strftime('%Y-%m')
    df_inc = df_inc.rename(columns={col_money_inc: 'المبلغ المحصل (جم)'})

    return df_exp, df_inc

df_exp, df_inc = load_data()

# --- الفلاتر (الجزء الجديد) ---
st.sidebar.header("🔍 خيارات العرض")

# 1. فلتر السنة (تلقائي: السنة الحالية)
current_year = datetime.now().year
available_years = sorted(list(set(df_exp['السنة'].unique()) | set(df_inc['السنة'].unique())), reverse=True)
if current_year not in available_years: available_years.insert(0, current_year)
selected_year = st.sidebar.selectbox("السنة", available_years, index=available_years.index(current_year))

# 2. فلتر الشهر (تلقائي: الشهر الحالي)
current_month = datetime.now().month
months_map = {1:'يناير', 2:'فبراير', 3:'مارس', 4:'أبريل', 5:'مايو', 6:'يونيو', 
              7:'يوليو', 8:'أغسطس', 9:'سبتمبر', 10:'أكتوبر', 11:'نوفمبر', 12:'ديسمبر'}
selected_month = st.sidebar.selectbox("الشهر", list(months_map.keys()), format_func=lambda x: months_map[x], index=current_month-1)

# 3. فلتر اليوم (اختياري: الكل افتراضياً)
# نجمع الأيام المتاحة في الشهر والسنة المحددين
days_in_exp = df_exp[(df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month)]['اليوم'].unique()
days_in_inc = df_inc[(df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month)]['اليوم'].unique()
available_days = sorted(list(set(days_in_exp) | set(days_in_inc)))

selected_day = st.sidebar.selectbox("اليوم (اختياري)", ["الكل"] + available_days)

# --- تطبيق الفلتر ---
if selected_day == "الكل":
    mask_exp = (df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month)
    mask_inc = (df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month)
    period_title = f"{months_map[selected_month]} {selected_year}"
else:
    mask_exp = (df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month) & (df_exp['اليوم'] == selected_day)
    mask_inc = (df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month) & (df_inc['اليوم'] == selected_day)
    period_title = f"{selected_day} {months_map[selected_month]} {selected_year}"

df_exp_filtered = df_exp.loc[mask_exp]
df_inc_filtered = df_inc.loc[mask_inc]

# --- الواجهة الرئيسية ---
st.title(f"📊 التقرير المالي: {period_title}")

if st.button("🔄 تحديث البيانات من جوجل شيت"):
    st.cache_data.clear()
    st.rerun()

# KPIs
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

c1, c2, c3 = st.columns(3)
c1.metric("صافي الربح", f"{net_profit:,.0f} ج.م")
c2.metric("المصروفات", f"{total_exp:,.0f} ج.م", delta_color="inverse")
c3.metric("التحصيلات", f"{total_inc:,.0f} ج.م")

st.markdown("---")

# --- تحليل البنود الرئيسية (الطلب الجديد) ---
if not df_exp_filtered.empty:
    st.subheader("📋 تفاصيل المصاريف حسب البند الرئيسي")
    
    # تجميع البيانات حسب البند الرئيسي
    grouped_expenses = df_exp_filtered.groupby('البند الرئيسي')['المبلغ (جم)'].sum().reset_index()
    # ترتيب من الأكبر للأصغر
    grouped_expenses = grouped_expenses.sort_values(by='المبلغ (جم)', ascending=False)
    
    col_table, col_chart = st.columns([1, 1])
    
    with col_table:
        # عرض كجدول أنيق
        st.dataframe(
            grouped_expenses, 
            column_config={
                "البند الرئيسي": "البند",
                "المبلغ (جم)": st.column_config.NumberColumn("الإجمالي (ج.م)", format="%.0f ج.م")
            },
            use_container_width=True,
            hide_index=True
        )
    
    with col_chart:
        # رسم بياني شريطي لنفس البيانات
        fig_bar = px.bar(grouped_expenses, x='المبلغ (جم)', y='البند الرئيسي', orientation='h', 
                         text_auto='.2s', title="الأكثر استهلاكاً للميزانية")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}) # ترتيب الأعمدة
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("لا توجد مصاريف مسجلة في هذه الفترة.")

st.markdown("---")

# --- الرسوم البيانية الإضافية ---
col_pie1, col_pie2 = st.columns(2)

with col_pie1:
    if not df_exp_filtered.empty:
        st.caption("توزيع المصاريف (نسبة مئوية)")
        fig_pie = px.pie(df_exp_filtered, values='المبلغ (جم)', names='البند الرئيسي', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

with col_pie2:
    if not df_inc_filtered.empty:
        st.caption("مصادر الدخل")
        fig_inc = px.pie(df_inc_filtered, values='المبلغ المحصل (جم)', names='نوع التحصيل', hole=0.4)
        st.plotly_chart(fig_inc, use_container_width=True)

# --- الجداول التفصيلية (كاملة) ---
with st.expander("📄 عرض سجل المصاريف التفصيلي (كل العمليات)"):
    st.dataframe(df_exp_filtered[['التاريخ', 'البند الرئيسي', 'تفاصيل', 'المبلغ (جم)', 'ملاحظات']], use_container_width=True)

with st.expander("📄 عرض سجل التحصيلات التفصيلي"):
    st.dataframe(df_inc_filtered[['التاريخ', 'نوع التحصيل', 'شركة الشحن', 'المبلغ المحصل (جم)']], use_container_width=True)
