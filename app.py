@st.cache_data(ttl=300)
def load_data():
    exp_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_EXPENSES}"
    inc_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INCOME}"

    df_exp = pd.read_csv(exp_url)
    df_inc = pd.read_csv(inc_url)

    # ---------------------------
    # 🔍 Detect amount column
    # ---------------------------
    def detect_amount_column(df):
        for col in df.columns:
            col_clean = str(col).lower()
            if any(k in col_clean for k in ["المبلغ", "amount", "egp", "ج.م"]):
                return col
        return None

    exp_amount_col = detect_amount_column(df_exp)
    inc_amount_col = detect_amount_column(df_inc)

    if not exp_amount_col or not inc_amount_col:
        st.error("❌ لم يتم العثور على عمود المبلغ في الشيت")
        st.stop()

    # ---------------------------
    # 🧹 Clean currency
    # ---------------------------
    df_exp[exp_amount_col] = df_exp[exp_amount_col].apply(clean_currency)
    df_inc[inc_amount_col] = df_inc[inc_amount_col].apply(clean_currency)

    df_exp.rename(columns={exp_amount_col: "المبلغ"}, inplace=True)
    df_inc.rename(columns={inc_amount_col: "المبلغ"}, inplace=True)

    # ---------------------------
    # 📅 Date handling
    # ---------------------------
    df_exp["التاريخ"] = pd.to_datetime(df_exp["التاريخ"], errors="coerce")
    df_inc["التاريخ"] = pd.to_datetime(df_inc["التاريخ"], errors="coerce")

    df_exp.dropna(subset=["التاريخ"], inplace=True)
    df_inc.dropna(subset=["التاريخ"], inplace=True)

    for df in [df_exp, df_inc]:
        df["السنة"] = df["التاريخ"].dt.year
        df["الشهر"] = df["التاريخ"].dt.month
        df["اليوم"] = df["التاريخ"].dt.day
        df["شهر"] = df["التاريخ"].dt.strftime("%Y-%m")

    return df_exp, df_inc
