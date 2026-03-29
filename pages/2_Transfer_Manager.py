import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data_loader import load_enriched_players, load_schedule
from core.transfer_engine import (
    load_state, get_transfer_budget_report, recommend_transfers,
    recommend_captain_vc, apply_transfers, change_captain_vc,
    use_booster, load_transfer_log, BOOSTER_TYPES,
    get_squad_health_report, TOTAL_SEASON_MATCHES, TOTAL_LEAGUE_TRANSFERS,
)
from core.scraper import get_playing_xi_cached
from core.scorer import estimate_fantasy_points

st.set_page_config(page_title="Transfer Manager | IPL 2026", page_icon="🔄", layout="wide")

st.title("Transfer Manager — Smart Budget Engine")
st.caption("160 transfers for 70 matches. Schedule-aware dynamic budgeting. Every transfer must count.")


@st.cache_data(ttl=300)
def get_data():
    return load_enriched_players(), load_schedule()


players_df, schedule_df = get_data()
state = load_state()
budget = get_transfer_budget_report()

# --- Transfer Budget Dashboard ---
st.subheader("Season Budget Overview")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Used", budget["transfers_used"])
with col2:
    st.metric("Remaining", budget["transfers_remaining"])
with col3:
    st.metric("Avg Rate", f"{budget['burn_rate']}/match")
with col4:
    st.metric("Base Rate", f"{budget['base_rate']}/match", help="transfers_remaining / matches_left")
with col5:
    colors = {"Surplus": "🟢", "On Track": "🟢", "Tight": "🟡", "Critical": "🔴"}
    st.metric("Forecast", f"{colors.get(budget['status'], '⚪')} {budget['status']}")

pct = budget["transfers_used"] / TOTAL_LEAGUE_TRANSFERS
st.progress(min(pct, 1.0), text=f"{budget['transfers_used']}/{TOTAL_LEAGUE_TRANSFERS} transfers | {budget['matches_played']}/{TOTAL_SEASON_MATCHES} matches | Projected end: {budget['projected_surplus']:+d} surplus")

st.markdown("---")

# --- Squad Health Report ---
today = pd.Timestamp(date.today())
upcoming = schedule_df[schedule_df["Date"] >= today].sort_values("Date").head(2)

