import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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
# GRAFIK
# =========================
def plot_expense_pie(transactions):
    expenses = [t for t in transactions if t['type'] == 'Expense']
    if not expenses:
        st.write("Belum ada pengeluaran")
        return

    df = pd.DataFrame(expenses)
    category_sum = df.groupby('category')['amount'].sum()

    fig, ax = plt.subplots()
    ax.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

def plot_balance_over_time(transactions):
    if not transactions:
        return

    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    df['cumulative'] = df.apply(
        lambda x: x['amount'] if x['type'] == 'Income' else -x['amount'], axis=1
    ).cumsum()

    fig, ax = plt.subplots()
    ax.plot(df['date'], df['cumulative'], marker='o')

    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f"Rp. {int(x):,}".replace(",", "."))
    )

    ax.set_title("Saldo dari Waktu ke Waktu")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Saldo")
    plt.xticks(rotation=45)
    st.pyplot(fig)

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
        st.bar_chart(category_sum)

        st.subheader("Atur Budget")
        for cat in category_sum.index:
            budget = st.number_input(f"Budget {cat}", min_value=0.0)
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
    plot_expense_pie(st.session_state.transactions)
    plot_balance_over_time(st.session_state.transactions)

# =========================
# PENGATURAN
# =========================
elif page == "Pengaturan":
    export_to_csv(st.session_state.transactions)
    if st.button("Reset Data"):
        st.session_state.transactions = []
        st.success("Data berhasil direset")
