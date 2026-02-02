import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# إعدادات الصفحة (يجب أن تكون أول أمر في الكود)
st.set_page_config(
    page_title="لوحة المعلومات المالية",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- تنسيق CSS لتحسين المظهر ودعم اللغة العربية (RTL) ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    h1, h2, h3 {
        font-family: 'Tajawal', sans-serif;
        text-align: right;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: right;
    }
    div[data-testid="stMetricLabel"] {
        text-align: right; 
        direction: rtl;
    }
    div[data-testid="stMetricValue"] {
        text-align: right;
        direction: rtl;
    }
    .css-10trblm {
        text-align: right;
    }
    /* محاولة لفرض اتجاه اليمين لليسار للعناصر */
    .stDataFrame, .stTable {
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

# --- دالة تنظيف العملة (تتعامل مع الفواصل العربية) ---
def clean_currency(val):
    if isinstance(val, str):
        # إزالة كلمة EGP والمسافات
        val = val.replace('EGP', '').strip()
        # استبدال الفاصلة العربية للألوف (٬) بلا شيء
        val = val.replace('٬', '')
        # استبدال الفاصلة العربية العشرية (٫) بنقطة عادية
        val = val.replace('٫', '.')
        # إزالة الفاصلة العادية إذا وجدت كفاصل ألوف (احتياطي)
        val = val.replace(',', '')
        try:
            return float(val)
        except ValueError:
            return 0.0
    return val

# --- دالة تحميل البيانات ---
@st.cache_data
def load_data(expenses_file, income_file):
    # تحميل الملفات
    df_exp = pd.read_csv(expenses_file)
    df_inc = pd.read_csv(income_file)

    # 1. معالجة المصاريف
    df_exp['المبلغ (جم)'] = df_exp['المبلغ (جم)'].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'])
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.to_period('M').astype(str)
    
    # 2. معالجة الدخل
    df_inc['المبلغ المحصل (جم)'] = df_inc['المبلغ المحصل (جم)'].apply(clean_currency)
    df_inc['التاريخ'] = pd.to_datetime(df_inc['التاريخ'])
    df_inc['الشهر_سنة'] = df_inc['التاريخ'].dt.to_period('M').astype(str)

    return df_exp, df_inc

# --- الواجهة الرئيسية ---

st.title("📊 لوحة المعلومات المالية الاحترافية")
st.markdown("---")

# رفع الملفات (اختياري، إذا لم توجد الملفات في المسار)
# لجعل الكود يعمل مباشرة مع الملفات المرفقة، سنفترض وجودها بنفس الاسم
# ولكن سنضع خيار الرفع للمرونة
col_upload1, col_upload2 = st.columns(2)
uploaded_exp = col_upload1.file_uploader("تحميل ملف المصاريف (Expenses.csv)", type=['csv'])
uploaded_inc = col_upload2.file_uploader("تحميل ملف الدخل (Income.csv)", type=['csv'])

# استخدام الملفات الافتراضية إذا لم يتم الرفع
if not uploaded_exp:
    try:
        uploaded_exp = "New Microsoft Excel Worksheet.xlsx - Expenses.csv"
    except:
        st.warning("يرجى رفع ملف المصاريف")

if not uploaded_inc:
    try:
        uploaded_inc = "New Microsoft Excel Worksheet.xlsx - Income.csv"
    except:
        st.warning("يرجى رفع ملف الدخل")

try:
    df_exp, df_inc = load_data(uploaded_exp, uploaded_inc)
except Exception as e:
    st.error(f"بانتظار تحميل الملفات... أو حدث خطأ في القراءة: {e}")
    st.stop()

# --- الفلاتر الجانبية (Sidebar) ---
st.sidebar.header("🔍 خيارات التصفية")
st.sidebar.markdown("---")

# استخراج التواريخ المتاحة
all_dates = pd.concat([df_exp['التاريخ'], df_inc['التاريخ']])
min_date = all_dates.min()
max_date = all_dates.max()

start_date = st.sidebar.date_input("من تاريخ", min_date)
end_date = st.sidebar.date_input("إلى تاريخ", max_date)

# تطبيق الفلتر على البيانات
mask_exp = (df_exp['التاريخ'].dt.date >= start_date) & (df_exp['التاريخ'].dt.date <= end_date)
mask_inc = (df_inc['التاريخ'].dt.date >= start_date) & (df_inc['التاريخ'].dt.date <= end_date)

df_exp_filtered = df_exp.loc[mask_exp]
df_inc_filtered = df_inc.loc[mask_inc]

# --- الحسابات الرئيسية (KPIs) ---
total_expenses = df_exp_filtered['المبلغ (جم)'].sum()
total_income = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_income - total_expenses

# عرض المؤشرات
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="💰 صافي الربح", value=f"{net_profit:,.2f} ج.م", delta_color="normal")
with col2:
    st.metric(label="📉 إجمالي المصاريف", value=f"{total_expenses:,.2f} ج.م", delta="-")
with col3:
    st.metric(label="📈 إجمالي الدخل", value=f"{total_income:,.2f} ج.م")

st.markdown("---")

# --- الرسوم البيانية ---

# 1. تجهيز بيانات الرسم البياني الشهري (مجمع)
monthly_exp = df_exp_filtered.groupby('الشهر_سنة')['المبلغ (جم)'].sum().reset_index()
monthly_inc = df_inc_filtered.groupby('الشهر_سنة')['المبلغ المحصل (جم)'].sum().reset_index()

monthly_exp['النوع'] = 'مصاريف'
monthly_inc['النوع'] = 'دخل'
monthly_inc.columns = ['الشهر_سنة', 'المبلغ', 'النوع']
monthly_exp.columns = ['الشهر_سنة', 'المبلغ', 'النوع']

combined_monthly = pd.concat([monthly_inc, monthly_exp])

# رسم المخطط البياني (Bar Chart)
fig_monthly = px.bar(
    combined_monthly, 
    x='الشهر_سنة', 
    y='المبلغ', 
    color='النوع', 
    barmode='group',
    title='مقارنة الدخل والمصاريف شهرياً',
    color_discrete_map={'دخل': '#2ecc71', 'مصاريف': '#e74c3c'},
    text_auto='.2s'
)
fig_monthly.update_layout(xaxis_title="الشهر", yaxis_title="المبلغ (ج.م)")
st.plotly_chart(fig_monthly, use_container_width=True)

# تقسيم الشاشة للتحليلات التفصيلية
tab1, tab2 = st.tabs(["تحليل المصاريف", "تحليل الدخل"])

with tab1:
    st.header("تفاصيل المصروفات")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        # Pie Chart للبند الرئيسي
        fig_pie_exp = px.pie(
            df_exp_filtered, 
            values='المبلغ (جم)', 
            names='البند الرئيسي', 
            title='توزيع المصاريف حسب البند الرئيسي',
            hole=0.4
        )
        st.plotly_chart(fig_pie_exp, use_container_width=True)
    
    with c2:
        # Bar chart للمصنع vs أونلاين
        if 'أونلاين / مصنع' in df_exp_filtered.columns:
            exp_type_counts = df_exp_filtered.groupby('أونلاين / مصنع')['المبلغ (جم)'].sum().reset_index()
            fig_bar_type = px.bar(
                exp_type_counts, 
                x='أونلاين / مصنع', 
                y='المبلغ (جم)',
                color='أونلاين / مصنع',
                title='المصاريف: مصنع مقابل أونلاين'
            )
            st.plotly_chart(fig_bar_type, use_container_width=True)
            
    st.subheader("جدول بيانات المصاريف")
    st.dataframe(df_exp_filtered[['التاريخ', 'البند الرئيسي', 'تفاصيل', 'المبلغ (جم)', 'ملاحظات']], use_container_width=True)

with tab2:
    st.header("تفاصيل الدخل")
    
    # Bar Chart لنوع التحصيل
    income_by_type = df_inc_filtered.groupby('نوع التحصيل')['المبلغ المحصل (جم)'].sum().reset_index().sort_values(by='المبلغ المحصل (جم)', ascending=False)
    
    fig_inc_bar = px.bar(
        income_by_type,
        x='نوع التحصيل',
        y='المبلغ المحصل (جم)',
        text_auto='.2s',
        title='مصادر الدخل (شركات الشحن)',
        color='المبلغ المحصل (جم)',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_inc_bar, use_container_width=True)
    
    st.subheader("جدول بيانات الدخل")
    st.dataframe(df_inc_filtered[['التاريخ', 'نوع التحصيل', 'شركة الشحن', 'المبلغ المحصل (جم)']], use_container_width=True)

# --- تذييل الصفحة ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>تم إنشاء هذه اللوحة بواسطة بايثون (Streamlit) 🚀</div>", unsafe_allow_html=True)