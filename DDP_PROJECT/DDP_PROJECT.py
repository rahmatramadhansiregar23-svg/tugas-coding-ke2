import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io

# Fungsi untuk menghitung total income
def calculate_total_income(transactions):
    return sum(t['amount'] for t in transactions if t['type'] == 'Income')

# Fungsi untuk menghitung total expenses
def calculate_total_expenses(transactions):
    return sum(t['amount'] for t in transactions if t['type'] == 'Expense')

# Fungsi untuk menghitung balance
def calculate_balance(transactions):
    income = calculate_total_income(transactions)
    expenses = calculate_total_expenses(transactions)
    return income - expenses

# Fungsi untuk menambahkan transaksi
def add_transaction(transactions, date, description, amount, category, transaction_type):
    if amount <= 0:
        st.error("Amount must be positive!")
        return
    if transaction_type not in ['Income', 'Expense']:
        st.error("Invalid transaction type!")
        return
    transactions.append({
        'date': date,
        'description': description,
        'amount': amount,
        'category': category,
        'type': transaction_type
    })
    st.success("Transaction added successfully!")

# Fungsi untuk menghapus transaksi berdasarkan index
def delete_transaction(transactions, index):
    if 0 <= index < len(transactions):
        del transactions[index]
        st.success("Transaction deleted successfully!")
    else:
        st.error("Invalid index!")

# Fungsi untuk membuat chart pie untuk expenses berdasarkan kategori
def plot_expense_pie(transactions):
    expenses = [t for t in transactions if t['type'] == 'Expense']
    if not expenses:
        st.write("No expenses to display.")
        return
    df = pd.DataFrame(expenses)
    category_sum = df.groupby('category')['amount'].sum()
    fig, ax = plt.subplots()
    ax.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

# Fungsi untuk membuat line chart balance over time
def plot_balance_over_time(transactions):
    if not transactions:
        st.write("No transactions to display.")
        return
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['cumulative'] = df.apply(lambda x: x['amount'] if x['type'] == 'Income' else -x['amount'], axis=1).cumsum()
    fig, ax = plt.subplots()
    ax.plot(df['date'], df['cumulative'], marker='o')
    ax.set_title('Balance Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Balance')
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Fungsi untuk export data ke CSV
def export_to_csv(transactions):
    df = pd.DataFrame(transactions)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='transactions.csv',
        mime='text/csv'
    )

# Inisialisasi session state untuk menyimpan data
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# Judul aplikasi
st.title("Complex Financial Management Dashboard")

# Sidebar untuk navigasi
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Add Transaction", "View Transactions", "Budget Analysis", "Reports", "Settings"])

# Dashboard Overview
if page == "Overview":
    st.header("Financial Overview")
    transactions = st.session_state.transactions
    total_income = calculate_total_income(transactions)
    total_expenses = calculate_total_expenses(transactions)
    balance = calculate_balance(transactions)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"Rp{total_income:.2f}")
    with col2:
        st.metric("Total Expenses", f"Rp{total_expenses:.2f}")
    with col3:
        st.metric("Balance", f"Rp{balance:.2f}")
    
    if balance < 0:
        st.warning("Your balance is negative! Consider reducing expenses.")
    elif balance > 1000:
        st.success("Great! You have a healthy balance.")
    else:
        st.info("Keep tracking your finances.")

# Dashboard Add Transaction
elif page == "Add Transaction":
    st.header("Add New Transaction")
    with st.form("add_transaction_form"):
        date = st.date_input("Date", value=datetime.today())
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Bills", "Salary", "Other"])
        transaction_type = st.selectbox("Type", ["Income", "Expense"])
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            add_transaction(st.session_state.transactions, date, description, amount, category, transaction_type)

# Dashboard View Transactions
elif page == "View Transactions":
    st.header("View All Transactions")
    transactions = st.session_state.transactions
    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df)
        # Opsi hapus transaksi
        index_to_delete = st.number_input("Enter index to delete (0-based)", min_value=0, max_value=len(transactions)-1, step=1)
        if st.button("Delete Transaction"):
            delete_transaction(transactions, index_to_delete)
    else:
        st.write("No transactions yet.")

# Dashboard Budget Analysis
elif page == "Budget Analysis":
    st.header("Budget vs Actual")
    transactions = st.session_state.transactions
    expenses = [t for t in transactions if t['type'] == 'Expense']
    if expenses:
        df = pd.DataFrame(expenses)
        category_sum = df.groupby('category')['amount'].sum()
        st.bar_chart(category_sum)
        # Budget input
        st.subheader("Set Budgets")
        budgets = {}
        for cat in ["Food", "Transport", "Entertainment", "Bills", "Other"]:
            budgets[cat] = st.number_input(f"Budget for {cat}", min_value=0.0, step=0.01, value=0.0)
        if st.button("Compare"):
            for cat, budget in budgets.items():
                actual = category_sum.get(cat, 0)
                if actual > budget and budget > 0:
                    st.error(f"Over budget in {cat}: ${actual:.2f} > ${budget:.2f}")
                elif budget > 0:
                    st.success(f"Under budget in {cat}: ${actual:.2f} <= ${budget:.2f}")
    else:
        st.write("No expenses to analyze.")

# Dashboard Reports
elif page == "Reports":
    st.header("Financial Reports")
    transactions = st.session_state.transactions
    if transactions:
        st.subheader("Expense Breakdown")
        plot_expense_pie(transactions)
        st.subheader("Balance Over Time")
        plot_balance_over_time(transactions)
    else:
        st.write("No data for reports.")

# Dashboard Settings
elif page == "Settings":
    st.header("Settings")
    st.subheader("Export Data")
    export_to_csv(st.session_state.transactions)
    st.subheader("Reset All Data")
    if st.button("Reset"):
        st.session_state.transactions = []
        st.success("All data reset!")
