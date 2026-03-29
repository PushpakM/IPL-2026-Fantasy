import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.transfer_engine import load_transfer_log, load_state

st.set_page_config(page_title="History | IPL 2026", page_icon="📜", layout="wide")

st.title("Team History")

GENERATED_DIR = Path(__file__).resolve().parent.parent / "data" / "generated_teams"

# --- Load saved teams ---
saved_files = sorted(GENERATED_DIR.glob("Match_*_Teams.json")) if GENERATED_DIR.exists() else []

if saved_files:
    st.subheader(f"Saved Teams ({len(saved_files)} matches)")

    for f in saved_files:
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue

        match_num = data.get("match_num", "?")
        match_name = data.get("match", "Unknown")
        venue = data.get("venue", "Unknown")
        match_date = data.get("date", "")

        with st.expander(f"Match {match_num}: {match_name} — {venue}", expanded=False):
            col1, col2 = st.columns(2)

            for col, platform, label in [
                (col1, "my11circle", "My11Circle"),
                (col2, "tata_ipl", "TATA IPL Fantasy"),
            ]:
                with col:
                    team = data.get(platform, {})
                    if not team:
                        st.info(f"No {label} team saved")
                        continue

                    st.markdown(f"**{label}**")
                    st.markdown(f"Captain: **{team.get('captain', 'N/A')}** | VC: **{team.get('vice_captain', 'N/A')}**")
                    st.markdown(f"Credits: {team.get('credits_used', 'N/A')}/100 | Est. Pts: {team.get('total_points', 'N/A')}")

                    players = team.get("players", [])
                    for p in players:
                        marker = ""
                        if p == team.get("captain"):
                            marker = " (C)"
                        elif p == team.get("vice_captain"):
                            marker = " (VC)"
                        st.markdown(f"- {p}{marker}")

            # Actual points (manual input)
            st.markdown("---")
            st.markdown("**Actual Points (enter after match):**")
            acol1, acol2 = st.columns(2)
            with acol1:
                actual_my11 = st.number_input(
                    f"My11Circle actual pts (Match {match_num})",
                    min_value=0, max_value=2000, value=0,
                    key=f"actual_my11_{match_num}",
                )
            with acol2:
                actual_tata = st.number_input(
                    f"TATA IPL actual pts (Match {match_num})",
                    min_value=0, max_value=2000, value=0,
                    key=f"actual_tata_{match_num}",
                )

else:
    st.info("No teams generated yet. Go to Team Builder to create teams for your first match!")

# --- Transfer Log ---
st.markdown("---")
st.subheader("Transfer Log")

log = load_transfer_log()
if log:
    log_rows = []
    for entry in log:
        log_rows.append({
            "Match": entry.get("match", "?"),
            "Date": entry.get("date", "")[:10],
            "Players Out": ", ".join(entry.get("out", [])),
            "Players In": ", ".join(entry.get("in", [])),
            "Transfers After": entry.get("transfers_after", "?"),
        })
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
else:
    st.info("No transfers made yet.")

# --- Season Summary ---
st.markdown("---")
st.subheader("Season Summary")

state = load_state()
scol1, scol2, scol3 = st.columns(3)
with scol1:
    st.metric("Transfers Used", state.get("transfers_used", 0))
with scol2:
    st.metric("Boosters Used", len(state.get("boosters_used", [])))
with scol3:
    st.metric("Current Match", state.get("current_match", 0))
