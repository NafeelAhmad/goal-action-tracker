import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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
        duration = (end_time - st.session_state.start_time).total_seconds() / 60.0
        
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
    # Convert duration to hours
    summary = df.groupby("category")["duration_minutes"].sum().reset_index()
    summary["Hours"] = (summary["duration_minutes"] / 60.0).round(2)
    
    # Display Key Metrics
    cat_a_hrs = summary[summary["category"].str.contains("Category A")]["Hours"].sum()
    cat_b_hrs = summary[summary["category"].str.contains("Category B")]["Hours"].sum()
    cat_c_hrs = summary[summary["category"].str.contains("Category C")]["Hours"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Cat A (Goal)", f"{cat_a_hrs} hrs")
    m2.metric("Cat B (Hold)", f"{cat_b_hrs} hrs")
    m3.metric("Cat C (Loss)", f"{cat_c_hrs} hrs")

    st.bar_chart(data=summary, x="category", y="Hours")
else:
    st.write("No tracked time recorded yet.")