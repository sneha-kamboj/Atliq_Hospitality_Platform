import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(page_title="AtliQ Hospitality Dashboard", layout="wide")
st.title("🏨 AtliQ Hospitality Enterprise Production Platform")
st.markdown("---")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "atliq_database.db")

@st.cache_data
def run_data_pipeline():
   
    df_hotels = pd.read_csv(os.path.join(DATA_DIR, 'dim_hotels.csv'))
    df_rooms = pd.read_csv(os.path.join(DATA_DIR, 'dim_rooms.csv'))
    df_bookings = pd.read_csv(os.path.join(DATA_DIR, 'fact_bookings.csv'))
    
    df_bookings = df_bookings[df_bookings['no_guests'] > 0]
    df_bookings = df_bookings[df_bookings['revenue_generated'] <= 500000]
    
   
    conn = sqlite3.connect(DB_PATH)
    df_hotels.to_sql('dim_hotels', conn, if_exists='replace', index=False)
    df_rooms.to_sql('dim_rooms', conn, if_exists='replace', index=False)
    df_bookings.to_sql('fact_bookings', conn, if_exists='replace', index=False)
    conn.close()
    
    df_mrg = pd.merge(df_bookings, df_hotels, on='property_id')
    df_mrg = pd.merge(df_mrg, df_rooms, left_on='room_category', right_on='room_id')
    return df_mrg

try:
    df = run_data_pipeline()
    st.sidebar.success("✅ Engine Online: Data Pipeline & SQL Stack Active!")
except Exception as e:
    st.error(f"❌ Error: Kya aapne saari CSV files ko 'data' folder ke andar dala hai? Check karein. Error details: {e}")
    st.stop()


st.sidebar.header("Dashboard Filters")
selected_city = st.sidebar.selectbox("Choose a City to Analyze", ["All Cities"] + list(df['city'].unique()))


if selected_city != "All Cities":
    df = df[df['city'] == selected_city]

total_revenue = df['revenue_realized'].sum()
avg_rating = df['ratings_given'].mean()
total_bookings = len(df)

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue Realized", f"₹ {total_revenue:,.2f}")
col2.metric("⭐ Avg Customer Rating", f"{avg_rating:.2f} / 5")
col3.metric("📅 Total Bookings", f"{total_bookings:,}")
st.markdown("---")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Platform-wise Revenue Distribution")
    platform_rev = df.groupby('booking_platform')['revenue_realized'].sum().reset_index()
    fig1 = px.pie(platform_rev, values='revenue_realized', names='booking_platform', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    st.subheader("Property Performance Analysis")
    hotel_rev = df.groupby('property_name')['revenue_realized'].sum().reset_index()
    fig2 = px.bar(hotel_rev, x='property_name', y='revenue_realized', color='property_name', text_auto='.2s')
    st.plotly_chart(fig2, use_container_width=True)
