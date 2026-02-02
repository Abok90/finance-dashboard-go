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
        # إزالة الرموز والمسافات
        val = val.replace('EGP', '').strip()
        val = val.replace('ج.م', '').strip()
        val = val.replace('٬', '') # فاصلة الألوف العربية
        val = val.replace('٫', '.') # العلامة العشرية العربية
        val = val.replace(',', '') # فاصلة الألوف الإنجليزية
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
        st.error(f"⚠️ فشل تحميل البيانات من جوجل شيت. السبب: {e}")
        st.stop()

    # --- معالجة المصاريف ---
    # البحث عن عمود المبلغ بمرونة
    col_money_exp = None
    for col in df_exp.columns:
        if "المبلغ" in str(col) or "amount" in str(col).lower():
            col_money_exp = col
            break
    if not col_money_exp: col_money_exp = df_exp.columns[4] # افتراضي لو ملقاش الاسم

    df_exp[col_money_exp] = df_exp[col_money_exp].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce')
    df_exp = df_exp.dropna(subset=['التاريخ'])
    
    # استخراج التقسيمات الزمنية
    df_exp['السنة'] = df_exp['التاريخ'].dt.year
    df_exp['الشهر'] = df_exp['التاريخ'].dt.month
    df_exp['اليوم'] = df_exp['التاريخ'].dt.day
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    
    # توحيد اسم عمود المبلغ
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

# --- الفلاتر (Dropdowns) ---
st.sidebar.header("🔍 خيارات التصفية")

# 1. السنة (تلقائي: السنة الحالية)
current_year = datetime.now().year
years_list = sorted(list(set(df_exp['السنة'].unique()) | set(df_inc['السنة'].unique())), reverse=True)
if current_year not in years_list: years_list.insert(0, current_year)
selected_year = st.sidebar.selectbox("السنة", years_list)

# 2. الشهر (تلقائي: الشهر الحالي)
current_month = datetime.now().month
months_map = {1:'يناير', 2:'فبراير', 3:'مارس', 4:'أبريل', 5:'مايو', 6:'يونيو', 
              7:'يوليو', 8:'أغسطس', 9:'سبتمبر', 10:'أكتوبر', 11:'نوفمبر', 12:'ديسمبر'}
selected_month_num = st.sidebar.selectbox("الشهر", list(months_map.keys()), format_func=lambda x: months_map[x], index=current_month-1)

# 3. اليوم (اختياري)
# فلتر ذكي: يظهر فقط الأيام الموجودة في الشهر والسنة المحددين
days_exp = df_exp[(df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month_num)]['اليوم']
days_inc = df_inc[(df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month_num)]['اليوم']
available_days = sorted(list(set(days_exp) | set(days_inc)))

selected_day = st.sidebar.selectbox("اليوم (اختياري)", ["الكل"] + available_days)

# --- تطبيق الفلاتر ---
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

# زر التحديث
if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()

# 1. بطاقات الأرقام (KPIs)
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("💰 صافي الربح", f"{net_profit:,.0f} ج.م")
col2.metric("💸 المصروفات", f"{total_exp:,.0f} ج.م", delta_color="inverse")
col3.metric("📥 التحصيلات", f"{total_inc:,.0f} ج.م")

st.markdown("---")

# 2. تحليل البنود الرئيسية (الطلب الجديد)
if not df_exp_filtered.empty:
    st.subheader("📋 تفاصيل المصاريف (حسب البند)")
    
    # تجميع حسب البند الرئيسي
    grouped = df_exp_filtered.groupby('البند الرئيسي')['المبلغ (جم)'].sum().reset_index()
    grouped = grouped.sort_values(by='المبلغ (جم)', ascending=False)
    
    c_table, c_chart = st.columns([1, 1])
    
    with c_table:
        st.dataframe(
            grouped,
            column_config={
                "البند الرئيسي": "البند",
                "المبلغ (جم)": st.column_config.NumberColumn("القيمة", format="%d ج.م")
            },
            use_container_width=True,
            hide_index=True
        )
    
    with c_chart:
        try:
            fig_bar = px.bar(grouped, x='المبلغ (جم)', y='البند الرئيسي', orientation='h', text_auto='.2s')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.warning(f"تعذر رسم المخطط: {e}")

else:
    st.info(f"لا توجد مصاريف مسجلة في {title_suffix}")

st.markdown("---")

# 3. الرسوم البيانية الدائرية
col_pie1, col_pie2 = st.columns(2)

with col_pie1:
    if not df_exp_filtered.empty:
        st.caption("توزيع المصاريف (%)")
        try:
            fig_p1 = px.pie(df_exp_filtered, values='المبلغ (جم)', names='البند الرئيسي', hole=0.5)
            fig_p1.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_p1, use_container_width=True)
        except: pass

with col_pie2:
    if not df_inc_filtered.empty:
        st.caption("مصادر الدخل (%)")
        try:
            fig_p2 = px.pie(df_inc_filtered, values='المبلغ المحصل (جم)', names='نوع التحصيل', hole=0.5)
            fig_p2.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_p2, use_container_width=True)
        except: pass

# 4. الجداول التفصيلية (داخل قوائم منسدلة)
with st.expander("📄 عرض جدول المصاريف التفصيلي"):
    st.dataframe(df_exp_filtered, use_container_width=True)

with st.expander("📄 عرض جدول التحصيلات التفصيلي"):
    st.dataframe(df_inc_filtered, use_container_width=True)
