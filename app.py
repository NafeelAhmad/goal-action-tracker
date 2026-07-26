import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from datetime import timedelta

def format_seconds(total_seconds):
    if not total_seconds or total_seconds <= 0:
        return "00:00:00:00"
    
    td = timedelta(seconds=int(total_seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    
st.set_page_config(page_title="Action Tracker", page_icon="⚡", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect("tracker.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_minutes REAL
    )
""")
conn.commit()

# --- APP STATE ---
if "active_category" not in st.session_state:
    st.session_state.active_category = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- FUNCTIONS ---
def start_timer(category):
    # Stop existing timer if running
    if st.session_state.active_category:
        stop_timer()
    st.session_state.active_category = category
    st.session_state.start_time = datetime.now()

def stop_timer():
    if st.session_state.active_category and st.session_state.start_time:
        end_time = datetime.now()
        duration = (end_time - st.session_state.start_time).total_seconds()
        
        cursor.execute(
            "INSERT INTO sessions (category, start_time, end_time, duration_minutes) VALUES (?, ?, ?, ?)",
            (
                st.session_state.active_category,
                st.session_state.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                round(duration, 2)
            )
        )
        conn.commit()
    st.session_state.active_category = None
    st.session_state.start_time = None

# --- UI HEADER ---
st.title("⚡ Action & Goal Tracker")

# --- ACTIVE STATUS ---
if st.session_state.active_category:
    st.info(f"🟢 **Currently Active:** {st.session_state.active_category}")
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
    if st.button("🚀 Cat A\n(Agentic AI)", use_container_width=True):
        start_timer("Category A (Working Towards Goal)")
        st.rerun()

with col2:
    if st.button("⏸️ Cat B\n(Office/Hold)", use_container_width=True):
        start_timer("Category B (Put On Hold)")
        st.rerun()

with col3:
    if st.button("🛑 Cat C\n(Distractions)", use_container_width=True):
        start_timer("Category C (Negative/Distraction)")
        st.rerun()

st.divider()

# --- DASHBOARD & ANALYTICS ---
st.subheader("📊 Time Summary")
df = pd.read_sql_query("SELECT * FROM sessions", conn)

if not df.empty:
    # Handles both seconds or legacy minutes
    if "duration_seconds" in df.columns:
        df["total_sec"] = df["duration_seconds"].fillna(0)
    else:
        df["total_sec"] = df["duration_minutes"].fillna(0) * 60

    # Calculate exact totals in seconds
    cat_a_sec = df[df["category"].str.contains("Category A")]["total_sec"].sum()
    cat_b_sec = df[df["category"].str.contains("Category B")]["total_sec"].sum()
    cat_c_sec = df[df["category"].str.contains("Category C")]["total_sec"].sum()
    
    # Display formatted metric cards: DD:HH:MM:SS
    m1, m2, m3 = st.columns(3)
    m1.metric("Cat A (Goal)", format_seconds(cat_a_sec))
    m2.metric("Cat B (Hold)", format_seconds(cat_b_sec))
    m3.metric("Cat C (Loss)", format_seconds(cat_c_sec))

    # Data Table displaying DD:HH:MM:SS format
    summary = df.groupby("category")["total_sec"].sum().reset_index()
    summary["Time Spent (DD:HH:MM:SS)"] = summary["total_sec"].apply(format_seconds)
    summary["Hours"] = (summary["total_sec"] / 3600.0).round(2)
    
    st.dataframe(summary[["category", "Time Spent (DD:HH:MM:SS)"]], use_container_width=True)
    st.bar_chart(data=summary, x="category", y="Hours")
