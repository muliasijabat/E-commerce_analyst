import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from PIL import Image
import plotly.express as px
from babel.numbers import format_currency
sns.set(style='dark')

# Helper function untuk menghasilkan data bulanan
def monthly_orders_df(df):
    df['order_purchase_timestamp'] = df['order_purchase_timestamp'].dt.to_period('M')
    monthly_orders_df = df.groupby('order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    }).reset_index()

    monthly_orders_df.rename(columns={
        'order_id': 'order_count',
        'total_price': 'revenue'
    }, inplace=True)

    return monthly_orders_df

def sum_order_items_df(df):
    sum_order_items_df = df.groupby("category_name").order_item_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def bycity_df(df):
    bystate_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)

    return bystate_df

def rfm_data_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.to_timestamp().dt.date
    recent_date = df["order_purchase_timestamp"].dt.to_timestamp().dt.date.max()

    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

#import Dataset
all_df = pd.read_csv("main_data.csv")

#ubah tipe data
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Membuat Komponen Filter
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()
 
with st.sidebar:
   # Menambahkan logo perusahaan
    img = Image.open('assets/cake.png')
    st.sidebar.image(img)
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

#menyimpan data yang difilter kedalam main_df
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

# Memanggil helper function
monthly_orders_data = monthly_orders_df(main_df)
order_item_data = sum_order_items_df(main_df)
bycity_data = bycity_df(main_df)
bystate_data = bystate_df(main_df)
rfm_data = rfm_data_df(main_df)

# Melengkapi Dashboard dengan Berbagai Visualisasi Data
st.title('Analisis RFM')
st.subheader('Hasil Analisis RFM Pelanggan')

st.subheader('Daily Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = monthly_orders_data.order_count.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_revenue = format_currency(monthly_orders_data.revenue.sum(), "Real", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)
 
fig, ax = plt.subplots(figsize=(16, 8))
monthly_orders_data["order_purchase_timestamp"] = monthly_orders_data["order_purchase_timestamp"].dt.to_timestamp().dt.date
ax.plot(
    monthly_orders_data["order_purchase_timestamp"],
    monthly_orders_data["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

# Best & Worst Performing Product
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

# Memanggil fungsi sum_order_items_df untuk mendapatkan DataFrame
sum_order_items_data = sum_order_items_df(main_df)

# Membuat plot untuk 10 produk terbaik
sns.barplot(x="order_item_id", y="category_name", data=sum_order_items_data.head(5), palette=colors, ax=ax[0])

ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

# Menggunakan .sort_values() pada DataFrame untuk 5 produk terburuk
sns.barplot(x="order_item_id", y="category_name", data=sum_order_items_data.sort_values(by="order_item_id", ascending=True).head(5), palette=colors, ax=ax[1])

ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)


# Visualisasi Demografi
# City
st.title("Number of Customer by City")

customer_city = all_df.groupby('customer_city')['customer_id'].count().reset_index()
customer_city.rename(columns={'customer_id': 'customer_count'}, inplace=True)
top_10_cities = customer_city.sort_values(by='customer_count', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
# Create the bar plot with Seaborn
sns.barplot(
    x="customer_count",
    y="customer_city",
    data=top_10_cities.sort_values(by="customer_count", ascending=False),
    palette=colors
)

plt.title("Number of Customer by City", loc="center", fontsize=15)
plt.ylabel(None)
plt.xlabel(None)
plt.tick_params(axis='y', labelsize=12)

# Display the Matplotlib figure using Streamlit
st.pyplot(fig)

# State
st.title("Number of Customer by State")

customer_states = all_df.groupby('customer_state')['customer_id'].count().reset_index()
customer_states.rename(columns={'customer_id': 'customer_count'}, inplace=True)
top_10_states = customer_states.sort_values(by='customer_count', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
# Create the bar plot with Seaborn
sns.barplot(
    x="customer_count",
    y="customer_state",
    data=top_10_states.sort_values(by="customer_count", ascending=False),
    palette=colors
)

plt.title("Number of Customer by State", loc="center", fontsize=15)
plt.ylabel(None)
plt.xlabel(None)
plt.tick_params(axis='y', labelsize=12)

# Display the Matplotlib figure using Streamlit
st.pyplot(fig)

# Analisa RFM
st.subheader("Best Customer Based on RFM Parameters")
rfm_data = rfm_data_df(main_df)
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_data.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_data.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_data.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)
 
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
 
sns.barplot(y="recency", x="customer_id", data=rfm_data.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
 
sns.barplot(y="frequency", x="customer_id", data=rfm_data.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
 
sns.barplot(y="monetary", x="customer_id", data=rfm_data.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
 
st.pyplot(fig)