import pandas as pd
from core.data_loader import load_points_system, load_venue_data

# Cache points system
_POINTS = None
_VENUES = None

TIER_WEIGHTS = {"Star": 1.0, "Premium": 0.8, "Value": 0.6, "Budget": 0.4}

# Venue character → role boost multipliers
VENUE_ROLE_BOOST = {
    "Batting Paradise": {"BAT": 1.3, "WK": 1.2, "AR": 1.1, "BOW": 0.85},
    "Batting Heaven": {"BAT": 1.3, "WK": 1.25, "AR": 1.1, "BOW": 0.8},
    "Batting-friendly": {"BAT": 1.2, "WK": 1.15, "AR": 1.1, "BOW": 0.9},
    "Spin Paradise": {"BAT": 0.9, "WK": 1.0, "AR": 1.1, "BOW": 1.3},
    "Pace-friendly": {"BAT": 0.95, "WK": 1.0, "AR": 1.05, "BOW": 1.25},
    "Balanced (Spin)": {"BAT": 1.0, "WK": 1.0, "AR": 1.1, "BOW": 1.15},
    "Balanced": {"BAT": 1.0, "WK": 1.0, "AR": 1.05, "BOW": 1.0},
}


def _get_points():
    global _POINTS
    if _POINTS is None:
        _POINTS = load_points_system()
    return _POINTS


def _get_venues():
    global _VENUES
    if _VENUES is None:
        _VENUES = load_venue_data()
    return _VENUES


def get_venue_character(venue_name: str) -> str:
    """Get the batting/bowling character of a venue."""
    venues = _get_venues()
    match = venues[venues["Venue"].str.contains(venue_name[:15], case=False, na=False)]
    if len(match) > 0:
        return match.iloc[0].get("Batting/Bowling", "Balanced")
    return "Balanced"


def get_venue_avg_score(venue_name: str) -> int:
    """Get average first innings score at a venue."""
    venues = _get_venues()
    match = venues[venues["Venue"].str.contains(venue_name[:15], case=False, na=False)]
    if len(match) > 0:
        return int(match.iloc[0].get("Avg 1st Inn Score", 160))
    return 160


def get_matchup_bonus(player: dict, venue_name: str = "") -> float:
    """
    Extra venue-role synergy bonus for extreme matchups.
    Star batsmen at batting paradises, spin bowlers at spin tracks, etc.
    Returns a multiplier (1.0 = no bonus, 1.1 = +10%).
    """
    if not venue_name:
        return 1.0

    role = player.get("RoleCode", "BAT")
    tier = player.get("Performance Tier", "Value")
    venue_char = get_venue_character(venue_name)

    bonus = 1.0

    # Star/Premium players get extra edge at their ideal venue
    if tier in ("Star", "Premium"):
        if role == "BAT" and venue_char in ("Batting Paradise", "Batting Heaven"):
            bonus = 1.10
        elif role == "BOW" and venue_char in ("Spin Paradise", "Pace-friendly"):
            bonus = 1.10
        elif role == "AR":
            # All-rounders benefit slightly everywhere — double contribution
            bonus = 1.05
        elif role == "WK" and venue_char in ("Batting Paradise", "Batting Heaven"):
            bonus = 1.07

    # Value/Budget players get a smaller matchup bonus (differential potential)
    elif tier in ("Value", "Budget"):
        if role == "BOW" and venue_char in ("Spin Paradise", "Pace-friendly"):
            bonus = 1.08  # Specialist bowler at bowler-friendly venue = high upside
        elif role == "AR":
            bonus = 1.04

    return bonus


def estimate_fantasy_points(player: dict, venue_name: str = "", platform: str = "tata_ipl") -> float:
    """
    Estimate fantasy points for a player in a given match context.

    Uses: performance tier, role, venue character, credits (as proxy for ability),
    and matchup bonus for strong venue-role synergies.
    Returns estimated base points (before captain multiplier).
    """
    role = player.get("RoleCode", "BAT")
    tier = player.get("Performance Tier", "Value")
    credits = player.get("Credits", 7.0)

    # Base score from tier and credits
    tier_weight = TIER_WEIGHTS.get(tier, 0.6)
    base_score = credits * 5 * tier_weight

    # Venue boost
    venue_char = get_venue_character(venue_name) if venue_name else "Balanced"
    role_boost = VENUE_ROLE_BOOST.get(venue_char, VENUE_ROLE_BOOST["Balanced"])
    venue_mult = role_boost.get(role, 1.0)

    # Role-specific baseline adjustments
    role_base = {"BAT": 30, "BOW": 28, "AR": 32, "WK": 27}
    base = role_base.get(role, 28)

    # Category bonuses
    category = player.get("Category", "")
    category_bonus = 0
    if category in ("Captain", "Vice-Captain"):
        category_bonus = 5
    elif category == "Retained":
        category_bonus = 3

    # Matchup bonus for strong venue-role synergies
    matchup = get_matchup_bonus(player, venue_name)

    estimated = (base + base_score + category_bonus) * venue_mult * matchup

    # Form factor (if available from scraper, default to neutral)
    form = player.get("FormFactor", 1.0)
    estimated *= form

    return round(estimated, 1)


def estimate_captain_value(player: dict, venue_name: str = "", platform: str = "tata_ipl") -> float:
    """Estimate points if this player is captain (2x multiplier)."""
    base = estimate_fantasy_points(player, venue_name, platform)
    return round(base * 2.0, 1)


def estimate_vc_value(player: dict, venue_name: str = "", platform: str = "tata_ipl") -> float:
    """Estimate points if this player is vice-captain (1.5x multiplier)."""
    base = estimate_fantasy_points(player, venue_name, platform)
    return round(base * 1.5, 1)


def points_per_credit(player: dict, venue_name: str = "", platform: str = "tata_ipl") -> float:
    """Calculate value efficiency: estimated points per credit spent."""
    pts = estimate_fantasy_points(player, venue_name, platform)
    credits = player.get("Credits", 7.0)
    if credits <= 0:
        return 0.0
    return round(pts / credits, 2)
