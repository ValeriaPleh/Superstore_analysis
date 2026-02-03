# Импорт библиотек
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

# Загружаем CSV
df = pd.read_csv('data/Superstore.csv', encoding='ISO-8859-1')
print(df.head())

# Приведем название колонок к удобному виду
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
print(df.columns)

# Подготовка данных
print(df.dtypes)
print(df.isnull().sum())
print(df.duplicated().sum())
df = df.drop_duplicates()
df['order_date'] = pd.to_datetime(df['order_date'], dayfirst=True)
df['ship_date'] = pd.to_datetime(df['ship_date'], dayfirst=True)

# Структурируем данные под SQL и аналитические запросы
# Таблица клиентов
customers = df[['customer_id', 'customer_name', 'segment', 'city', 'state', 'region', 'country', 'postal_code']].drop_duplicates()
# Таблица товаров
products = df[['product_id', 'product_name', 'category', 'sub_category']].drop_duplicates()
# Таблица заказов (факты продаж)
orders = df[['order_id', 'order_date', 'ship_date', 'ship_mode', 'customer_id', 'product_id', 'sales', 'quantity', 'discount', 'profit']]

# Создание временной БД
conn = sqlite3.connect(':memory:')
customers.to_sql('customers', conn, index=False, if_exists='replace')
products.to_sql('products', conn, index=False, if_exists='replace')
orders.to_sql('orders', conn, index=False, if_exists='replace')

#Запросы SQL
#Анализ продаж
#Сумма продаж по категориям и подкатегориям товаров
query = """
SELECT p.category, p.sub_category, SUM(o.sales) as total_sum
FROM orders o
JOIN products p
ON o.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY p.category, total_sum desc
"""
print("\n===== Сумма продаж по категориям и подкатегориям товаров =====")
result_category_sales = pd.read_sql(query, conn)
print(result_category_sales)

# Топ-5 продаваемых товаров
query = """
SELECT 
    p.product_name,
    SUM(o.quantity) AS total_quantity,
    SUM(o.sales) AS total_sales
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_sales DESC
LIMIT 5;
"""
print("\n===== Топ 5 самых продаваемых товаров =====")
result_top5 = pd.read_sql(query, conn)
print(result_top5)

# Убыточные товары в категории Furniture
query = """
SELECT 
    p.product_name,
    SUM(o.sales) AS total_sales,
    SUM(o.profit) AS total_profit
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE p.category = 'Furniture'
GROUP BY p.product_name
HAVING SUM(o.profit) < 0
ORDER BY total_profit ASC;
"""
print("\n===== Убыточные товары в категории Furniture =====")
result_furniture = pd.read_sql(query, conn)
print(result_furniture)

#Средняя стоимость заказа по сегментам, общая сумма заказов
# выручка по каждому сегменту
query = """
SELECT 
    c.segment,
    AVG(order_total) AS avg_order_value,
    SUM(order_total) AS total_sales,
    SUM(order_profit) AS total_profit
FROM (
    SELECT 
        o.order_id, 
        o.customer_id, 
        SUM(o.sales) AS order_total,
        SUM(o.profit) AS order_profit
    FROM orders o
    GROUP BY o.order_id, o.customer_id
) AS order_sums
JOIN customers c ON order_sums.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY total_sales DESC;
"""
print("\n===== Средняя стоимость заказа по сегментам, общая сумма заказов, выручка по каждому сегменту =====")
result_segment = pd.read_sql(query, conn)
print(result_segment)

# Сумма продаж и выручка по годам
query = """
SELECT 
    strftime('%Y', order_date) AS year,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit
FROM orders
GROUP BY year
ORDER BY year;
"""
print("\n===== Сумма продаж и выручка по годам =====")
result_year = pd.read_sql(query, conn)
print(result_year)

# Города с наибольшей выручкой по продажам
query = """
SELECT 
    c.city,
    SUM(o.sales) AS total_sales,
    SUM(o.profit) AS total_profit
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
ORDER BY total_sales DESC
LIMIT 10;
"""
print("\n===== Топ -10 городов с наибольшей выручкой по продажам =====")
result_city = pd.read_sql(query, conn)
print(result_city)

#Визуализация данных
#Сумма продаж по категориям товаров
categories = result_category_sales['category'] + " / " + result_category_sales['sub_category']
sales = result_category_sales['total_sum']
plt.barh(categories, sales, color='skyblue')
plt.xlabel("Продажи (Total Sales)")
plt.ylabel("Категория / Подкатегория")
plt.title("Сумма продаж по категориям и подкатегориям")
plt.tight_layout()
plt.show()

#Средняя стоимость заказов по сегментам
plt.bar(result_segment['segment'], result_segment['avg_order_value'], color='orange')
plt.xlabel("Сегмент")
plt.ylabel("Средняя стоимость заказа")
plt.title("Средняя стоимость заказа по сегментам")
plt.tight_layout()
plt.show()

#Сумма продаж и прибыль по годам
plt.plot(result_year['year'], result_year['total_sales'], marker='o', label='Продажи')
plt.plot(result_year['year'], result_year['total_profit'], marker='o', color='orange', label='Прибыль')
plt.xlabel("Год")
plt.ylabel("Сумма")
plt.title("Продажи и прибыль по годам")
plt.legend()
plt.tight_layout()
plt.show()