import streamlit as st
import pandas as pd
from datetime import datetime

# =========================
# FORMAT RUPIAH INDONESIA
# =========================
def format_rupiah(amount):
    return f"Rp. {int(amount):,}".replace(",", ".")


# =========================
# FUNGSI PERHITUNGAN
# =========================
def calculate_total_income(transactions):
    return sum(t['amount'] for t in transactions if t['type'] == 'Income')

def calculate_total_expenses(transactions):
    return sum(t['amount'] for t in transactions if t['type'] == 'Expense')

def calculate_balance(transactions):
    return calculate_total_income(transactions) - calculate_total_expenses(transactions)

# =========================
# TRANSAKSI
# =========================
def add_transaction(transactions, date, description, amount, category, transaction_type):
    if amount <= 0:
        st.error("Jumlah harus lebih dari 0")
        return
    transactions.append({
        'date': date,
        'description': description,
        'amount': amount,
        'category': category,
        'type': transaction_type
    })
    st.success("Transaksi berhasil ditambahkan")

def delete_transaction(transactions, index):
    if 0 <= index < len(transactions):
        del transactions[index]
        st.success("Transaksi berhasil dihapus")

# =========================
# GRAFIK (DENGAN STREAMLIT CHART)
# =========================
def plot_expense_bar(transactions):
    expenses = [t for t in transactions if t['type'] == 'Expense']
    if not expenses:
        st.write("Belum ada pengeluaran")
        return

    df = pd.DataFrame(expenses)
    category_sum = df.groupby('category')['amount'].sum()
    st.bar_chart(category_sum)

def plot_balance_over_time(transactions):
    if not transactions:
        return

    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    df['cumulative'] = df.apply(
        lambda x: x['amount'] if x['type'] == 'Income' else -x['amount'], axis=1
    ).cumsum()

    # Untuk line chart, gunakan date sebagai index dan cumulative sebagai kolom
    df.set_index('date', inplace=True)
    st.line_chart(df[['cumulative']])

# =========================
# EXPORT CSV
# =========================
def export_to_csv(transactions):
    df = pd.DataFrame(transactions)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        "transaksi.csv",
        "text/csv"
    )

# =========================
# SESSION STATE
# =========================
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# =========================
# UI
# =========================
st.title("Dashboard Manajemen Keuangan")

page = st.sidebar.radio(
    "Menu",
    ["Overview", "Tambah Transaksi", "Lihat Transaksi", "Analisis Budget", "Laporan", "Pengaturan"]
)

# =========================
# OVERVIEW
# =========================
if page == "Overview":
    transaksi = st.session_state.transactions

    total_income = calculate_total_income(transaksi)
    total_expenses = calculate_total_expenses(transaksi)
    balance = calculate_balance(transaksi)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pemasukan", format_rupiah(total_income))
    col2.metric("Total Pengeluaran", format_rupiah(total_expenses))
    col3.metric("Saldo", format_rupiah(balance))

# =========================
# TAMBAH TRANSAKSI
# =========================
elif page == "Tambah Transaksi":
    with st.form("form_transaksi"):
        date = st.date_input("Tanggal", datetime.today())
        description = st.text_input("Keterangan")
        amount = st.number_input("Jumlah", min_value=0.01, step=1000.0)
        category = st.selectbox("Kategori", ["Food", "Transport", "Entertainment", "Bills", "Salary", "Other"])
        transaction_type = st.selectbox("Tipe", ["Income", "Expense"])
        submit = st.form_submit_button("Simpan")

        if submit:
            add_transaction(st.session_state.transactions, date, description, amount, category, transaction_type)

# =========================
# LIHAT TRANSAKSI
# =========================
elif page == "Lihat Transaksi":
    transaksi = st.session_state.transactions
    if transaksi:
        df = pd.DataFrame(transaksi)
        df['amount'] = df['amount'].apply(format_rupiah)
        st.dataframe(df)

        idx = st.number_input("Index yang dihapus", 0, len(transaksi)-1)
        if st.button("Hapus"):
            delete_transaction(transaksi, idx)
    else:
        st.info("Belum ada transaksi")

# =========================
# ANALISIS BUDGET
# =========================
elif page == "Analisis Budget":
    transaksi = st.session_state.transactions
    expenses = [t for t in transaksi if t['type'] == 'Expense']

    if expenses:
        df = pd.DataFrame(expenses)
        category_sum = df.groupby('category')['amount'].sum()

        # Chart pengeluaran per kategori
        st.subheader("Pengeluaran per Kategori")
        st.bar_chart(category_sum)

        # Statistik tambahan
        st.subheader("Statistik Pengeluaran")
        total_expenses = category_sum.sum()
        st.metric("Total Pengeluaran", format_rupiah(total_expenses))
        st.metric("Rata-rata Pengeluaran per Kategori", format_rupiah(category_sum.mean()))
        st.metric("Kategori dengan Pengeluaran Tertinggi", f"{category_sum.idxmax()} ({format_rupiah(category_sum.max())})")

        # Persentase pengeluaran per kategori
        st.subheader("Persentase Pengeluaran per Kategori")
        percentages = (category_sum / total_expenses * 100).round(2)
        for cat, pct in percentages.items():
            st.write(f"{cat}: {pct}%")

        st.subheader("Atur Budget")
        budgets = {}
        for cat in category_sum.index:
            budgets[cat] = st.number_input(f"Budget {cat}", min_value=0.0, value=0.0)

        # Chart budget vs actual
        if any(budgets.values()):
            st.subheader("Budget vs Aktual")
            budget_df = pd.DataFrame({
                'Kategori': category_sum.index,
                'Aktual': category_sum.values,
                'Budget': [budgets.get(cat, 0) for cat in category_sum.index]
            })
            budget_df.set_index('Kategori', inplace=True)
            st.bar_chart(budget_df)

            # Pesan untuk setiap kategori
            for cat in category_sum.index:
                budget = budgets[cat]
                actual = category_sum[cat]
                if budget > 0:
                    if actual > budget:
                        st.error(
                            f"{cat} melebihi budget: {format_rupiah(actual)} > {format_rupiah(budget)}"
                        )
                    else:
                        st.success(
                            f"{cat} aman: {format_rupiah(actual)} ≤ {format_rupiah(budget)}"
                        )

# =========================
# LAPORAN
# =========================
elif page == "Laporan":
    plot_expense_bar(st.session_state.transactions)
    plot_balance_over_time(st.session_state.transactions)

# =========================
# PENGATURAN
# =========================
elif page == "Pengaturan":
    export_to_csv(st.session_state.transactions)
    if st.button("Reset Data"):
        st.session_state.transactions = []
        st.success("Data berhasil direset")
