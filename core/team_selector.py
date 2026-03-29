"""
Smart team selection algorithm with knapsack-style optimization.
Builds optimal 11-player teams within 100 credit budget and role constraints.

Two platforms:
- My11Circle: fresh team from scratch every match, 3 risk modes (safe/balanced/aggressive)
- TATA IPL: season-long team with transfer optimization
"""

from typing import Dict, List, Optional
import pandas as pd

from core.scorer import estimate_fantasy_points, get_matchup_bonus, TIER_WEIGHTS
from core.validator import validate_team, get_valid_role_combinations, PLATFORM_RULES


# Risk mode tier weight adjustments for My11Circle
RISK_MODE_WEIGHTS = {
    "safe": {"Star": 1.15, "Premium": 0.95, "Value": 0.50, "Budget": 0.25},
    "balanced": {"Star": 1.0, "Premium": 0.8, "Value": 0.6, "Budget": 0.4},  # default
    "aggressive": {"Star": 0.85, "Premium": 0.75, "Value": 0.80, "Budget": 0.65},
}


def build_best_xi(
    players_df: pd.DataFrame,
    team1: str,
    team2: str,
    venue_name: str = "",
    platform: str = "tata_ipl",
    credit_budget: float = 100.0,
    next_venue: str = "",
    playing_xi: dict = None,
    risk_mode: str = "balanced",
) -> dict:
    """
    Build the optimal 11-player team for a match.

    Args:
        risk_mode: "safe" (high-floor), "balanced" (default), "aggressive" (differentials)
                   Only affects My11Circle. TATA IPL always uses balanced.
    """
    # Filter to available players from the two teams
    mask = (
        players_df["Team"].isin([team1, team2])
        & players_df["IsAvailable"]
    )
    available = players_df[mask].copy()

    # If playing XI is available, filter to only confirmed players
    if playing_xi:
        confirmed_names = set()
        for team_name, player_list in playing_xi.items():
            confirmed_names.update(player_list)
        if confirmed_names:
            xi_mask = available["Player Name"].isin(confirmed_names)
            xi_filtered = available[xi_mask]
            if len(xi_filtered) >= 11:
                available = xi_filtered

    if len(available) < 11:
        return {"error": f"Not enough available players: {len(available)}", "players": []}

    # Determine effective risk mode
    effective_mode = risk_mode if platform == "my11circle" else "balanced"
    mode_weights = RISK_MODE_WEIGHTS.get(effective_mode, RISK_MODE_WEIGHTS["balanced"])

    # Score each player
    use_lookahead = platform == "tata_ipl" and next_venue
    scores = []
    for _, row in available.iterrows():
        p = row.to_dict()

        # Apply risk-mode adjusted scoring
        original_tier = p.get("Performance Tier", "Value")
        original_weight = TIER_WEIGHTS.get(original_tier, 0.6)
        mode_weight = mode_weights.get(original_tier, 0.6)

        # Temporarily adjust for scoring
        if mode_weight != original_weight:
            adjusted_credits = p.get("Credits", 7.0) * (mode_weight / max(original_weight, 0.01))
            p_adjusted = dict(p)
            p_adjusted["Credits"] = adjusted_credits
        else:
            p_adjusted = p

        score1 = estimate_fantasy_points(p_adjusted, venue_name, platform)

        # Aggressive mode: extra bonus for all-rounders (more scoring dimensions)
        if effective_mode == "aggressive" and p.get("RoleCode") == "AR":
            score1 *= 1.10

        # Safe mode: extra bonus for high-credit proven players
        if effective_mode == "safe" and p.get("Credits", 0) >= 9.0:
            score1 *= 1.05

        if use_lookahead:
            score2 = estimate_fantasy_points(p_adjusted, next_venue, platform)
            combined = 0.7 * score1 + 0.3 * score2
        else:
            combined = score1

        p["EstimatedPts"] = round(combined, 1)
        p["MatchPts"] = round(score1, 1)
        scores.append(p)

    # Get all valid role combinations
    combos = get_valid_role_combinations(platform)
    rules = PLATFORM_RULES[platform]

    best_team = None
    best_total = 0

    for combo in combos:
        team = []
        total_credits = 0
        team_counts = {}

        role_pools = {}
        for p in scores:
            role = p.get("RoleCode", "BAT")
            if role not in role_pools:
                role_pools[role] = []
            role_pools[role].append(p)

        for role in role_pools:
            role_pools[role].sort(key=lambda x: x["EstimatedPts"], reverse=True)

        success = True
        used_names = set()

        for role, count in combo.items():
            pool = role_pools.get(role, [])
            picked = 0
            for p in pool:
                if p["Player Name"] in used_names:
                    continue
                p_team = p["Team"]
                p_credits = p.get("Credits", 7.0)

                if team_counts.get(p_team, 0) >= rules["max_per_team"]:
                    continue
                if total_credits + p_credits > credit_budget:
                    continue

                team.append(p)
                used_names.add(p["Player Name"])
                total_credits += p_credits
                team_counts[p_team] = team_counts.get(p_team, 0) + 1
                picked += 1

                if picked >= count:
                    break

            if picked < count:
                success = False
                break

        if not success or len(team) != 11:
            continue

        total_pts = sum(p["EstimatedPts"] for p in team)
        if total_pts > best_total:
            best_total = total_pts
            best_team = team

    if not best_team:
        sorted_all = sorted(scores, key=lambda x: x["EstimatedPts"], reverse=True)
        best_team = sorted_all[:11]
        best_total = sum(p["EstimatedPts"] for p in best_team)

    # Captain/VC selection varies by risk mode
    best_team.sort(key=lambda x: x["MatchPts"], reverse=True)
    if effective_mode == "aggressive":
        # Aggressive: pick high-upside captain (all-rounder or venue specialist)
        ar_or_top = [p for p in best_team if p.get("RoleCode") == "AR"]
        if ar_or_top and ar_or_top[0]["MatchPts"] >= best_team[1]["MatchPts"] * 0.85:
            captain = ar_or_top[0]["Player Name"]
            vc = best_team[0]["Player Name"] if best_team[0]["Player Name"] != captain else best_team[1]["Player Name"]
        else:
            captain = best_team[0]["Player Name"]
            vc = best_team[1]["Player Name"]
    else:
        captain = best_team[0]["Player Name"]
        vc = best_team[1]["Player Name"]

    # Sort team by role for display
    role_order = {"WK": 0, "BAT": 1, "AR": 2, "BOW": 3}
    best_team.sort(key=lambda x: (role_order.get(x.get("RoleCode", "BAT"), 9), -x["EstimatedPts"]))

    total_credits = sum(p.get("Credits", 0) for p in best_team)
    is_valid, errors = validate_team(best_team, platform)

    # Strategy description
    strategy_desc = {
        "safe": "High-floor proven performers. Star/Premium heavy, consistent scorers.",
        "balanced": "Optimal mix of reliability and value. Best overall expected points.",
        "aggressive": "Differential picks. Value-tier gems, all-rounders, venue specialists.",
    }

    return {
        "players": best_team,
        "captain": captain,
        "vice_captain": vc,
        "total_points": round(best_total, 1),
        "credits_used": round(total_credits, 1),
        "is_valid": is_valid,
        "validation_errors": errors,
        "platform": platform,
        "risk_mode": effective_mode,
        "strategy": strategy_desc.get(effective_mode, ""),
        "used_playing_xi": playing_xi is not None and bool(playing_xi),
    }


