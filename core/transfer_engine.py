"""
Smart transfer engine for TATA IPL Fantasy.

160 transfers for 70 matches (full season). Each team plays 14/70 matches.
~8.8 players idle per match on average → 616 total idle instances, only 160 transfers.
Every transfer must have positive ROI.

Strategy: Schedule-aware dynamic budgeting.
- Classify idle players as KEEP (team plays soon) vs SWAP (idle 3+ matches)
- Calculate per-match budget based on truly-idle count and remaining transfers
- Score replacements by ROI: immediate points + durability (future match coverage)
- Captain/VC changes are always free.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

from core.scorer import estimate_fantasy_points
from core.data_loader import load_schedule

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "season_state.json"
TRANSFER_LOG_FILE = DATA_DIR / "transfer_log.json"

TOTAL_LEAGUE_TRANSFERS = 160
TOTAL_SEASON_MATCHES = 70
TOTAL_BOOSTERS = 7

BOOSTER_TYPES = [
    "Triple Captain",
    "Indian Warrior",
    "Foreign Stars",
    "Wild Card",
    "Free Hit",
]


# ---------------------------------------------------------------------------
# State persistence (unchanged)
# ---------------------------------------------------------------------------

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_default_state() -> dict:
    return {
        "current_team": [],
        "captain": None,
        "vice_captain": None,
        "credits_used": 0.0,
        "transfers_used": 0,
        "transfers_remaining": TOTAL_LEAGUE_TRANSFERS,
        "current_match": 0,
        "boosters_remaining": TOTAL_BOOSTERS,
        "boosters_used": [],
        "last_updated": datetime.now().isoformat(),
    }


def load_state() -> dict:
    _ensure_data_dir()
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return get_default_state()


def save_state(state: dict):
    _ensure_data_dir()
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def load_transfer_log() -> list:
    if TRANSFER_LOG_FILE.exists():
        try:
            return json.loads(TRANSFER_LOG_FILE.read_text())
        except Exception:
            pass
    return []


def save_transfer_log(log: list):
    _ensure_data_dir()
    TRANSFER_LOG_FILE.write_text(json.dumps(log, indent=2, default=str))


def set_initial_team(players: list, captain: str, vice_captain: str):
    total_credits = sum(p.get("Credits", 0) for p in players)
    state = get_default_state()
    state["current_team"] = [p["Player Name"] for p in players]
    state["captain"] = captain
    state["vice_captain"] = vice_captain
    state["credits_used"] = round(total_credits, 1)
    state["current_match"] = 0
    save_state(state)
    return state


def apply_transfers(
    players_in: list, players_out: list, new_captain: str = None, new_vc: str = None
) -> Tuple[dict, List[str]]:
    state = load_state()
    errors = []

    num_transfers = len(players_in)
    if num_transfers != len(players_out):
        errors.append("Number of players in must equal players out")
        return state, errors

    if state["transfers_remaining"] < num_transfers:
        errors.append(
            f"Not enough transfers: need {num_transfers}, have {state['transfers_remaining']}"
        )
        return state, errors

    current = list(state["current_team"])
    for name in players_out:
        if name in current:
            current.remove(name)
        else:
            errors.append(f"{name} not in current team")

    for p in players_in:
        current.append(p["Player Name"])

    if errors:
        return state, errors

    state["current_team"] = current
    state["transfers_used"] += num_transfers
    state["transfers_remaining"] -= num_transfers

    if new_captain:
        state["captain"] = new_captain
    if new_vc:
        state["vice_captain"] = new_vc

    log = load_transfer_log()
    log.append({
        "match": state["current_match"],
        "date": datetime.now().isoformat(),
        "out": players_out,
        "in": [p["Player Name"] for p in players_in],
        "transfers_after": state["transfers_remaining"],
    })
    save_transfer_log(log)
    save_state(state)
    return state, []


def change_captain_vc(captain: str = None, vice_captain: str = None) -> dict:
    state = load_state()
    if captain:
        state["captain"] = captain
    if vice_captain:
        state["vice_captain"] = vice_captain
    save_state(state)
    return state


def use_booster(booster_name: str, match_num: int) -> Tuple[dict, str]:
    state = load_state()
    if state["boosters_remaining"] <= 0:
        return state, "No boosters remaining"
    state["boosters_used"].append({
        "booster": booster_name,
        "match": match_num,
        "date": datetime.now().isoformat(),
    })
    state["boosters_remaining"] -= 1
    save_state(state)
    return state, ""


# ---------------------------------------------------------------------------
# Schedule analysis — the core intelligence
# ---------------------------------------------------------------------------

def _get_playing_teams(match_info) -> set:
    """Get teams playing in a match. Accepts dict or Series."""
    if hasattr(match_info, "get"):
        return {match_info.get("Team1", ""), match_info.get("Team2", "")} - {""}
    return {match_info["Team1"], match_info["Team2"]} - {""}


def analyze_schedule_coverage(
    current_team_data: list,
    schedule_df,
    current_match_num: int,
    lookahead: int = 10,
) -> dict:
    """
    Analyze how well the current squad covers upcoming matches.

    Returns:
        per_match: list of dicts [{match_num, match, teams, active_count, idle_count, active_names, idle_names}]
        per_player: dict {player_name: {team, next_active_in, matches_in_window, classification}}
        team_diversity: number of distinct IPL teams in squad
        coverage_pct: % of upcoming matches where at least 5 players are active
    """
    future = schedule_df[schedule_df["Match #"] > current_match_num].sort_values("Match #").head(lookahead)

    # Map player → team
    player_teams = {p["Player Name"]: p.get("Team", "") for p in current_team_data}
    squad_teams = set(player_teams.values())
    team_diversity = len(squad_teams)

    # Per-match analysis
    per_match = []
    for _, row in future.iterrows():
        playing = _get_playing_teams(row)
        active_names = [name for name, team in player_teams.items() if team in playing]
        idle_names = [name for name, team in player_teams.items() if team not in playing]
        per_match.append({
            "match_num": int(row["Match #"]),
            "match": row["Match"],
            "venue": row.get("VenueName", ""),
            "teams": playing,
            "active_count": len(active_names),
            "idle_count": len(idle_names),
            "active_names": active_names,
            "idle_names": idle_names,
        })

    # Per-player analysis
    per_player = {}
    for name, team in player_teams.items():
        next_active_in = None
        matches_in_window = 0
        for i, pm in enumerate(per_match):
            if team in pm["teams"]:
                matches_in_window += 1
                if next_active_in is None:
                    next_active_in = i  # 0-indexed: 0 means next match

        # Classification
        if next_active_in is None:
            classification = "SWAP"  # Team doesn't play in entire window
        elif next_active_in == 0:
            classification = "ACTIVE"  # Plays next match
        elif next_active_in == 1:
            classification = "KEEP"  # Plays in match after next
        elif next_active_in == 2:
            classification = "MAYBE"  # 2 matches away
        else:
            classification = "SWAP"  # 3+ matches away

        per_player[name] = {
            "team": team,
            "next_active_in": next_active_in if next_active_in is not None else 99,
            "matches_in_window": matches_in_window,
            "classification": classification,
        }

    # Coverage: how many of the upcoming matches have >=5 active players
    covered = sum(1 for pm in per_match if pm["active_count"] >= 5)
    coverage_pct = (covered / len(per_match) * 100) if per_match else 0

    return {
        "per_match": per_match,
        "per_player": per_player,
        "team_diversity": team_diversity,
        "coverage_pct": round(coverage_pct, 0),
        "squad_teams": sorted(squad_teams),
    }


def calculate_transfer_budget(
    state: dict,
    schedule_df,
    current_match_num: int,
    current_team_data: list,
) -> dict:
    """
    Calculate the smart transfer budget for the current match.

    Returns dict with:
        budget: recommended number of transfers this match
        base_rate: flat average (remaining / matches_left)
        truly_idle: players idle this match AND next match
        multiplier: adjustment factor
        reasoning: human-readable explanation
    """
    remaining = state["transfers_remaining"]
    matches_left = max(TOTAL_SEASON_MATCHES - current_match_num, 1)
    base_rate = remaining / matches_left

    # Get this match and next match
    future = schedule_df[schedule_df["Match #"] >= current_match_num].sort_values("Match #")
    if len(future) == 0:
        return {"budget": 0, "base_rate": 0, "truly_idle": 0, "multiplier": 1.0, "reasoning": "No matches remaining"}

    this_match = future.iloc[0]
    next_match = future.iloc[1] if len(future) > 1 else None

    this_teams = _get_playing_teams(this_match)
    next_teams = _get_playing_teams(next_match) if next_match is not None else set()

    # Count truly idle: idle THIS match AND idle NEXT match
    truly_idle = 0
    idle_this = 0
    for p in current_team_data:
        team = p.get("Team", "")
        is_idle_now = team not in this_teams
        is_idle_next = team not in next_teams
        if is_idle_now:
            idle_this += 1
            if is_idle_next:
                truly_idle += 1

    # Dynamic multiplier based on idle severity
    if truly_idle >= 8:
        multiplier = 2.5
    elif truly_idle >= 5:
        multiplier = 2.0
    elif truly_idle >= 3:
        multiplier = 1.5
    else:
        multiplier = 1.0

    # Season phase adjustment
    season_pct = current_match_num / TOTAL_SEASON_MATCHES
    if season_pct > 0.85:
        # Late season: spend remaining budget more freely
        multiplier *= 1.3
    elif season_pct < 0.15:
        # Early season: slightly conservative to gather intel
        multiplier *= 0.9

    raw_budget = base_rate * multiplier
    budget = min(
        round(raw_budget),
        truly_idle,       # Never swap more than truly idle players
        remaining,        # Never exceed total remaining
        8,                # Hard cap per match
    )
    budget = max(budget, 0)

    # Reasoning
    if budget == 0:
        reasoning = "No truly idle players (or no transfers remaining)."
    elif truly_idle <= 2:
        reasoning = f"Only {truly_idle} players idle for 2+ matches. Conservative spending."
    elif truly_idle <= 5:
        reasoning = f"{truly_idle} players idle for 2+ matches. Moderate transfer window."
    else:
        reasoning = f"{truly_idle} players idle for 2+ matches. High-priority transfer window."

    return {
        "budget": budget,
        "base_rate": round(base_rate, 2),
        "truly_idle": truly_idle,
        "idle_this_match": idle_this,
        "multiplier": round(multiplier, 2),
        "reasoning": reasoning,
        "remaining": remaining,
        "matches_left": matches_left,
    }


# ---------------------------------------------------------------------------
# Smart transfer recommendations
# ---------------------------------------------------------------------------

def recommend_transfers(
    current_team_data: list,
    schedule_df,
    current_match_num: int,
    all_players: list = None,
    playing_xi: dict = None,
) -> dict:
    """
    Recommend transfers using schedule-aware ROI scoring.

    Args:
        current_team_data: list of player dicts currently in the team
        schedule_df: full season schedule DataFrame
        current_match_num: which match number we're planning for
        all_players: all available players to choose from
        playing_xi: {team_name: [player_names]} from scraper if available

    Returns dict with:
        transfers: list of swap recommendations with ROI
        keep_list: players recommended to KEEP (idle but team plays soon)
        captain/vc: recommended captain and vice captain
        budget_analysis: output from calculate_transfer_budget
        coverage: schedule coverage analysis
    """
    if not all_players:
        return {"transfers": [], "keep_list": [], "summary": "No player data available"}

    state = load_state()
    if state["transfers_remaining"] < 1:
        return {"transfers": [], "keep_list": [], "summary": "No transfers remaining!"}

    # Step 1: Analyze schedule coverage
    coverage = analyze_schedule_coverage(current_team_data, schedule_df, current_match_num - 1, lookahead=10)

    # Step 2: Calculate smart budget
    budget_analysis = calculate_transfer_budget(state, schedule_df, current_match_num, current_team_data)
    budget = budget_analysis["budget"]

    # Get this match info
    this_match_rows = schedule_df[schedule_df["Match #"] == current_match_num]
    if len(this_match_rows) == 0:
        return {"transfers": [], "keep_list": [], "summary": "Match not found in schedule"}
    this_match = this_match_rows.iloc[0]
    this_teams = _get_playing_teams(this_match)
    this_venue = this_match.get("VenueName", "")

    # Step 3: Classify each player
    keep_list = []
    swap_candidates = []
    maybe_candidates = []
    active_players = []

    for p in current_team_data:
        name = p["Player Name"]
        player_info = coverage["per_player"].get(name, {})
        classification = player_info.get("classification", "ACTIVE")
        team = p.get("Team", "")

        if team in this_teams:
            active_players.append(p)
        elif classification == "KEEP":
            keep_list.append({
                "player": name,
                "team": team,
                "reason": f"Team plays in match {current_match_num + player_info.get('next_active_in', 1) + 1} — keep to avoid wasting a transfer",
                "next_active_in": player_info.get("next_active_in", 1),
            })
        elif classification == "MAYBE":
            maybe_candidates.append(p)
        elif classification in ("SWAP", "ACTIVE"):
            if team not in this_teams:
                swap_candidates.append(p)

    # Step 4: Find replacements from playing teams
    current_names = {p["Player Name"] for p in current_team_data}
    available = [
        p for p in all_players
        if p["Player Name"] not in current_names
        and p.get("IsAvailable", True)
        and p.get("Team", "") in this_teams
    ]

    # Filter to confirmed XI if available
    if playing_xi:
        confirmed_names = set()
        for value in playing_xi.values():
            if isinstance(value, dict) and "players" in value:
                confirmed_names.update(value["players"])
            elif isinstance(value, list):
                confirmed_names.update(value)
        if confirmed_names:
            xi_available = [p for p in available if p["Player Name"] in confirmed_names]
            if len(xi_available) >= 5:
                available = xi_available

    # Step 5: Score replacements by ROI
    # Get future match teams for durability calculation
    future_matches = schedule_df[schedule_df["Match #"] > current_match_num].sort_values("Match #").head(5)
    future_team_counts = {}  # team → how many of next 5 matches they play
    for _, frow in future_matches.iterrows():
        for t in _get_playing_teams(frow):
            future_team_counts[t] = future_team_counts.get(t, 0) + 1

    replacement_scored = []
    for p in available:
        immediate_pts = estimate_fantasy_points(p, this_venue)
        team = p.get("Team", "")
        durability = future_team_counts.get(team, 0)
        durability_value = durability * 15  # ~15 pts per future active match
        roi = immediate_pts + durability_value
        replacement_scored.append({
            "player": p,
            "immediate_pts": round(immediate_pts, 1),
            "durability": durability,
            "durability_value": durability_value,
            "roi": round(roi, 1),
        })

    replacement_scored.sort(key=lambda x: x["roi"], reverse=True)

    # Step 6: Build swap recommendations — SWAP candidates first, then MAYBE if budget allows
    all_candidates = swap_candidates.copy()
    if budget > len(swap_candidates):
        all_candidates.extend(maybe_candidates)

    # Sort candidates: swap those idle longest first
    candidate_info = []
    for p in all_candidates:
        name = p["Player Name"]
        pinfo = coverage["per_player"].get(name, {})
        candidate_info.append({
            "player": p,
            "next_active_in": pinfo.get("next_active_in", 99),
            "classification": pinfo.get("classification", "SWAP"),
        })
    candidate_info.sort(key=lambda x: -x["next_active_in"])  # Longest idle first

    swaps = []
    seen_in = set()
    current_credits = sum(p.get("Credits", 0) for p in current_team_data)

    for ci in candidate_info:
        if len(swaps) >= budget:
            break

        out_player = ci["player"]
        out_role = out_player.get("RoleCode", "BAT")
        out_credits = out_player.get("Credits", 7.0)
        out_team = out_player.get("Team", "")

        # Calculate swap-back penalty: will we want this player back soon?
        out_future_matches = future_team_counts.get(out_team, 0)
        swap_back_penalty = 20 if out_future_matches >= 2 else 0

        # Find best same-role replacement
        best_rep = None
        for rep in replacement_scored:
            rp = rep["player"]
            if rp["Player Name"] in seen_in:
                continue
            if rp.get("RoleCode", "BAT") != out_role:
                continue
            net_credit = rp.get("Credits", 7.0) - out_credits
            if current_credits + net_credit > 100.0:
                continue
            # Check ROI threshold: must exceed swap_back_penalty
            adjusted_roi = rep["roi"] - swap_back_penalty
            if adjusted_roi > 30:  # Minimum ROI threshold
                best_rep = rep
                break

        if best_rep:
            rp = best_rep["player"]
            net_credit = rp.get("Credits", 7.0) - out_credits
            swaps.append({
                "out": out_player["Player Name"],
                "out_team": out_team,
                "out_role": out_role,
                "out_classification": ci["classification"],
                "out_next_active_in": ci["next_active_in"],
                "in": rp,
                "in_name": rp["Player Name"],
                "in_team": rp.get("Team", ""),
                "immediate_pts": best_rep["immediate_pts"],
                "durability": best_rep["durability"],
                "roi": best_rep["roi"],
                "credit_diff": round(net_credit, 1),
                "reason": _build_swap_reason(ci, best_rep, out_team),
            })
            seen_in.add(rp["Player Name"])
            current_credits += net_credit

    # Step 7: Captain/VC from projected team
    projected_team = list(current_team_data)
    swap_out_names = {s["out"] for s in swaps}
    projected_team = [p for p in projected_team if p["Player Name"] not in swap_out_names]
    for s in swaps:
        projected_team.append(s["in"])

    captain_rec = recommend_captain_vc(projected_team, {"Team1": this_match["Team1"], "Team2": this_match["Team2"], "VenueName": this_venue})

    # Summary
    active_count = len(active_players)
    idle_count = 11 - active_count
    summary = (
        f"Squad: {active_count} active, {idle_count} idle. "
        f"Smart budget: {budget} transfers this match "
        f"(base rate {budget_analysis['base_rate']:.1f}/match, "
        f"{state['transfers_remaining']} remaining for {budget_analysis['matches_left']} matches). "
        f"{budget_analysis['reasoning']}"
    )

    return {
        "transfers": swaps,
        "keep_list": keep_list,
        "new_captain": captain_rec["captain"],
        "new_vc": captain_rec["vice_captain"],
        "captain_pts": captain_rec["captain_pts"],
        "vc_pts": captain_rec["vc_pts"],
        "summary": summary,
        "active_count": active_count,
        "idle_count": idle_count,
        "budget_analysis": budget_analysis,
        "coverage": coverage,
    }


def _build_swap_reason(candidate_info: dict, replacement_info: dict, out_team: str) -> str:
    ci = candidate_info
    ri = replacement_info
    rp = ri["player"]
    idle_matches = ci["next_active_in"]
    if idle_matches >= 99:
        idle_str = "no upcoming matches"
    else:
        idle_str = f"idle {idle_matches} more matches"

    return (
        f"{out_team} {idle_str} → {rp.get('Team', '')} active now | "
        f"+{ri['immediate_pts']:.0f} pts this match, "
        f"plays {ri['durability']}/5 upcoming | ROI: {ri['roi']:.0f}"
    )


# ---------------------------------------------------------------------------
# Budget report & squad health
# ---------------------------------------------------------------------------

def get_transfer_budget_report(schedule_df=None, current_match_num: int = None) -> dict:
    """Get transfer budget status with smart metrics."""
    state = load_state()
    matches_played = max(state["current_match"], 1)
    matches_left = max(TOTAL_SEASON_MATCHES - matches_played, 1)

    burn_rate = state["transfers_used"] / matches_played if matches_played > 0 else 0
    base_rate = state["transfers_remaining"] / matches_left

    # Project season-end surplus/deficit
    projected_usage = burn_rate * TOTAL_SEASON_MATCHES
    projected_surplus = TOTAL_LEAGUE_TRANSFERS - projected_usage

    if projected_surplus > 30:
        status = "Surplus"
        status_color = "green"
    elif projected_surplus > 0:
        status = "On Track"
        status_color = "green"
    elif projected_surplus > -20:
        status = "Tight"
        status_color = "orange"
    else:
        status = "Critical"
        status_color = "red"

    return {
        "transfers_used": state["transfers_used"],
        "transfers_remaining": state["transfers_remaining"],
        "matches_played": matches_played,
        "matches_remaining": matches_left,
        "total_season_matches": TOTAL_SEASON_MATCHES,
        "burn_rate": round(burn_rate, 1),
        "base_rate": round(base_rate, 2),
        "projected_surplus": round(projected_surplus),
        "status": status,
        "status_color": status_color,
        "boosters_remaining": state["boosters_remaining"],
        "boosters_used": state["boosters_used"],
    }


def get_squad_health_report(
    current_team_data: list,
    schedule_df,
    current_match_num: int,
) -> dict:
    """
    Comprehensive squad health analysis.
    """
    coverage = analyze_schedule_coverage(current_team_data, schedule_df, current_match_num - 1, lookahead=10)

    # Team concentration risk
    team_counts = {}
    for p in current_team_data:
        t = p.get("Team", "")
        team_counts[t] = team_counts.get(t, 0) + 1

    max_concentration = max(team_counts.values()) if team_counts else 0
    concentration_risk = "High" if max_concentration >= 6 else ("Medium" if max_concentration >= 4 else "Low")

    # Average active players per match
    if coverage["per_match"]:
        avg_active = sum(pm["active_count"] for pm in coverage["per_match"]) / len(coverage["per_match"])
    else:
        avg_active = 0

    # Fixture density: which teams play most in the window
    team_fixture_density = {}
    for pm in coverage["per_match"]:
        for t in pm["teams"]:
            team_fixture_density[t] = team_fixture_density.get(t, 0) + 1

    # Suggested teams to target (high fixture density teams not in squad)
    squad_teams = set(p.get("Team", "") for p in current_team_data)
    target_teams = []
    for t, count in sorted(team_fixture_density.items(), key=lambda x: -x[1]):
        if t not in squad_teams and count >= 3:
            target_teams.append({"team": t, "matches_in_window": count})

    return {
        "team_diversity": coverage["team_diversity"],
        "team_counts": team_counts,
        "concentration_risk": concentration_risk,
        "max_concentration": max_concentration,
        "coverage_pct": coverage["coverage_pct"],
        "avg_active": round(avg_active, 1),
        "per_match": coverage["per_match"],
        "per_player": coverage["per_player"],
        "target_teams": target_teams[:3],
        "squad_teams": coverage["squad_teams"],
    }


# ---------------------------------------------------------------------------
# Captain / VC (unchanged — always free)
# ---------------------------------------------------------------------------

def recommend_captain_vc(current_team_data: list, match_info: dict, schedule_df=None) -> dict:
    """
    TATA IPL captain selection: AR preference + hot streak + fixture density.
    """
    from core.scorer import get_hot_streak_multiplier

    venue = match_info.get("VenueName", "")
    match_num = match_info.get("Match #", 1)
    playing_teams = _get_playing_teams(match_info)

    scored = []
    active_players = [p for p in current_team_data if p.get("Team", "") in playing_teams]
    if not active_players:
        active_players = current_team_data

    for p in active_players:
        pts = estimate_fantasy_points(p, venue, platform="tata_ipl")
        captain_score = pts

        # AR preference: +10% for all-rounders (dual contribution as captain)
        if p.get("RoleCode") == "AR":
            captain_score *= 1.10

        # Hot streak bonus
        captain_score *= get_hot_streak_multiplier(p)

        # Fixture density bonus
        if schedule_df is not None:
            from core.team_selector import get_fixture_density_factor
            fd = get_fixture_density_factor(p.get("Team", ""), schedule_df, match_num)
            captain_score *= fd

        scored.append({"player": p, "estimated_pts": pts, "captain_score": captain_score})

    scored.sort(key=lambda x: x["captain_score"], reverse=True)

    captain = scored[0] if scored else None
    vc = scored[1] if len(scored) > 1 else None

    return {
        "captain": captain["player"]["Player Name"] if captain else None,
        "captain_pts": captain["estimated_pts"] if captain else 0,
        "vice_captain": vc["player"]["Player Name"] if vc else None,
        "vc_pts": vc["estimated_pts"] if vc else 0,
    }
