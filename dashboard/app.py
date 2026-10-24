
from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

st.set_page_config(
    page_title="DataPulse | Data Platform Monitor",
    page_icon="📊",
    layout="wide",
)

st.title("DataPulse")
st.caption("Olist Data Engineering Platform | Pipeline Monitoring")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "olist"),
    "user": os.getenv("DB_USER", "olist_user"),
    "password": os.getenv("DB_PASSWORD", ""),
    "connect_timeout": 5,
}


def query_dataframe(sql):
    with psycopg.connect(**DB_CONFIG) as conn:
        return pd.read_sql_query(sql, conn)


@st.cache_data(ttl=60)
def get_sales():
    return query_dataframe("""
        SELECT
            order_date,
            order_status,
            order_count,
            order_item_count,
            customer_count,
            gross_item_value,
            freight_value,
            item_total_revenue,
            average_item_price
        FROM analytics.mart_daily_sales
        ORDER BY order_date
    """)


@st.cache_data(ttl=60)
def get_table_counts():
    return query_dataframe("""
        SELECT 'Raw orders' AS table_name,
               COUNT(*) AS row_count
        FROM raw.olist_orders_dataset

        UNION ALL

        SELECT 'Staging orders', COUNT(*)
        FROM analytics.stg_orders

        UNION ALL

        SELECT 'Order item facts', COUNT(*)
        FROM analytics.fact_order_items
    """)

@st.cache_data(ttl=60)
def get_corruption_report():
    path = ROOT_DIR / "docs" / "corruption_test_report.csv"

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)

try:
    sales = get_sales()
    counts = get_table_counts()

    if sales.empty:
        st.warning("The daily sales mart contains no rows yet.")
    else:
        total_orders = int(sales["order_count"].sum())
        total_items = int(sales["order_item_count"].sum())
        total_value = float(sales["gross_item_value"].sum())
        total_freight = float(sales["freight_value"].sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Orders", f"{total_orders:,}")
        c2.metric("Order items", f"{total_items:,}")
        c3.metric("Item value", f"R$ {total_value:,.2f}")
        c4.metric("Freight", f"R$ {total_freight:,.2f}")

        st.subheader("Daily sales trend")

        daily = (
            sales.groupby("order_date", as_index=False)
            .agg(
                item_value=("gross_item_value", "sum"),
                freight=("freight_value", "sum"),
                orders=("order_count", "sum"),
            )
        )

        fig = px.line(
            daily,
            x="order_date",
            y="item_value",
            title="Daily item value",
            labels={
                "order_date": "Order date",
                "item_value": "Item value (BRL)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sales by order status")

        by_status = (
            sales.groupby("order_status", as_index=False)
            .agg(
                orders=("order_count", "sum"),
                item_value=("gross_item_value", "sum"),
            )
        )

        st.dataframe(by_status, use_container_width=True)

    st.subheader("Warehouse row counts")
    st.dataframe(counts, use_container_width=True)

    st.caption("Database metrics refresh every 60 seconds.")
    st.subheader("Data Quality Test Results")

    quality_report = get_corruption_report()

    if quality_report.empty:
        st.info(
            "No corruption test report found. "
            "Run python -m src.corruption_tests first."
        )
    else:
        passed = int(
            (quality_report["status"] == "PASS").sum()
        )
        failed = int(
            (quality_report["status"] == "FAIL").sum()
        )

        q1, q2 = st.columns(2)
        q1.metric("Checks passed", passed)
        q2.metric("Checks failed", failed)

        st.dataframe(
            quality_report,
            use_container_width=True,
            hide_index=True,
        )


except Exception as exc:
    st.error("Could not load dashboard data from PostgreSQL.")
    st.code(str(exc))
    st.info(
        "Check Docker, the database connection settings, "
        "and whether the required analytics tables exist."
    )



