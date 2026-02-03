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
    div[data-testid="stAlert"] { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# دالة تنظيف العملة
def clean_currency(val):
    if isinstance(val, str):
        val = val.replace('EGP', '').strip()
        val = val.replace('ج.م', '').strip()
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
    except Exception as e:
        st.error(f"⚠️ فشل تحميل البيانات: {e}")
        st.stop()

    # --- معالجة المصاريف ---
    col_money_exp = None
    for col in df_exp.columns:
        if "المبلغ" in str(col) or "amount" in str(col).lower():
            col_money_exp = col
            break
    if not col_money_exp: col_money_exp = df_exp.columns[4]

    df_exp[col_money_exp] = df_exp[col_money_exp].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce')
    df_exp = df_exp.dropna(subset=['التاريخ'])
    
    df_exp['السنة'] = df_exp['التاريخ'].dt.year
    df_exp['الشهر'] = df_exp['التاريخ'].dt.month
    df_exp['اليوم'] = df_exp['التاريخ'].dt.day
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    
    df_exp = df_exp.rename(columns={col_money_exp: 'المبلغ (جم)'})

    # --- معالجة الدخل ---
    col_money_inc = None
    for col in df_inc.columns:
        if "المبلغ" in str(col) or "amount" in str(col).lower():
            col_money_inc = col
            break
    if not col_money_inc: col_money_inc = df_inc.columns[3]

    df_inc[col_money_inc] = df_inc[col_money_inc].apply(clean_currency)
    df_inc['التاريخ'] = pd.to_datetime(df_inc['التاريخ'], errors='coerce')
    df_inc = df_inc.dropna(subset=['التاريخ'])
    
    df_inc['السنة'] = df_inc['التاريخ'].dt.year
    df_inc['الشهر'] = df_inc['التاريخ'].dt.month
    df_inc['اليوم'] = df_inc['التاريخ'].dt.day
    df_inc['الشهر_سنة'] = df_inc['التاريخ'].dt.strftime('%Y-%m')
    
    df_inc = df_inc.rename(columns={col_money_inc: 'المبلغ المحصل (جم)'})

    return df_exp, df_inc

# تنفيذ التحميل
df_exp, df_inc = load_data()

# --- الفلاتر ---
st.sidebar.header("🔍 خيارات التصفية")

# السنة
current_year = datetime.now().year
years_list = sorted(list(set(df_exp['السنة'].unique()) | set(df_inc['السنة'].unique())), reverse=True)
if current_year not in years_list: years_list.insert(0, current_year)
selected_year = st.sidebar.selectbox("السنة", years_list)

# الشهر
current_month = datetime.now().month
months_map = {1:'يناير', 2:'فبراير', 3:'مارس', 4:'أبريل', 5:'مايو', 6:'يونيو', 
              7:'يوليو', 8:'أغسطس', 9:'سبتمبر', 10:'أكتوبر', 11:'نوفمبر', 12:'ديسمبر'}
selected_month_num = st.sidebar.selectbox("الشهر", list(months_map.keys()), format_func=lambda x: months_map[x], index=current_month-1)

# اليوم
days_exp = df_exp[(df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month_num)]['اليوم']
days_inc = df_inc[(df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month_num)]['اليوم']
available_days = sorted(list(set(days_exp) | set(days_inc)))

selected_day = st.sidebar.selectbox("اليوم (اختياري)", ["الكل"] + available_days)

# تطبيق الفلتر
if selected_day == "الكل":
    mask_exp = (df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month_num)
    mask_inc = (df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month_num)
    title_suffix = f"{months_map[selected_month_num]} {selected_year}"
else:
    mask_exp = (df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month_num) & (df_exp['اليوم'] == selected_day)
    mask_inc = (df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month_num) & (df_inc['اليوم'] == selected_day)
    title_suffix = f"{selected_day} {months_map[selected_month_num]} {selected_year}"

df_exp_filtered = df_exp.loc[mask_exp]
df_inc_filtered = df_inc.loc[mask_inc]

# --- الواجهة الرئيسية ---
st.title(f"📊 التقرير المالي: {title_suffix}")

if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()

# 1. KPIs
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("💰 صافي الربح", f"{net_profit:,.0f} ج.م")
col2.metric("💸 المصروفات", f"{total_exp:,.0f} ج.م", delta_color="inverse")
col3.metric("📥 التحصيلات", f"{total_inc:,.0f} ج.م")

st.markdown("---")

# 2. تحليل البنود (مصاريف + تحصيلات)
col_analysis_1, col_analysis_2 = st.columns(2)

# أ) تحليل المصاريف
with col_analysis_1:
    if not df_exp_filtered.empty:
        st.subheader("📋 تفاصيل المصاريف")
        grouped_exp = df_exp_filtered.groupby('البند الرئيسي')['المبلغ (جم)'].sum().reset_index()
        grouped_exp = grouped_exp.sort_values(by='المبلغ (جم)', ascending=False)
        
        st.dataframe(grouped_exp, column_config={"البند الرئيسي": "البند", "المبلغ (جم)": st.column_config.NumberColumn("القيمة", format="%d")}, use_container_width=True, hide_index=True)
        
        try:
            fig_bar_exp = px.bar(grouped_exp, x='المبلغ (جم)', y='البند الرئيسي', orientation='h', text_auto='.2s', title="توزيع المصاريف")
            fig_bar_exp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar_exp, use_container_width=True)
        except: pass
    else:
        st.info("لا توجد مصاريف")