if state.get("current_team"):
    current_team_data = []
    for name in state["current_team"]:
        match_data = players_df[players_df["Player Name"] == name]
        if len(match_data) > 0:
            current_team_data.append(match_data.iloc[0].to_dict())

    current_match_num = int(upcoming.iloc[0]["Match #"]) if len(upcoming) > 0 else state["current_match"] + 1

    health = get_squad_health_report(current_team_data, schedule_df, current_match_num)

    st.subheader("Squad Health")

    hcol1, hcol2, hcol3, hcol4 = st.columns(4)
    with hcol1:
        st.metric("Team Diversity", f"{health['team_diversity']} teams", help="More teams = better coverage")
    with hcol2:
        risk_colors = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
        st.metric("Concentration Risk", f"{risk_colors.get(health['concentration_risk'], '⚪')} {health['concentration_risk']}")
    with hcol3:
        st.metric("Avg Active/Match", f"{health['avg_active']}/11")
    with hcol4:
        st.metric("Coverage (5+ active)", f"{health['coverage_pct']:.0f}%")

    # Team composition
    with st.expander("Squad Composition by Team"):
        for team, count in sorted(health["team_counts"].items(), key=lambda x: -x[1]):
            bar = "█" * count + "░" * (11 - count)
            st.markdown(f"**{team}:** {count} players {bar}")

    # Target teams
    if health.get("target_teams"):
        st.markdown("**Teams to target (high fixture density, not in squad):**")
        for tt in health["target_teams"]:
            st.markdown(f"- **{tt['team']}**: {tt['matches_in_window']} matches in next 10")

    st.markdown("---")

    # --- Coverage Map (next 10 matches) ---
    st.subheader("Coverage Map — Next 10 Matches")

    if health["per_match"]:
        coverage_rows = []
        for pm in health["per_match"]:
            active_pct = pm["active_count"] / 11 * 100
            if pm["active_count"] >= 5:
                status = "🟢"
            elif pm["active_count"] >= 3:
                status = "🟡"
            else:
                status = "🔴"
            coverage_rows.append({
                "Match": f"#{pm['match_num']}",
                "Fixture": pm["match"],
                "Active": pm["active_count"],
                "Idle": pm["idle_count"],
                "Coverage": f"{status} {active_pct:.0f}%",
            })
        st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Current Team with Classification ---
    st.subheader("Current Squad — Player Status")

    player_rows = []
    for p in current_team_data:
        name = p["Player Name"]
        pinfo = health["per_player"].get(name, {})
        cls = pinfo.get("classification", "?")
        next_in = pinfo.get("next_active_in", 99)
        matches_window = pinfo.get("matches_in_window", 0)

        cls_emoji = {"ACTIVE": "🟢", "KEEP": "🟢", "MAYBE": "🟡", "SWAP": "🔴"}.get(cls, "⚪")
        marker = ""
        if p["Player Name"] == state.get("captain"):
            marker = " (C)"
        elif p["Player Name"] == state.get("vice_captain"):
            marker = " (VC)"

        if next_in == 0:
            next_str = "This match"
        elif next_in >= 99:
            next_str = "None in window"
        else:
            next_str = f"In {next_in} match(es)"

        player_rows.append({
            "Status": f"{cls_emoji} {cls}",
            "Player": f"{name}{marker}",
            "Team": p["Team"],
            "Role": p.get("RoleCode", ""),
            "Next Active": next_str,
            "Matches/10": matches_window,
        })

    st.dataframe(pd.DataFrame(player_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Transfer Recommendations ---
    st.subheader("Transfer Recommendations")

    if len(upcoming) > 0:
        next_match = upcoming.iloc[0]
        st.markdown(f"**For Match {int(next_match['Match #'])}: {next_match['Match']} @ {next_match['VenueName']}**")

        playing_xi = get_playing_xi_cached()
        all_players = players_df[players_df["IsAvailable"]].to_dict("records")

        if st.button("Generate Smart Recommendations", type="primary", use_container_width=True):
            with st.spinner("Analyzing schedule, scoring replacements, calculating ROI..."):
                rec = recommend_transfers(
                    current_team_data, schedule_df,
                    int(next_match["Match #"]), all_players, playing_xi,
                )
                st.session_state["transfer_rec"] = rec

        if "transfer_rec" in st.session_state:
            rec = st.session_state["transfer_rec"]

            # Budget analysis
            ba = rec.get("budget_analysis", {})
            bcol1, bcol2, bcol3 = st.columns(3)
            with bcol1:
                st.metric("Smart Budget This Match", ba.get("budget", 0))
            with bcol2:
                st.metric("Truly Idle", ba.get("truly_idle", 0), help="Idle this AND next match")
            with bcol3:
                st.metric("Budget Multiplier", f"{ba.get('multiplier', 1.0)}x")

            st.info(rec.get("summary", ""))

            # KEEP list
            if rec.get("keep_list"):
                with st.expander(f"🟢 KEEP — {len(rec['keep_list'])} players (save transfers)", expanded=False):
                    for k in rec["keep_list"]:
                        st.markdown(f"- **{k['player']}** ({k['team']}) — {k['reason']}")

            # Swap recommendations
            if rec.get("transfers"):
                for i, swap in enumerate(rec["transfers"], 1):
                    cls_emoji = {"SWAP": "🔴", "MAYBE": "🟡"}.get(swap.get("out_classification", ""), "🔴")
                    with st.expander(
                        f"{cls_emoji} Transfer {i}: {swap['out']} → {swap['in_name']} | ROI: {swap['roi']:.0f}",
                        expanded=True,
                    ):
                        tcol1, tcol2, tcol3 = st.columns(3)
                        with tcol1:
                            st.markdown(f"**OUT:** {swap['out']} ({swap['out_team']})")
                            st.caption(f"Idle {swap.get('out_next_active_in', '?')} more matches")
                        with tcol2:
                            st.markdown(f"**IN:** {swap['in_name']} ({swap['in_team']})")
                            st.caption(f"+{swap['immediate_pts']:.0f} pts this match | {swap['durability']}/5 future matches")
                        with tcol3:
                            st.metric("ROI Score", f"{swap['roi']:.0f}")
                            st.caption(f"Credit: {swap['credit_diff']:+.1f}")

                st.markdown("")
                st.markdown(f"**Captain (2x):** {rec.get('new_captain', 'N/A')} ({rec.get('captain_pts', 0):.0f} pts)")
                st.markdown(f"**VC (1.5x):** {rec.get('new_vc', 'N/A')} ({rec.get('vc_pts', 0):.0f} pts)")

                if st.button("Apply All Transfers", type="primary"):
                    out_names = [s["out"] for s in rec["transfers"]]
                    in_players = [s["in"] for s in rec["transfers"]]
                    new_state, errors = apply_transfers(
                        in_players, out_names,
                        rec.get("new_captain"), rec.get("new_vc"),
                    )
                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        st.success(f"Applied {len(rec['transfers'])} transfers! {new_state['transfers_remaining']} remaining.")
                        st.rerun()
            else:
                st.success("No transfers needed — squad is well-positioned.")

        # --- Captain/VC ---
        st.markdown("---")
        st.subheader("Captain/VC Recommendation (Free)")

        next_info = {"Team1": next_match["Team1"], "Team2": next_match["Team2"], "VenueName": next_match["VenueName"]}
        cv_rec = recommend_captain_vc(current_team_data, next_info)
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            st.markdown(f"**Current C:** {state.get('captain', 'Not set')}")
            st.markdown(f"**Recommended:** {cv_rec['captain']} ({cv_rec['captain_pts']:.0f} pts)")
        with ccol2:
            st.markdown(f"**Current VC:** {state.get('vice_captain', 'Not set')}")
            st.markdown(f"**Recommended:** {cv_rec['vice_captain']} ({cv_rec['vc_pts']:.0f} pts)")

        if st.button("Update Captain/VC"):
            change_captain_vc(cv_rec["captain"], cv_rec["vice_captain"])
            st.success(f"Captain: {cv_rec['captain']}, VC: {cv_rec['vice_captain']}")
            st.rerun()

else:
    st.info("No team set yet. Go to Team Builder to create your initial team.")

# --- Booster Manager ---
st.markdown("---")
st.subheader(f"Boosters ({budget['boosters_remaining']} / 7 remaining)")

if budget["boosters_remaining"] > 0:
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        booster = st.selectbox("Select Booster", BOOSTER_TYPES)
    with bcol2:
        match_num = st.number_input(
            "For Match #", min_value=1, max_value=70,
            value=int(upcoming.iloc[0]["Match #"]) if len(upcoming) > 0 else 1,
        )

    booster_descriptions = {
        "Triple Captain": "Captain earns 3x points instead of 2x",
        "Indian Warrior": "Doubles points for all Indian players",
        "Foreign Stars": "Doubles points for all overseas players",
        "Wild Card": "Unlimited transfers for one gameweek",
        "Free Hit": "Transfers don't count against budget",
    }
    st.caption(booster_descriptions.get(booster, ""))

    if st.button(f"Use {booster} for Match {match_num}"):
        new_state, error = use_booster(booster, match_num)
        if error:
            st.error(error)
        else:
            st.success(f"{booster} activated for Match {match_num}!")
            st.rerun()

if budget["boosters_used"]:
    st.markdown("**Used Boosters:**")
    for b in budget["boosters_used"]:
        st.markdown(f"- {b['booster']} — Match {b['match']}")

# --- Transfer History ---
st.markdown("---")
st.subheader("Transfer History")

log = load_transfer_log()
if log:
    for entry in reversed(log[-10:]):
        out_str = ", ".join(entry.get("out", []))
        in_str = ", ".join(entry.get("in", []))
        st.markdown(f"**Match {entry.get('match', '?')}:** OUT: {out_str} | IN: {in_str} ({entry.get('transfers_after', '?')} remaining)")
else:
    st.info("No transfers made yet.")

# --- What-If Simulator ---
st.markdown("---")
st.subheader("What-If Simulator")

if state.get("current_team") and len(upcoming) > 0:
    sim_col1, sim_col2 = st.columns(2)
    current_names = state["current_team"]
    with sim_col1:
        player_out = st.selectbox("Player OUT", current_names, key="sim_out")
    with sim_col2:
        out_data = players_df[players_df["Player Name"] == player_out]
        out_role = out_data.iloc[0]["RoleCode"] if len(out_data) > 0 else None
        available = players_df[
            (players_df["IsAvailable"]) &
            (~players_df["Player Name"].isin(current_names)) &
            (players_df["RoleCode"] == out_role if out_role else True)
        ].sort_values("Credits", ascending=False)
        player_in = st.selectbox("Player IN", available["Player Name"].tolist(), key="sim_in")

    if player_out and player_in:
        venue = upcoming.iloc[0]["VenueName"]
        out_pts = estimate_fantasy_points(out_data.iloc[0].to_dict(), venue) if len(out_data) > 0 else 0
        in_data = players_df[players_df["Player Name"] == player_in]
        in_pts = estimate_fantasy_points(in_data.iloc[0].to_dict(), venue) if len(in_data) > 0 else 0
        gain = in_pts - out_pts

        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            st.metric(f"{player_out}", f"{out_pts:.0f} pts")
        with scol2:
            st.metric(f"{player_in}", f"{in_pts:.0f} pts")
        with scol3:
            st.metric("Net Gain", f"{gain:+.0f} pts", delta=f"{gain:+.0f}", delta_color="normal")