def build_my11circle_team(
    players_df: pd.DataFrame,
    team1: str,
    team2: str,
    venue_name: str = "",
    playing_xi: dict = None,
    risk_mode: str = "balanced",
) -> dict:
    """Build fresh My11Circle team. No transfers — purely maximize this match."""
    return build_best_xi(
        players_df, team1, team2, venue_name,
        platform="my11circle", credit_budget=100.0,
        next_venue="", playing_xi=playing_xi,
        risk_mode=risk_mode,
    )


def build_my11circle_team_modes(
    players_df: pd.DataFrame,
    team1: str,
    team2: str,
    venue_name: str = "",
    playing_xi: dict = None,
) -> dict:
    """Build 3 My11Circle teams: safe, balanced, aggressive."""
    return {
        "safe": build_my11circle_team(players_df, team1, team2, venue_name, playing_xi, "safe"),
        "balanced": build_my11circle_team(players_df, team1, team2, venue_name, playing_xi, "balanced"),
        "aggressive": build_my11circle_team(players_df, team1, team2, venue_name, playing_xi, "aggressive"),
    }


def build_tata_ipl_team(
    players_df: pd.DataFrame,
    team1: str,
    team2: str,
    venue_name: str = "",
    next_venue: str = "",
    playing_xi: dict = None,
) -> dict:
    """Build TATA IPL team with 2-match lookahead."""
    return build_best_xi(
        players_df, team1, team2, venue_name,
        platform="tata_ipl", credit_budget=100.0,
        next_venue=next_venue, playing_xi=playing_xi,
        risk_mode="balanced",
    )


def build_teams_for_match(
    players_df: pd.DataFrame,
    match_info: dict,
    next_match_info: dict = None,
    playing_xi: dict = None,
) -> dict:
    team1 = match_info.get("Team1", "")
    team2 = match_info.get("Team2", "")
    venue = match_info.get("VenueName", "")
    next_venue = next_match_info.get("VenueName", "") if next_match_info else ""

    my11 = build_my11circle_team(players_df, team1, team2, venue, playing_xi)
    tata = build_tata_ipl_team(players_df, team1, team2, venue, next_venue, playing_xi)

    return {
        "match": f"{team1} vs {team2}",
        "venue": venue,
        "my11circle": my11,
        "tata_ipl": tata,
    }


def suggest_differential_picks(
    players_df: pd.DataFrame, team1: str, team2: str, venue: str = ""
) -> list:
    mask = (
        players_df["Team"].isin([team1, team2])
        & players_df["IsAvailable"]
        & players_df["Performance Tier"].isin(["Value", "Budget"])
    )
    candidates = players_df[mask].copy()

    diffs = []
    for _, row in candidates.iterrows():
        p = row.to_dict()
        pts = estimate_fantasy_points(p, venue)
        credits = p.get("Credits", 6.0)
        matchup = get_matchup_bonus(p, venue)
        efficiency = pts / credits if credits > 0 else 0
        diffs.append({
            "player": p,
            "estimated_pts": round(pts, 1),
            "credits": credits,
            "efficiency": round(efficiency, 2),
            "matchup_bonus": round((matchup - 1) * 100, 0),
        })

    diffs.sort(key=lambda x: x["efficiency"], reverse=True)
    return diffs[:5]
