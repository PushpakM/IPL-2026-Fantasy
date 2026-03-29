import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data_loader import load_schedule

st.set_page_config(page_title="Schedule | IPL 2026", page_icon="📅", layout="wide")

st.title("IPL 2026 Schedule")


@st.cache_data(ttl=600)
def get_schedule():
    return load_schedule()


schedule_df = get_schedule()
today = pd.Timestamp(date.today())

# --- Phase Filter ---
phases = ["All"] + sorted(schedule_df["Phase"].dropna().unique().astype(int).astype(str).tolist())
selected_phase = st.selectbox("Filter by Phase", phases)

if selected_phase != "All":
    display_df = schedule_df[schedule_df["Phase"] == int(selected_phase)].copy()
else:
    display_df = schedule_df.copy()

# --- Stats ---
total = len(schedule_df)
completed = len(schedule_df[schedule_df["Date"] < today])
upcoming_count = total - completed

scol1, scol2, scol3, scol4 = st.columns(4)
with scol1:
    st.metric("Total Matches", total)
with scol2:
    st.metric("Completed", completed)
with scol3:
    st.metric("Upcoming", upcoming_count)
with scol4:
    current_phase = schedule_df[schedule_df["Date"] >= today]["Phase"].dropna().min()
    st.metric("Current Phase", int(current_phase) if pd.notna(current_phase) else "Done")

st.markdown("---")

# --- Schedule Table ---
def highlight_match(row):
    """Highlight today's match and color by phase."""
    if hasattr(row["Date"], "date") and row["Date"].date() == date.today():
        return ["background-color: #fff3cd"] * len(row)  # Yellow for today
    elif hasattr(row["Date"], "date") and row["Date"].date() < date.today():
        return ["color: #6c757d"] * len(row)  # Gray for past
    return [""] * len(row)


# Prepare display
display_df = display_df.copy()
display_df["Date Display"] = display_df["Date"].apply(
    lambda d: d.strftime("%a, %b %d") if hasattr(d, "strftime") else str(d)
)

show_cols = {
    "Match #": "Match #",
    "Date Display": "Date",
    "Match": "Match",
    "VenueName": "Venue",
    "Time (IST)": "Time",
    "Phase": "Phase",
}

table_df = display_df[list(show_cols.keys())].rename(columns=show_cols)
table_df["Phase"] = table_df["Phase"].apply(lambda x: int(x) if pd.notna(x) else "")
table_df["Match #"] = table_df["Match #"].astype(int)

# Mark today and past matches
def get_status(idx):
    row = display_df.iloc[idx]
    if hasattr(row["Date"], "date"):
        if row["Date"].date() == date.today():
            return "TODAY"
        elif row["Date"].date() < date.today():
            return "Done"
    return ""


table_df["Status"] = [get_status(i) for i in range(len(table_df))]

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    height=700,
)

# --- Phase Breakdown ---
st.markdown("---")
st.subheader("Phase Breakdown")

phase_summary = schedule_df.groupby("Phase").agg(
    Matches=("Match #", "count"),
    Start=("Date", "min"),
    End=("Date", "max"),
).reset_index()

phase_summary["Phase"] = phase_summary["Phase"].astype(int)
phase_summary["Start"] = phase_summary["Start"].apply(lambda d: d.strftime("%b %d") if hasattr(d, "strftime") else "")
phase_summary["End"] = phase_summary["End"].apply(lambda d: d.strftime("%b %d") if hasattr(d, "strftime") else "")

st.dataframe(phase_summary, use_container_width=True, hide_index=True)
