import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from datetime import timedelta


def format_seconds(total_seconds):
    if not total_seconds or total_seconds <= 0:
        return "00:00:00:00"
    
    total_sec = int(total_seconds)
    
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    
    # Strict Format: DD:HH:MM:SS
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    
st.set_page_config(page_title="Action Tracker", page_icon="⚡", layout="centered")

# --- DATABASE SETUP ---
# --- DATABASE SETUP ---
conn = sqlite3.connect("tracker.db", check_same_thread=False)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_seconds REAL
    )
""")
conn.commit()

# Self-healing check: Ensure duration_seconds column exists in existing DB
cursor.execute("PRAGMA table_info(sessions)")
columns = [col[1] for col in cursor.fetchall()]

if "duration_seconds" not in columns:
    if "duration_minutes" in columns:
        cursor.execute("ALTER TABLE sessions RENAME COLUMN duration_minutes TO duration_seconds")
    else:
        cursor.execute("ALTER TABLE sessions ADD COLUMN duration_seconds REAL")
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
        duration_sec = (end_time - st.session_state.start_time).total_seconds()
        
        cursor.execute(
            "INSERT INTO sessions (category, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
            (
                st.session_state.active_category,
                st.session_state.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                round(duration_sec, 2)
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
    # Ensure duration_seconds column is used directly without multiplying by 60
    if "duration_seconds" in df.columns:
        df["total_sec"] = df["duration_seconds"].fillna(0)
    else:
        df["total_sec"] = df["duration_minutes"].fillna(0)

    # Parse start_time to date string (YYYY-MM-DD)
    df["start_dt"] = pd.to_datetime(df["start_time"])
    df["date"] = df["start_dt"].dt.strftime("%Y-%m-%d")

    # Filter Options: Today, Last 7 Days, All Time
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

    # Display Top Metrics for Selected Range
    cat_a_sec = filtered_df[filtered_df["category"].str.contains("Category A")]["total_sec"].sum()
    cat_b_sec = filtered_df[filtered_df["category"].str.contains("Category B")]["total_sec"].sum()
    cat_c_sec = filtered_df[filtered_df["category"].str.contains("Category C")]["total_sec"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Cat A (Goal)", format_seconds(cat_a_sec))
    m2.metric("Cat B (Hold)", format_seconds(cat_b_sec))
    m3.metric("Cat C (Loss)", format_seconds(cat_c_sec))

    # --- DAILY BREAKDOWN TABLE & CHART ---
    st.markdown("### 📆 Day-by-Day Breakdown")
    daily_summary = filtered_df.groupby(["date", "category"])["total_sec"].sum().reset_index()
    daily_summary["Time Spent (DD:HH:MM:SS)"] = daily_summary["total_sec"].apply(format_seconds)
    daily_summary["Hours"] = (daily_summary["total_sec"] / 3600.0).round(2)

    # Pivot table so dates are rows and categories are columns
    pivot_df = daily_summary.pivot(index="date", columns="category", values="Hours").fillna(0)
    
    # Display Daily Stacked Bar Chart across the week
    st.bar_chart(pivot_df)
    st.dataframe(daily_summary[["date", "category", "Time Spent (DD:HH:MM:SS)"]], use_container_width=True)
else:
    st.write("No tracked time recorded yet.")
