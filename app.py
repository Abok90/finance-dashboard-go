import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------
# ⚙️ إعدادات الربط بجوجل شيت (الروابط الخاصة بك)
# ---------------------------------------------------------
SHEET_ID = "1FP43Qlbqznlg57YpYwHECtwKf3i3Y9b6qHpjQ5WJXbQ"
GID_EXPENSES = "0"
GID_INCOME = "1950785482"
# ---------------------------------------------------------

# إعداد الصفحة لتكون عريضة ومتجاوبة
st.set_page_config(
    page_title="الداشبورد المالي",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed" # القائمة الجانبية مغلقة لراحة الموبايل
)

# --- تنسيق CSS مخصص للموبايل واللغة العربية ---
st.markdown("""
    <style>
    /* خلفية وتنسيق عام */
    .main { background-color: #f8f9fa; }
    
    /* محاذاة النصوص لليمين (RTL) */
    h1, h2, h3, h4, .stMarkdown, .stDataFrame, .stAlert {
        font-family: 'Tajawal', sans-serif;
        text-align: right;
        direction: rtl;
    }
    
    /* تنسيق بطاقات الأرقام (KPIs) */
    div[data-testid="stMetricLabel"] {
        text-align: right; 
        direction: rtl; 
        font-weight: bold;
        font-size: 1rem;
    }
    div[data-testid="stMetricValue"] {
        text-align: right; 
        direction: rtl;
    }
    
    /* تنسيق القوائم المنسدلة */
    div[data-testid="stSelectbox"] label {
        text-align: right; 
        direction: rtl;
    }
    
    /* إخفاء مؤشرات الجدول المزعجة */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    """, unsafe_allow_html=True)

# --- دوال المعالجة ---

def clean_currency(val):
    """دالة لتنظيف الأرقام والعملات المكتوبة بصيغ مختلفة"""
    if isinstance(val, str):
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

@st.cache_data(ttl=300) # تحديث البيانات تلقائياً كل 5 دقائق
def load_data():
    """تحميل البيانات من جوجل شيت وتنظيفها"""
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    try:
        df_exp = pd.read_csv(url_exp)
        df_inc = pd.read_csv(url_inc)
    except Exception as e:
        st.error(f"⚠️ تعذر الاتصال بجوجل شيت. تأكد من إعدادات المشاركة.\nالخطأ: {e}")
        st.stop()

    # --- تنظيف جدول المصاريف ---
    # محاولة إيجاد عمود المبلغ بذكاء
    col_money_exp = None
    for col in df_exp.columns:
        if "المبلغ" in str(col) or "amount" in str(col).lower():
            col_money_exp = col
            break
    if not col_money_exp: col_money_exp = df_exp.columns[4] # افتراضي

    df_exp[col_money_exp] = df_exp[col_money_exp].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce')
    df_exp = df_exp.dropna(subset=['التاريخ'])
    
    df_exp['السنة'] = df_exp['التاريخ'].dt.year
    df_exp['الشهر'] = df_exp['التاريخ'].dt.month
    df_exp['اليوم'] = df_exp['التاريخ'].dt.day
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    
    df_exp = df_exp.rename(columns={col_money_exp: 'المبلغ (جم)'})

    # --- تنظيف جدول الدخل ---
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

# تحميل البيانات
df_exp, df_inc = load_data()

# --- الفلاتر الجانبية ---
st.sidebar.header("🔍 فلترة البيانات")

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
days_exp = df_exp[(df_exp['السنة'] == selected_year) & (df_exp['الشهر'] == selected_month_num)]['اليوم']
days_inc = df_inc[(df_inc['السنة'] == selected_year) & (df_inc['الشهر'] == selected_month_num)]['اليوم']
available_days = sorted(list(set(days_exp) | set(days_inc)))
selected_day = st.sidebar.selectbox("اليوم (اختياري)", ["الكل"] + available_days)

# تطبيق الفلاتر
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

