import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.data_loader import load_schedule, load_enriched_players
from core.transfer_engine import load_state, get_transfer_budget_report
from core.scraper import post_match_sync

st.set_page_config(
    page_title="IPL 2026 Fantasy Team Builder",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        text-align: center;
        padding: 0.5rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .match-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def get_next_match(schedule_df):
    """Find the next upcoming match from the schedule."""
    today = pd.Timestamp(date.today())
    upcoming = schedule_df[schedule_df["Date"] >= today].sort_values("Date")
    if len(upcoming) > 0:
        return upcoming.iloc[0]
    # If all matches are past, return the last one
    return schedule_df.iloc[-1] if len(schedule_df) > 0 else None


def main():
    st.markdown('<div class="main-header">IPL 2026 Fantasy Team Builder</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Load data
    schedule = load_schedule()
    state = load_state()
    budget = get_transfer_budget_report()

    # Next match info
    next_match = get_next_match(schedule)

    # --- Season Dashboard ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Transfers Remaining",
            f"{budget['transfers_remaining']} / 160",
            delta=f"{budget['burn_rate']}/match avg",
            delta_color="inverse",
        )

    with col2:
        st.metric(
            "Boosters Left",
            f"{budget['boosters_remaining']} / 7",
        )

    with col3:
        st.metric(
            "Matches Played",
            f"{budget['matches_played']}",
            delta=f"{budget['matches_remaining']} remaining",
        )

    with col4:
        status_emoji = {"Surplus": "🟢", "On Track": "🟢", "Tight": "🟡", "Critical": "🔴"}.get(budget["status"], "⚪")
        st.metric(
            "Transfer Budget Status",
            f"{status_emoji} {budget['status']}",
            delta=f"{budget['base_rate']}/match avg",
        )

    st.markdown("---")

    # --- Next Match ---
    if next_match is not None:
        st.subheader("Next Match")
        mcol1, mcol2 = st.columns([2, 1])

        with mcol1:
            match_str = next_match.get("Match", "TBD")
            venue = next_match.get("Venue / City", "TBD")
            match_date = next_match.get("Date", "")
            match_num = int(next_match.get("Match #", 0))
            phase = next_match.get("Phase", "")

            st.markdown(f"""
            <div class="match-card">
                <h3>Match {match_num}: {match_str}</h3>
                <p><strong>Venue:</strong> {venue}</p>
                <p><strong>Date:</strong> {match_date.strftime('%A, %B %d, %Y') if hasattr(match_date, 'strftime') else match_date} | <strong>Phase:</strong> {int(phase) if pd.notna(phase) else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)

        with mcol2:
            if hasattr(match_date, 'date'):
                days_until = (match_date.date() - date.today()).days
                if days_until > 0:
                    st.metric("Days Until Match", days_until)
                elif days_until == 0:
                    st.metric("Match Day!", "TODAY")
                else:
                    st.metric("Match Status", "Completed")

        st.markdown("")

        # Quick action buttons
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            if st.button("Build Team for Next Match", type="primary", use_container_width=True):
                st.switch_page("pages/1_Team_Builder.py")
        with bcol2:
            if st.button("Manage Transfers", use_container_width=True):
                st.switch_page("pages/2_Transfer_Manager.py")
        with bcol3:
            if st.button("View Schedule", use_container_width=True):
                st.switch_page("pages/4_Schedule.py")

    st.markdown("---")

    # --- Post-Match Sync ---
    st.subheader("Post-Match Sync")
    st.caption("After a match ends, sync to update injury tracker and player form.")

    sync_col1, sync_col2, sync_col3 = st.columns(3)
    completed_matches = schedule[schedule["Date"] < pd.Timestamp(date.today())].sort_values("Date", ascending=False)

    if len(completed_matches) > 0:
        with sync_col1:
            last_match = completed_matches.iloc[0]
            st.info(f"Last completed: Match {int(last_match['Match #'])} — {last_match['Match']}")

        with sync_col2:
            if st.button("Sync Last Match", use_container_width=True):
                with st.spinner("Fetching match data..."):
                    result = post_match_sync(last_match["Team1"], last_match["Team2"])
                    if result["updates"]:
                        for update in result["updates"]:
                            st.success(update)
                    else:
                        st.info("No new updates found. Data may not be available yet.")
    else:
        st.info("No completed matches yet. Season starts March 28!")

    # --- Current Team Preview ---
    if state.get("current_team"):
        st.markdown("---")
        st.subheader("Your Current Team")
        team_names = state["current_team"]
        captain = state.get("captain", "")
        vc = state.get("vice_captain", "")

        display = []
        for name in team_names:
            marker = ""
            if name == captain:
                marker = " (C)"
            elif name == vc:
                marker = " (VC)"
            display.append(f"{name}{marker}")

        cols = st.columns(3)
        for i, name in enumerate(display):
            cols[i % 3].write(f"- {name}")

        st.caption(f"Credits used: {state.get('credits_used', 0)} / 100")

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### Navigation")
        st.page_link("app.py", label="Home", icon="🏠")
        st.page_link("pages/1_Team_Builder.py", label="Team Builder", icon="🏏")
        st.page_link("pages/2_Transfer_Manager.py", label="Transfer Manager", icon="🔄")
        st.page_link("pages/3_Player_Stats.py", label="Player Stats", icon="📊")
        st.page_link("pages/4_Schedule.py", label="Schedule", icon="📅")
        st.page_link("pages/5_History.py", label="History", icon="📜")

        st.markdown("---")
        st.markdown("### Season Info")
        st.markdown(f"**Transfers:** {budget['transfers_remaining']} left")
        st.markdown(f"**Boosters:** {budget['boosters_remaining']} left")
        st.markdown(f"**Status:** {budget['status']}")


if __name__ == "__main__":
    main()
