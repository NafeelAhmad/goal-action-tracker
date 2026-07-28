import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# Define Timezone as IST
IST = ZoneInfo("Asia/Kolkata")

def get_ist_now():
    return datetime.now(IST)

def format_seconds(total_seconds):
    if not total_seconds or total_seconds <= 0:
        return "00:00:00"
    
    total_sec = int(total_seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

st.set_page_config(page_title="Action Tracker", page_icon="⚡", layout="centered")

# --- VIEWER MODE CHECK ---
query_params = st.query_params
is_viewer_mode = query_params.get("mode") == "viewer"

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

# 2. Table to store active timer state
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
        dt = datetime.fromisoformat(row[1])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return row[0], dt
    return None, None

def set_active_state(category, start_dt):
    dt_str = start_dt.isoformat()
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
    if active_cat and start_dt:
        end_dt = get_ist_now()
        duration_sec = (end_dt - start_dt).total_seconds()
        
        cursor.execute(
            "INSERT INTO sessions (category, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
            (
                active_cat,
                start_dt.isoformat(),
                end_dt.isoformat(),
                round(duration_sec, 2)
            )
        )
        conn.commit()
        clear_active_state()

def start_timer(category):
    stop_timer()
    set_active_state(category, get_ist_now())

# --- UI HEADER ---
st.title("⚡ Action & Goal Tracker")

if is_viewer_mode:
    st.info("👁️ **Viewer Mode Active:** Controls, editing, and timer buttons are hidden.")

# --- ACTIVE STATUS (Hidden in Viewer Mode) ---
if not is_viewer_mode:
    active_category, active_start_time = get_active_state()

    if active_category and active_start_time:
        elapsed_sec = (get_ist_now() - active_start_time).total_seconds()
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
st.subheader("📊 Time Summary (IST)")
df = pd.read_sql_query("SELECT * FROM sessions", conn)

if not df.empty:
    df["total_sec"] = df["duration_seconds"].fillna(0)
    
    # Parse dates and convert to IST
    def parse_to_ist(val):
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(IST)

    df["start_dt"] = df["start_time"].apply(parse_to_ist)
    df["date"] = df["start_dt"].dt.strftime("%Y-%m-%d")

    st.markdown("### 🗓️ View Range")
    time_filter = st.radio("Select View:", ["Today", "Last 7 Days", "All Time"], horizontal=True)

    today_str = get_ist_now().strftime("%Y-%m-%d")
    seven_days_ago = (get_ist_now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")

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
    daily_summary["Time Spent (HH:MM:SS)"] = daily_summary["total_sec"].apply(format_seconds)
    daily_summary["Hours"] = (daily_summary["total_sec"] / 3600.0).round(2)

    pivot_df = daily_summary.pivot(index="date", columns="category", values="Hours").fillna(0)
    st.bar_chart(pivot_df)
    st.dataframe(daily_summary[["date", "category", "Time Spent (HH:MM:SS)"]], use_container_width=True)

    # --- SESSION EDITING & REALLOCATION (Admin Only) ---
    if not is_viewer_mode:
        st.divider()
        with st.expander("✏️ Edit & Reallocate Session Time"):
            st.write("Correct mistakes if you left a category running too long:")
            
            # Form to select session
            session_options = df.sort_values(by="id", ascending=False)
            session_options["display"] = session_options.apply(
                lambda r: f"ID #{r['id']} | {r['date']} | {r['category'][:12]}... | {format_seconds(r['total_sec'])}", axis=1
            )
            
            selected_session_str = st.selectbox("Select Session to Adjust:", session_options["display"].tolist())
            selected_id = int(selected_session_str.split("#")[1].split(" ")[0])
            
            target_row = df[df["id"] == selected_id].iloc[0]
            st.info(f"**Current Duration:** {format_seconds(target_row['total_sec'])} in **{target_row['category']}**")

            categories_list = [
                "Category A (Working Towards Goal)",
                "Category B (Put On Hold)",
                "Category C (Negative/Distraction)"
            ]
            
            reallocate_to = st.selectbox("Reallocate time to:", [c for c in categories_list if c != target_row['category']])
            
            max_minutes = float(target_row['total_sec'] / 60.0)
            minutes_to_move = st.number_input("Minutes to move to new category:", min_value=1.0, max_value=max_minutes, value=min(60.0, max_minutes))

            if st.button("🔄 Move & Reallocate Time"):
                seconds_to_move = minutes_to_move * 60.0
                new_orig_sec = max(0.0, target_row['total_sec'] - seconds_to_move)

                # Update original session duration
                cursor.execute("UPDATE sessions SET duration_seconds = ? WHERE id = ?", (new_orig_sec, selected_id))

                # Insert new reallocated session log
                cursor.execute(
                    "INSERT INTO sessions (category, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
                    (reallocate_to, target_row['start_time'], target_row['end_time'], seconds_to_move)
                )
                conn.commit()
                st.success(f"Successfully moved {minutes_to_move} mins from {target_row['category']} to {reallocate_to}!")
                st.rerun()

else:
    st.write("No tracked time recorded yet.")
