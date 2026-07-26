import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def format_seconds(total_seconds):
    if not total_seconds or total_seconds <= 0:
        return "00:00:00:00"
    
    total_sec = int(total_seconds)
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"

st.set_page_config(page_title="Action Tracker", page_icon="⚡", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect("tracker.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Main sessions table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_seconds REAL
    )
""")

# 2. Table to store currently active state across mobile tab switches
cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        category TEXT,
        start_time TEXT
    )
""")
conn.commit()

# --- DATABASE STATE FUNCTIONS ---
def get_active_state():
    cursor.execute("SELECT category, start_time FROM active_state WHERE id = 1")
    row = cursor.fetchone()
    if row:
        return row[0], datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    return None, None

def set_active_state(category, start_dt):
    dt_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT OR REPLACE INTO active_state (id, category, start_time) VALUES (1, ?, ?)",
        (category, dt_str)
    )
    conn.commit()

def clear_active_state():
    cursor.execute("DELETE FROM active_state WHERE id = 1")
    conn.commit()

def stop_timer():
    active_cat, start_dt = get_active_state()
    if active_Progressivend start_dt:
        end_dt = datetime.now()
        duration_sec = (end_dt - start_dt).total_seconds()
        
        cursor.execute(
            "INSERT INTO sessions (category, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
            (
                active_cat,
                start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                round(duration_sec, 2)
            )
        )
        conn.commit()
        clear_active_state()

def start_timer(category):
    # Stop existing active timer if running
    stop_timer()
    # Save new start timestamp instantly to database
    set_active_state(category, datetime.now())

# --- UI HEADER ---
st.title("⚡ Action & Goal Tracker")

active_category, active_start_time = get_active_state()

# --- ACTIVE STATUS ---
if active_category and active_start_time:
    elapsed_sec = (datetime.now() - active_start_time).total_seconds()
    st.info(f"🟢 **Currently Active:** {active_category}\n\n⏱️ **Running Time:** {format_seconds(elapsed_sec)}")
    
    if st.button("⏹️ Stop / Pause Current Activity", use_container_width=True):
        stop_timer()
        st.rerun()
else:
    st.warning("⏸️ No active timer running")

st.divider()

# --- CATEGORY BUTTONS ---
st.subheader("Switch Activity")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 Progressive\n(Agentic AI)", use_container_width=True):
        start_timer("Category A (Working Towards Goal)")
        st.rerun()

with col2:
    if st.button("⏸️ Pause\n(Office/Hold)", use_container_width=True):
        start_timer("Category B (Put On Hold)")
        st.rerun()

with col3:
    if st.button("🛑 Penalty\n(Distractions)", use_container_width=True):
        start_timer("Category C (Negative/Distraction)")
        st.rerun()

st.divider()

# --- DASHBOARD & ANALYTICS ---
st.subheader("📊 Time Summary")
df = pd.read_sql_query("SELECT * FROM sessions", conn)

if not df.empty:
    if "duration_seconds" in df.columns:
        df["total_sec"] = df["duration_seconds"].fillna(0)
    else:
        df["total_sec"] = df["duration_minutes"].fillna(0)

    df["start_dt"] = pd.to_datetime(df["start_time"])
    df["date"] = df["start_dt"].dt.strftime("%Y-%m-%d")

    st.markdown("### 🗓️ View Range")
    time_filter = st.radio("Select View:", ["Today", "Last 7 Days", "All Time"], horizontal=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    if time_filter == "Today":
        filtered_df = df[df["date"] == today_str]
    elif time_filter == "Last 7 Days":
        filtered_df = df[df["date"] >= seven_days_ago]
    else:
        filtered_df = df

    cat_a_sec = filtered_df[filtered_df["category"].str.contains("Category A")]["total_sec"].sum()
    cat_b_sec = filtered_df[filtered_df["category"].str.contains("Category B")]["total_sec"].sum()
    cat_c_sec = filtered_df[filtered_df["category"].str.contains("Category C")]["total_sec"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Progressive (Goal)", format_seconds(cat_a_sec))
    m2.metric("Pause (Hold)", format_seconds(cat_b_sec))
    m3.metric("Penalty (Loss)", format_seconds(cat_c_sec))

    st.markdown("### 📆 Day-by-Day Breakdown")
    daily_summary = filtered_df.groupby(["date", "category"])["total_sec"].sum().reset_index()
    daily_summary["Time Spent (DD:HH:MM:SS)"] = daily_summary["total_sec"].apply(format_seconds)
    daily_summary["Hours"] = (daily_summary["total_sec"] / 3600.0).round(2)

    pivot_df = daily_summary.pivot(index="date", columns="category", values="Hours").fillna(0)
    st.bar_chart(pivot_df)
    st.dataframe(daily_summary[["date", "category", "Time Spent (DD:HH:MM:SS)"]], use_container_width=True)
else:
    st.write("No tracked time recorded yet.")
