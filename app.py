import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# ⚙️ إعدادات الربط بجوجل شيت (تم دمج روابطك هنا)
# ---------------------------------------------------------

SHEET_ID = "1FP43Qlbqznlg57YpYwHECtwKf3i3Y9b6qHpjQ5WJXbQ"
GID_EXPENSES = "0"
GID_INCOME = "1950785482"

# ---------------------------------------------------------

st.set_page_config(
    page_title="داشبورد عايدة",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تنسيق CSS لدعم العربية وتحسين المظهر
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    h1, h2, h3 { font-family: 'Tajawal', sans-serif; text-align: right; }
    div[data-testid="stMetricLabel"] { text-align: right; direction: rtl; font-weight: bold;}
    div[data-testid="stMetricValue"] { text-align: right; direction: rtl; }
    .stDataFrame { direction: rtl; }
    div[data-testid="stExpander"] { direction: rtl; }
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

# تحميل البيانات من جوجل شيت
@st.cache_data(ttl=600) # تحديث كل 10 دقائق
def load_data():
    # تكوين روابط التحميل (CSV Export)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    try:
        df_exp = pd.read_csv(url_exp)
        df_inc = pd.read_csv(url_inc)
    except Exception as e:
        st.error(f"⚠️ مشكلة في الاتصال بجوجل شيت.\nتأكد أنك جعلت الشيت 'Anyone with the link' (أي شخص لديه الرابط).\nتفاصيل الخطأ: {e}")
        st.stop()

    # --- معالجة المصاريف ---
    # محاولة العثور على عمود المبلغ وتوحيد اسمه
    col_money_exp = 'المبلغ (جم)' if 'المبلغ (جم)' in df_exp.columns else df_exp.columns[4]
    
    df_exp[col_money_exp] = df_exp[col_money_exp].apply(clean_currency)
    df_exp['التاريخ'] = pd.to_datetime(df_exp['التاريخ'], errors='coerce')
    df_exp = df_exp.dropna(subset=['التاريخ'])
    df_exp = df_exp[df_exp['التاريخ'].dt.year > 2023] # فلتر السنوات
    df_exp['الشهر_سنة'] = df_exp['التاريخ'].dt.strftime('%Y-%m')
    df_exp = df_exp.rename(columns={col_money_exp: 'المبلغ (جم)'})

    # --- معالجة الدخل ---
    col_money_inc = 'المبلغ المحصل (جم)' if 'المبلغ المحصل (جم)' in df_inc.columns else df_inc.columns[3]

    df_inc[col_money_inc] = df_inc[col_money_inc].apply(clean_currency)
    df_inc['التاريخ'] = pd.to_datetime(df_inc['التاريخ'], errors='coerce')
    df_inc = df_inc.dropna(subset=['التاريخ'])
    df_inc = df_inc[df_inc['التاريخ'].dt.year > 2023] # فلتر السنوات
    df_inc['الشهر_سنة'] = df_inc['التاريخ'].dt.strftime('%Y-%m')
    df_inc = df_inc.rename(columns={col_money_inc: 'المبلغ المحصل (جم)'})

    return df_exp, df_inc

# تنفيذ التحميل
df_exp, df_inc = load_data()

# --- الفلاتر الجانبية ---
st.sidebar.header("📅 فلترة التاريخ")
if not df_exp.empty and not df_inc.empty:
    min_date = min(df_exp['التاريخ'].min(), df_inc['التاريخ'].min())
    max_date = max(df_exp['التاريخ'].max(), df_inc['التاريخ'].max())
else:
    min_date = pd.to_datetime("2024-01-01")
    max_date = pd.to_datetime("2030-12-31")

start_date = st.sidebar.date_input("من", min_date)
end_date = st.sidebar.date_input("إلى", max_date)

# تطبيق الفلتر
mask_exp = (df_exp['التاريخ'].dt.date >= start_date) & (df_exp['التاريخ'].dt.date <= end_date)
mask_inc = (df_inc['التاريخ'].dt.date >= start_date) & (df_inc['التاريخ'].dt.date <= end_date)

df_exp_filtered = df_exp.loc[mask_exp]
df_inc_filtered = df_inc.loc[mask_inc]

# --- الواجهة الرئيسية ---
st.title("📊 تقرير الأداء المالي (مباشر)")

if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()

# حسابات KPIs
total_exp = df_exp_filtered['المبلغ (جم)'].sum()
total_inc = df_inc_filtered['المبلغ المحصل (جم)'].sum()
net_profit = total_inc - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("صافي الربح", f"{net_profit:,.0f} ج.م")
col2.metric("المصروفات", f"{total_exp:,.0f} ج.م", delta_color="inverse")
col3.metric("التحصيلات", f"{total_inc:,.0f} ج.م")

st.markdown("---")

# --- الرسم البياني المقارن ---
st.subheader("📈 مقارنة شهرية")

if not df_exp_filtered.empty or not df_inc_filtered.empty:
    monthly_exp = df_exp_filtered.groupby('الشهر_سنة')['المبلغ (جم)'].sum().reset_index()
    monthly_inc = df_inc_filtered.groupby('الشهر_سنة')['المبلغ المحصل (جم)'].sum().reset_index()
    
    # توحيد الأسماء للرسم البياني
    monthly_exp = monthly_exp.rename(columns={'المبلغ (جم)': 'المبلغ'})
    monthly_inc = monthly_inc.rename(columns={'المبلغ المحصل (جم)': 'المبلغ'})
    
    monthly_exp['النوع'] = 'مصروفات'
    monthly_inc['النوع'] = 'تحصيلات'
    
    combined = pd.concat([monthly_inc, monthly_exp])
    
    if not combined.empty:
        fig = px.bar(combined, x='الشهر_سنة', y='المبلغ', color='النوع', 
                     barmode='group', color_discrete_map={'تحصيلات': '#2ecc71', 'مصروفات': '#e74c3c'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات كافية للرسم البياني")
else:
    st.info("لا توجد بيانات")

# --- الرسوم الدائرية ---
col_pie1, col_pie2 = st.columns(2)
with col_pie1:
    st.caption("توزيع المصروفات")
    if not df_exp_filtered.empty:
        fig_pie = px.pie(df_exp_filtered, values='المبلغ (جم)', names='البند الرئيسي', hole=0.4)
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

with col_pie2:
    st.caption("مصادر الدخل")
    if not df_inc_filtered.empty:
        fig_pie_inc = px.pie(df_inc_filtered, values='المبلغ المحصل (جم)', names='نوع التحصيل', hole=0.4)
        fig_pie_inc.update_layout(showlegend=False)
        st.plotly_chart(fig_pie_inc, use_container_width=True)

# --- الجداول التفصيلية ---
with st.expander("اضغط هنا لعرض تفاصيل المصاريف"):
    st.dataframe(df_exp_filtered, use_container_width=True)

with st.expander("اضغط هنا لعرض تفاصيل التحصيلات"):
    st.dataframe(df_inc_filtered, use_container_width=True)
