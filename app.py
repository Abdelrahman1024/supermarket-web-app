import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# ==============================
# Database setup
# ==============================
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
c = conn.cursor()

# إنشاء جدول المنتجات لو مش موجود
c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                price REAL,
                quantity INTEGER
            )''')
conn.commit()

# إضافة الأعمدة الجديدة لو مش موجودة
columns = [col[1] for col in c.execute("PRAGMA table_info(products)").fetchall()]
if "cost" not in columns:
    c.execute("ALTER TABLE products ADD COLUMN cost REAL DEFAULT 0")
if "profit_margin" not in columns:
    c.execute("ALTER TABLE products ADD COLUMN profit_margin REAL DEFAULT 0")
conn.commit()

# إنشاء جدول المبيعات
c.execute('''CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                total REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )''')
conn.commit()

# ==============================
# Helper Functions
# ==============================
def add_or_update_product(name, category, cost, profit_margin, quantity):
    selling_price = cost * (1 + profit_margin / 100)
    c.execute("SELECT id, quantity FROM products WHERE name=? AND category=?", (name, category))
    product = c.fetchone()
    if product:
        new_qty = product[1] + quantity
        c.execute("UPDATE products SET quantity=?, price=?, cost=?, profit_margin=? WHERE id=?",
                  (new_qty, selling_price, cost, profit_margin, product[0]))
    else:
        c.execute("INSERT INTO products (name, category, price, cost, profit_margin, quantity) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, category, selling_price, cost, profit_margin, quantity))
    conn.commit()

def get_products_by_category(category):
    c.execute("SELECT id, name FROM products WHERE category=?", (category,))
    return c.fetchall()

def delete_product(product_id):
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()

def record_sale(product_id, qty):
    c.execute("SELECT quantity, price, cost FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    if product and product[0] >= qty:
        new_qty = product[0] - qty
        total = qty * product[1]
        profit = qty * (product[1] - product[2])
        c.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, product_id))
        c.execute("INSERT INTO sales (product_id, quantity, total) VALUES (?, ?, ?)", (product_id, qty, total))
        conn.commit()
        return True, total, profit
    return False, 0, 0

# ==============================
# واجهة Streamlit
# ==============================
st.set_page_config(page_title="Supermarket System", layout="wide")

st.sidebar.title("📊 إدارة السوبرماركت")
menu = st.sidebar.radio("اختر الصفحة", ["إدارة المنتجات", "إدارة المخزون", "إدارة المبيعات", "إدارة التحليلات"])

categories = ["خضار", "فاكهة", "مشروبات", "حلويات", "معلبات", "أسماك"]

# ==============================
# إدارة المنتجات
# ==============================
if menu == "إدارة المنتجات":
    st.header("🛒 إدارة المنتجات")
    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("اختر الفئة", categories)
        name = st.text_input("اسم المنتج")
        cost = st.number_input("تكلفة المنتج", min_value=0.0, step=0.5)
        profit_margin = st.number_input("نسبة الربح %", min_value=0.0, max_value=100.0, step=1.0)
        qty = st.number_input("الكمية", min_value=1, step=1)
        if st.button("➕ إضافة / تحديث المنتج"):
            if name and cost > 0:
                add_or_update_product(name, category, cost, profit_margin, qty)
                st.success(f"✅ تم الحفظ بنجاح! سعر البيع = {cost * (1 + profit_margin / 100):.2f} جنيه")

    with col2:
        st.subheader("📋 قائمة المنتجات")
        df = pd.read_sql("SELECT * FROM products", conn)
        st.dataframe(df)

        product_list = get_products_by_category(category)
        if product_list:
            prod_id = st.selectbox("اختر منتج للحذف", product_list, format_func=lambda x: x[1])
            if st.button("🗑️ حذف المنتج"):
                delete_product(prod_id[0])
                st.warning("تم حذف المنتج")

# ==============================
# إدارة المخزون
# ==============================
# ==============================
# إدارة المخزون
# ==============================
elif menu == "إدارة المخزون":
    st.header("📦 إدارة المخزون")
    df = pd.read_sql("SELECT * FROM products", conn)

    # إضافة عمود حالة المخزون
    df["حالة المخزون"] = df["quantity"].apply(lambda x: "⚠️ قليل" if x < 5 else "✅ متوفر")

    # تلوين الجدول حسب الكمية
    def highlight_stock(row):
        color = 'background-color: red' if row['quantity'] < 5 else 'background-color: lightgreen'
        return [color]*len(row)

    st.dataframe(df.style.apply(highlight_stock, axis=1))

# ==============================
# إدارة المبيعات
# ==============================
elif menu == "إدارة المبيعات":
    st.header("💵 إدارة المبيعات")
    category = st.selectbox("اختر الفئة", categories)
    products = get_products_by_category(category)
    if products:
        prod_id = st.selectbox("اختر المنتج", products, format_func=lambda x: x[1])
        qty = st.number_input("الكمية", min_value=1, step=1)
        if st.button("💰 تسجيل عملية بيع"):
            success, total, profit = record_sale(prod_id[0], qty)
            if success:
                st.success(f"✅ تم تسجيل البيع - الإجمالي: {total:.2f} جنيه - الربح: {profit:.2f} جنيه")
            else:
                st.error("❌ الكمية غير كافية بالمخزن")
    else:
        st.info("لا يوجد منتجات في هذه الفئة")

# ==============================
# إدارة التحليلات
# ==============================
elif menu == "إدارة التحليلات":
    st.header("📊 التحليلات")

    sales_df = pd.read_sql("SELECT * FROM sales", conn)
    products_df = pd.read_sql("SELECT id, name, cost FROM products", conn)

    if not sales_df.empty:
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        sales_df["day"] = sales_df["date"].dt.date
        sales_df = sales_df.merge(products_df, left_on="product_id", right_on="id", how="left")
        
        # حساب الربح لكل عملية
        sales_df["profit"] = sales_df["total"] - (sales_df["quantity"] * sales_df["cost"])
        
        # الربح الصافي الإجمالي
        net_profit = sales_df["profit"].sum()
        st.metric("💰 الربح الصافي الإجمالي", f"{net_profit:.2f} جنيه")

        # الربح الصافي اليومي
        daily_profit = sales_df.groupby("day")["profit"].sum().reset_index()
        fig_profit = px.line(daily_profit, x="day", y="profit", title="💵 الربح الصافي اليومي")
        st.plotly_chart(fig_profit, use_container_width=True)

        # المبيعات اليومية
        daily_sales = sales_df.groupby("day")["total"].sum().reset_index()
        fig_sales = px.line(daily_sales, x="day", y="total", title="📈 المبيعات اليومية")
        st.plotly_chart(fig_sales, use_container_width=True)

        # أكثر المنتجات مبيعًا
        top_products = sales_df.groupby("product_id")["quantity"].sum().reset_index()
        top_products = top_products.merge(products_df, left_on="product_id", right_on="id")
        fig_top = px.bar(top_products, x="name", y="quantity", title="🏆 المنتجات الأكثر مبيعًا")
        st.plotly_chart(fig_top, use_container_width=True)

    else:
        st.info("لا توجد بيانات مبيعات بعد")