# ب) تحليل التحصيلات (الطلب الجديد)
with col_analysis_2:
    if not df_inc_filtered.empty:
        st.subheader("📋 تفاصيل التحصيلات")
        # التجميع حسب نوع التحصيل
        grouped_inc = df_inc_filtered.groupby('نوع التحصيل')['المبلغ المحصل (جم)'].sum().reset_index()
        grouped_inc = grouped_inc.sort_values(by='المبلغ المحصل (جم)', ascending=False)
        
        st.dataframe(grouped_inc, column_config={"نوع التحصيل": "المصدر", "المبلغ المحصل (جم)": st.column_config.NumberColumn("القيمة", format="%d")}, use_container_width=True, hide_index=True)
        
        try:
            fig_bar_inc = px.bar(grouped_inc, x='المبلغ المحصل (جم)', y='نوع التحصيل', orientation='h', text_auto='.2s', title="توزيع مصادر الدخل", color_discrete_sequence=['#2ecc71'])
            fig_bar_inc.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar_inc, use_container_width=True)
        except: pass
    else:
        st.info("لا توجد تحصيلات")

st.markdown("---")

# 3. الجداول التفصيلية
with st.expander("📄 عرض جدول المصاريف التفصيلي"):
    st.dataframe(df_exp_filtered, use_container_width=True)

with st.expander("📄 عرض جدول التحصيلات التفصيلي"):
    st.dataframe(df_inc_filtered, use_container_width=True)

st.markdown("---")

# 4. ملخص شهري شامل (كل البيانات) - (الطلب الجديد)
st.header("📅 ملخص الأداء الشهري (لكل الفترات)")
st.caption("يعرض هذا الجدول جميع الشهور الموجودة في الملف للمقارنة")

# تجميع كل المصاريف حسب الشهر
all_exp_monthly = df_exp.groupby('الشهر_سنة')['المبلغ (جم)'].sum().reset_index()
all_exp_monthly.rename(columns={'المبلغ (جم)': 'المصاريف'}, inplace=True)

# تجميع كل الدخل حسب الشهر
all_inc_monthly = df_inc.groupby('الشهر_سنة')['المبلغ المحصل (جم)'].sum().reset_index()
all_inc_monthly.rename(columns={'المبلغ المحصل (جم)': 'التحصيلات'}, inplace=True)

# دمج الجدولين
monthly_summary = pd.merge(all_inc_monthly, all_exp_monthly, on='الشهر_سنة', how='outer').fillna(0)
monthly_summary['صافي الربح'] = monthly_summary['التحصيلات'] - monthly_summary['المصاريف']
monthly_summary = monthly_summary.sort_values('الشهر_سنة')

# رسم بياني للمقارنة
melted_summary = monthly_summary.melt(id_vars=['الشهر_سنة'], value_vars=['التحصيلات', 'المصاريف'], var_name='النوع', value_name='المبلغ')

fig_history = px.bar(melted_summary, x='الشهر_سنة', y='المبلغ', color='النوع', 
                     barmode='group', text_auto='.2s',
                     color_discrete_map={'التحصيلات': '#2ecc71', 'المصاريف': '#e74c3c'},
                     title="مقارنة الدخل والمصاريف عبر الشهور")
st.plotly_chart(fig_history, use_container_width=True)

# عرض الجدول الشامل
st.dataframe(
    monthly_summary.style.format("{:,.0f}"),
    use_container_width=True,
    column_config={
        "الشهر_سنة": "الشهر",
        "التحصيلات": st.column_config.NumberColumn("إجمالي التحصيلات", format="%d ج.م"),
        "المصاريف": st.column_config.NumberColumn("إجمالي المصاريف", format="%d ج.م"),
        "صافي الربح": st.column_config.NumberColumn("صافي الربح", format="%d ج.م"),
    }
)
