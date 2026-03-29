import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data_loader import load_enriched_players
from core.scorer import estimate_fantasy_points, points_per_credit

st.set_page_config(page_title="Player Stats | IPL 2026", page_icon="📊", layout="wide")

st.title("Player Stats")


@st.cache_data(ttl=300)
def get_players():
    return load_enriched_players()


players_df = get_players()

# --- Filters ---
st.subheader("Filters")
fcol1, fcol2, fcol3, fcol4 = st.columns(4)

with fcol1:
    teams = ["All"] + sorted(players_df["Team"].unique().tolist())
    selected_team = st.selectbox("Team", teams)

with fcol2:
    roles = ["All"] + sorted(players_df["Role"].unique().tolist())
    selected_role = st.selectbox("Role", roles)

with fcol3:
    tiers = ["All"] + sorted(players_df["Performance Tier"].dropna().unique().tolist())
    selected_tier = st.selectbox("Performance Tier", tiers)

with fcol4:
    availability = st.selectbox("Availability", ["All", "Available Only", "Injured/Unavailable"])

# Search
search = st.text_input("Search by player name")

# Apply filters
filtered = players_df.copy()

if selected_team != "All":
    filtered = filtered[filtered["Team"] == selected_team]
if selected_role != "All":
    filtered = filtered[filtered["Role"] == selected_role]
if selected_tier != "All":
    filtered = filtered[filtered["Performance Tier"] == selected_tier]
if availability == "Available Only":
    filtered = filtered[filtered["IsAvailable"]]
elif availability == "Injured/Unavailable":
    filtered = filtered[~filtered["IsAvailable"]]
if search:
    filtered = filtered[filtered["Player Name"].str.contains(search, case=False, na=False)]

st.markdown(f"**Showing {len(filtered)} players**")

# --- Player Table ---
display_cols = ["Player Name", "Team", "Role", "RoleCode", "Performance Tier", "Credits", "Availability", "Notes"]
available_cols = [c for c in display_cols if c in filtered.columns]

# Add estimated points (using generic venue)
filtered = filtered.copy()
filtered["Est. Points"] = filtered.apply(
    lambda row: estimate_fantasy_points(row.to_dict(), ""), axis=1
)
filtered["Pts/Credit"] = filtered.apply(
    lambda row: points_per_credit(row.to_dict(), ""), axis=1
)

# Sort options
sort_by = st.selectbox("Sort by", ["Est. Points", "Credits", "Pts/Credit", "Player Name", "Team"])
ascending = sort_by == "Player Name"
filtered = filtered.sort_values(sort_by, ascending=ascending)

# Display
show_cols = available_cols + ["Est. Points", "Pts/Credit"]
st.dataframe(
    filtered[show_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    height=600,
)

# --- Team Breakdown ---
st.markdown("---")
st.subheader("Team Breakdown")

tcol1, tcol2 = st.columns(2)

with tcol1:
    st.markdown("**Players per Team**")
    team_counts = players_df.groupby("Team").size().reset_index(name="Count")
    st.dataframe(team_counts, use_container_width=True, hide_index=True)

with tcol2:
    st.markdown("**Players per Role**")
    role_counts = players_df.groupby("Role").size().reset_index(name="Count")
    st.dataframe(role_counts, use_container_width=True, hide_index=True)

# Tier distribution
st.markdown("**Performance Tier Distribution**")
tier_team = players_df.groupby(["Team", "Performance Tier"]).size().unstack(fill_value=0)
st.dataframe(tier_team, use_container_width=True)