if st.button("🔄 تحديث البيانات الآن", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# --- 1. ملخص الأرقام (KPIs) ---
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("💰 صافي الربح", f"{net_profit:,.0f}", delta_color="normal")
col2.metric("💸 المصروفات", f"{total_exp:,.0f}", delta_color="inverse")
col3.metric("📥 التحصيلات", f"{total_inc:,.0f}")

st.markdown("---")

# --- 2. التحليل التفصيلي (مصاريف ودخل) ---
# استخدام Tabs لتوفير مساحة على الموبايل
tab1, tab2 = st.tabs(["📉 تحليل المصاريف", "📈 تحليل الدخل"])

with tab1:
    if not df_exp_filtered.empty:
        # تجميع المصاريف حسب البند
        grouped_exp = df_exp_filtered.groupby('البند الرئيسي')['المبلغ (جم)'].sum().reset_index()
        grouped_exp = grouped_exp.sort_values(by='المبلغ (جم)', ascending=False)
        
        # الرسم البياني
        fig_exp = px.bar(grouped_exp, x='المبلغ (جم)', y='البند الرئيسي', orientation='h', 
                         text_auto='.2s', title="أعلى بنود الصرف")
        fig_exp.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0,r=0))
        st.plotly_chart(fig_exp, use_container_width=True)
        
        # الجدول
        st.dataframe(
            grouped_exp,
            column_config={
                "البند الرئيسي": "البند",
                "المبلغ (جم)": st.column_config.NumberColumn("القيمة (ج.م)", format="%d")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("لا توجد بيانات مصاريف في هذه الفترة.")

with tab2:
    if not df_inc_filtered.empty:
        # تجميع الدخل حسب النوع
        grouped_inc = df_inc_filtered.groupby('نوع التحصيل')['المبلغ المحصل (جم)'].sum().reset_index()
        grouped_inc = grouped_inc.sort_values(by='المبلغ المحصل (جم)', ascending=False)
        
        # الرسم البياني
        fig_inc = px.bar(grouped_inc, x='المبلغ المحصل (جم)', y='نوع التحصيل', orientation='h', 
                         text_auto='.2s', title="مصادر الدخل", color_discrete_sequence=['#2ecc71'])
        fig_inc.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0,r=0))
        st.plotly_chart(fig_inc, use_container_width=True)
        
        # الجدول
        st.dataframe(
            grouped_inc,
            column_config={
                "نوع التحصيل": "المصدر",
                "المبلغ المحصل (جم)": st.column_config.NumberColumn("القيمة (ج.م)", format="%d")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("لا توجد بيانات دخل في هذه الفترة.")

# --- 3. الجداول التفصيلية (داخل Expander لتوفير المساحة) ---
st.markdown("### 📄 السجلات التفصيلية")
with st.expander("عرض سجل المصاريف اليومي"):
    st.dataframe(df_exp_filtered, use_container_width=True, hide_index=True)

with st.expander("عرض سجل التحصيلات اليومي"):
    st.dataframe(df_inc_filtered, use_container_width=True, hide_index=True)

st.markdown("---")

# --- 4. الملخص التاريخي الشامل (جميع الشهور) ---
st.header("📅 الأداء الشهري العام")
st.caption("مقارنة إجمالي الدخل والمصاريف لكل شهر موجود في الملف")

if not df_exp.empty or not df_inc.empty:
    # تجميع كل البيانات
    all_exp = df_exp.groupby('الشهر_سنة')['المبلغ (جم)'].sum().reset_index().rename(columns={'المبلغ (جم)': 'المصاريف'})
    all_inc = df_inc.groupby('الشهر_سنة')['المبلغ المحصل (جم)'].sum().reset_index().rename(columns={'المبلغ المحصل (جم)': 'التحصيلات'})
    
    # دمج الجدولين
    history_df = pd.merge(all_inc, all_exp, on='الشهر_سنة', how='outer').fillna(0)
    history_df['صافي الربح'] = history_df['التحصيلات'] - history_df['المصاريف']
    history_df = history_df.sort_values('الشهر_سنة')

    # رسم بياني مجمع
    melted = history_df.melt(id_vars=['الشهر_سنة'], value_vars=['التحصيلات', 'المصاريف'], var_name='النوع', value_name='المبلغ')
    fig_hist = px.bar(melted, x='الشهر_سنة', y='المبلغ', color='النوع', barmode='group',
                      color_discrete_map={'التحصيلات': '#2ecc71', 'المصاريف': '#e74c3c'})
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # عرض الجدول (تم إصلاح خطأ التنسيق هنا)
    st.dataframe(
        history_df,
        column_config={
            "الشهر_سنة": "الشهر",
            "التحصيلات": st.column_config.NumberColumn("الدخل", format="%d ج.م"),
            "المصاريف": st.column_config.NumberColumn("المصروف", format="%d ج.م"),
            "صافي الربح": st.column_config.NumberColumn("الصافي", format="%d ج.م"),
        },
        use_container_width=True,
        hide_index=True
    )
