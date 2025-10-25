import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
import numpy as np
from sklearn.linear_model import LinearRegression

conn = sqlite3.connect("expenses.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL
)
""")
conn.commit()

st.set_page_config(page_title="💰 Smart Expense Tracker", page_icon="💳")
st.write("### 💳 Smart Expense Tracker")
st.write("Record your daily expenses, analyze them, and visualize your spending!")

if st.button("🗑️ Delete All Expenses"):
    c.execute("DELETE FROM expenses")
    conn.commit()
    st.warning("⚠️ All expenses have been deleted!")

st.write("### ➕ Add a New Expense")
category = st.selectbox("Expense Category", ["Food", "Transport", "Entertainment", "Technology", "Health", "Other"])
amount = st.number_input("Amount (₺)", min_value=1, step=100)
expense_date = st.date_input("Date", value=date.today())

if st.button("💾 Save Expense"):
    c.execute("INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)", 
              (expense_date.strftime("%Y-%m-%d"), category, amount))
    conn.commit()
    st.success("✅ Expense saved to database!")

df = pd.read_sql("SELECT * FROM expenses", conn)

if not df.empty:
    st.write("### 📅 Filter and Analyze")
    start_date = st.date_input("Start Date", value=pd.to_datetime(df['date']).min())
    end_date = st.date_input("End Date", value=pd.to_datetime(df['date']).max())
    selected_categories = st.multiselect("Select Categories", options=df['category'].unique(), default=df['category'].unique())

    filtered_df = df[(df['date'] >= str(start_date)) & (df['date'] <= str(end_date))]
    filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

    if not filtered_df.empty:
        st.write("### 📊 Expense List")
        st.dataframe(filtered_df)

        total = filtered_df["amount"].sum()
        average = filtered_df["amount"].mean()
        st.info(f"💸 Total Expenses: {total:.2f} ₺")
        st.info(f"📈 Average Expense: {average:.2f} ₺")

        category_total = filtered_df.groupby("category")["amount"].sum()
        fig, ax = plt.subplots()
        ax.pie(category_total, labels=category_total.index, autopct="%1.1f%%")
        ax.set_title("Filtered Expenses by Category")
        st.pyplot(fig)
    else:
        st.warning("No data matches the selected filters.")
else:
    st.warning("No expenses recorded yet.")

# --- Predict next month's spending by category ---
st.write("### 📈 Next Month Expense Prediction (Category-wise)")
next_month_predictions = {}

for category in df['category'].unique():
    cat_df = df[df['category'] == category]
    cat_df['year_month'] = pd.to_datetime(cat_df['date']).dt.to_period('M')
    monthly_total = cat_df.groupby('year_month')['amount'].sum().reset_index()
    
    if len(monthly_total) > 1:
        monthly_total['month_index'] = np.arange(len(monthly_total))
        X = monthly_total[['month_index']]
        y = monthly_total['amount']
        model = LinearRegression()
        model.fit(X, y)
        next_month = np.array([[len(monthly_total)]])
        prediction = model.predict(next_month)[0]
        next_month_predictions[category] = prediction
    else:
        next_month_predictions[category] = 0

for cat, pred in next_month_predictions.items():
    st.info(f"💰 {cat}: {pred:.2f} ₺")

total_prediction = sum(next_month_predictions.values())
st.success(f"💳 Predicted Total Expenses for Next Month: {total_prediction:.2f} ₺")

conn.close()
