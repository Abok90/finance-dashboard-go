import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة
st.set_page_config(
    page_title="داشبورد عايدة",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed" # جعل القائمة الجانبية مغلقة لراحة الموبايل
)

# --- تنسيق CSS لتحسين المظهر للموبايل ---
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    h1, h2, h3 { font-family: 'Tajawal', sans-serif; text-align: right; }
    div[data-testid="stMetricLabel"] { text-align: right; direction: rtl; font-weight: bold;}
    div[data-testid="stMetricValue"] { text-align: right; direction: rtl; }
    /* إخفاء القوائم المزعجة */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    /* تحسين الجداول */
    .stDataFrame { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- دوال التنظيف ---
def clean_currency(val):
    if isinstance(val, str):
        val = val.replace('EGP', '').strip()
        val = val.replace('٬', '') # فاصلة الألوف
        val = val.replace('٫', '.') # العلامة العشرية
        val = val.replace(',', '') 
        try:
            return float(val)
        except:
            return 0.0
    return val

@st.cache_data
def load_data():
    # أسماء الملفات كما رفعتها أنت
    files = {
        "expenses": "expenses.csv",
        "income": "income.csv"
    }
    
    try:
        df_exp = pd.read_csv(files["expenses"])
        df_inc = pd.read_csv(files["income"])
    except FileNotFoundError:
        st.error("⚠️ الملفات غير موجودة! تأكد من رفع ملفات CSV بنفس الأسماء الصحيحة.")
        st.stop()

    # معالجة المصاريف
    df_exp['المبلغ (جم)'] = df_exp['المبلغ (جم)'].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce') # تجاهل التواريخ الخاطئة
    df_exp = df_exp.dropna(subset=['التاريخ']) # حذف الصفوف بدون تاريخ
    df_exp = df_exp[df_exp['التاريخ'].dt.year > 2023] # (تعديل هام) تجاهل أي سنة قبل 2024
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    
    # معالجة الدخل
    df_inc['المبلغ المحصل (جم)'] = df_inc['المبلغ المحصل (جم)'].apply(clean_currency)
    df_inc['التاريخ'] = pd.to_datetime(df_inc['التاريخ'], errors='coerce')
    df_inc = df_inc.dropna(subset=['التاريخ'])
    df_inc = df_inc[df_inc['التاريخ'].dt.year > 2023] # (تعديل هام) تجاهل أي سنة قبل 2024
    df_inc['الشهر_سنة'] = df_inc['التاريخ'].dt.strftime('%Y-%m')

    return df_exp, df_inc

# --- تحميل البيانات ---
df_exp, df_inc = load_data()

# --- القائمة الجانبية (الفلاتر) ---
st.sidebar.header("📅 فلترة التاريخ")
# تحديد تواريخ افتراضية منطقية (أول وآخر تاريخ موجود فعلياً في البيانات)
min_date = min(df_exp['التاريخ'].min(), df_inc['التاريخ'].min())
max_date = max(df_exp['التاريخ'].max(), df_inc['التاريخ'].max())

start_date = st.sidebar.date_input("من", min_date)
end_date = st.sidebar.date_input("إلى", max_date)

# تطبيق الفلتر
mask_exp = (df_exp['التاريخ'].dt.date >= start_date) & (df_exp['التاريخ'].dt.date <= end_date)
mask_inc = (df_inc['التاريخ'].dt.date >= start_date) & (df_inc['التاريخ'].dt.date <= end_date)
df_exp_filtered = df_exp.loc[mask_exp]
df_inc_filtered = df_inc.loc[mask_inc]

# --- الواجهة الرئيسية ---
st.title("📊 لوحة المتابعة المالية")

# 1. ملخص الأرقام (KPIs)
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

# استخدام أعمدة متجاوبة للموبايل
col1, col2, col3 = st.columns(3)
col1.metric("صافي الربح", f"{net_profit:,.0f}", delta_color="normal")
col2.metric("المصروفات", f"{total_exp:,.0f}", delta="-")
col3.metric("التحصيلات", f"{total_inc:,.0f}")

st.markdown("---")

# 2. الرسم البياني الشهري (الأهم)
st.subheader("📈 حركة الأموال شهرياً")
monthly_exp = df_exp_filtered.groupby('الشهر_سنة')['المبلغ (جم)'].sum().reset_index()
monthly_inc = df_inc_filtered.groupby('الشهر_سنة')['المبلغ المحصل (جم)'].sum().reset_index()
monthly_exp['النوع'] = 'مصروفات'
monthly_inc['النوع'] = 'تحصيلات'
combined = pd.concat([monthly_inc, monthly_exp])

fig = px.bar(combined, x='الشهر_سنة', y='المبلغ', color='النوع', 
             barmode='group', color_discrete_map={'تحصيلات': '#2ecc71', 'مصروفات': '#e74c3c'})
fig.update_layout(xaxis_title="", yaxis_title="", showlegend=True, legend_title="")
st.plotly_chart(fig, use_container_width=True)

# 3. تفاصيل المصروفات
st.markdown("---")
st.subheader("💸 أين تذهب المصروفات؟")
col_pie, col_bar = st.columns([1, 1])

with col_pie:
    # رسم دائري للبند الرئيسي
    fig_pie = px.pie(df_exp_filtered, values='المبلغ (جم)', names='البند الرئيسي', hole=0.4)
    fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# 4. الجداول التفصيلية (داخل قوائم منسدلة لتوفير المساحة)
st.markdown("---")
with st.expander("📄 اضغط هنا لعرض جدول تفاصيل المصاريف"):
    st.dataframe(df_exp_filtered[['التاريخ', 'البند الرئيسي', 'تفاصيل', 'المبلغ (جم)']], use_container_width=True)

with st.expander("📄 اضغط هنا لعرض جدول تفاصيل التحصيلات"):
    st.dataframe(df_inc_filtered[['التاريخ', 'شركة الشحن', 'المبلغ المحصل (جم)']], use_container_width=True)

