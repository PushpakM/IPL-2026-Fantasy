"""
Fantasy scoring engine for IPL 2026.

Two platform paths:
- My11Circle: tier × venue × home × intel × hot_streak × weather × form
- TATA IPL: 3-signal composite (career + form + venue/matchup) + consistency + H2H + intel × weather
"""

import pandas as pd
from core.data_loader import load_points_system, load_venue_data
from core.scraper import get_weather_for_match

# Cache points system
_POINTS = None
_VENUES = None

TIER_WEIGHTS = {"Star": 1.0, "Premium": 0.8, "Value": 0.6, "Budget": 0.4}

# Role-specific baseline points (Playing XI + typical contribution)
ROLE_BASE = {"BAT": 30, "BOW": 28, "AR": 32, "WK": 27}

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

# ============================================
# DATA INFRASTRUCTURE
# ============================================

# Venue → Home Team mapping
VENUE_HOME_TEAM = {
    "Wankhede": "MI", "DY Patil": "MI", "Brabourne": "MI",
    "Chinnaswamy": "RCB", "M. Chinnaswamy": "RCB",
    "Chepauk": "CSK", "MA Chidambaram": "CSK", "Chidambaram": "CSK",
    "Eden Gardens": "KKR", "Eden": "KKR",
    "Rajiv Gandhi": "SRH", "Uppal": "SRH",
    "Arun Jaitley": "DC", "Feroz Shah Kotla": "DC", "Kotla": "DC",
    "Narendra Modi": "GT", "Motera": "GT",
    "Sawai Mansingh": "RR", "SMS": "RR",
    "Punjab Cricket": "PBKS", "PCA": "PBKS", "Mullanpur": "PBKS", "IS Bindra": "PBKS",
    "BRSABV Ekana": "LSG", "Ekana": "LSG",
    "Barsapara": None,  # Neutral (Guwahati)
    "Dharamsala": None, "HPCA": None,  # Neutral
    "ACA-VDCA": None, "Barabati": None,
}

# Bowling style lookup for known players (bowlers + all-rounders)
BOWLING_STYLE_MAP = {
    # CSK
    "Ravindra Jadeja": "left-arm orthodox", "Deepak Chahar": "right-arm fast-medium",
    "Tushar Deshpande": "right-arm fast-medium", "Maheesh Theekshana": "off-spin",
    "Matheesha Pathirana": "right-arm fast", "Khaleel Ahmed": "left-arm fast-medium",
    "Rachin Ravindra": "left-arm orthodox", "Ravichandran Ashwin": "off-spin",
    "Noor Ahmad": "left-arm wrist-spin",
    # MI
    "Jasprit Bumrah": "right-arm fast", "Trent Boult": "left-arm fast",
    "Hardik Pandya": "right-arm fast-medium", "AM Ghazanfar": "off-spin",
    "Mayank Markande": "leg-spin", "Shardul Thakur": "right-arm fast-medium",
    "Naman Dhir": "right-arm medium",
    # RCB
    "Josh Hazlewood": "right-arm fast", "Bhuvneshwar Kumar": "right-arm fast-medium",
    "Liam Livingstone": "leg-spin", "Krunal Pandya": "left-arm orthodox",
    "Suyash Sharma": "leg-spin", "Rasikh Salam": "right-arm fast",
    "Swapnil Singh": "left-arm orthodox",
    # KKR
    "Varun Chakaravarthy": "right-arm leg-spin", "Sunil Narine": "off-spin",
    "Anukul Roy": "left-arm orthodox", "Vaibhav Arora": "right-arm fast-medium",
    "Blessing Muzarabani": "right-arm fast", "Umran Malik": "right-arm fast",
    "Cameron Green": "right-arm fast-medium", "Ramandeep Singh": "right-arm medium",
    # SRH
    "Pat Cummins": "right-arm fast", "Mohammed Shami": "right-arm fast-medium",
    "Harshal Patel": "right-arm fast-medium", "Adam Zampa": "leg-spin",
    "Abhishek Sharma": "left-arm orthodox", "Washington Sundar": "off-spin",
    "T Natarajan": "left-arm fast-medium",
    # DC
    "Axar Patel": "left-arm orthodox", "Mitchell Starc": "left-arm fast",
    "Kuldeep Yadav": "left-arm wrist-spin", "Mukesh Kumar": "right-arm fast-medium",
    "Kamlesh Nagarkoti": "right-arm fast", "Ashutosh Sharma": "right-arm medium",
    # RR
    "Sandeep Sharma": "right-arm fast-medium", "Trent Boult": "left-arm fast",
    "Yuzvendra Chahal": "leg-spin", "Wanindu Hasaranga": "leg-spin",
    "Jaydev Unadkat": "left-arm fast-medium", "Manoj Bhandage": "left-arm fast-medium",
    "Jofra Archer": "right-arm fast",
    # PBKS
    "Arshdeep Singh": "left-arm fast-medium", "Yuzvendra Chahal": "leg-spin",
    "Harpreet Brar": "left-arm orthodox", "Marco Jansen": "left-arm fast",
    "Lockie Ferguson": "right-arm fast", "Vishnu Vinod": "right-arm off-spin",
    # GT
    "Rashid Khan": "leg-spin", "Mohammed Siraj": "right-arm fast",
    "Kagiso Rabada": "right-arm fast", "Nishant Sindhu": "left-arm orthodox",
    "Prasidh Krishna": "right-arm fast", "Rahul Tewatia": "leg-spin",
    # LSG
    "Ravi Bishnoi": "leg-spin", "Shahbaz Ahmed": "left-arm orthodox",
    "Mohsin Khan": "left-arm fast-medium", "Avesh Khan": "right-arm fast",
    "Mitchell Marsh": "right-arm fast-medium", "David Miller": "right-arm off-spin",
}

# Tier-based form estimates (when FormFactor is default 1.0 / not yet tracked)
TIER_FORM_ESTIMATE = {
    "Star": 1.12, "Premium": 1.05, "Value": 0.95, "Budget": 0.88,
}

# Consistency bonus by tier (pts)
CONSISTENCY_BONUS = {"Star": 8, "Premium": 4, "Value": 0, "Budget": -5}


# ============================================
# HELPER FUNCTIONS
# ============================================

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


def get_effective_tier(player: dict) -> str:
    """Return 4-tier classification. Splits Value into Value + Budget based on credits."""
    tier = player.get("Performance Tier", "Value")
    if tier == "Value" and player.get("Credits", 7.0) <= 6.5:
        return "Budget"
    return tier


def get_bowling_style(player: dict) -> str:
    """Get bowling style from static map, with role-based fallback."""
    name = player.get("Player Name", "")
    if name in BOWLING_STYLE_MAP:
        return BOWLING_STYLE_MAP[name]
    role = player.get("RoleCode", "BAT")
    if role == "BOW":
        return "right-arm fast-medium"
    if role == "AR":
        return "right-arm medium"
    return ""


def _is_pace_bowler(bowling_style: str) -> bool:
    """Check if bowling style indicates pace bowling."""
    pace_keywords = ["fast", "medium", "pace"]
    spin_keywords = ["spin", "leg", "off", "orthodox", "slow", "wrist"]
    style_lower = bowling_style.lower()
    if any(s in style_lower for s in spin_keywords):
        return False
    return any(p in style_lower for p in pace_keywords) or not style_lower


def _is_spinner(bowling_style: str) -> bool:
    """Check if bowling style indicates spin bowling."""
    spin_keywords = ["spin", "leg", "off", "orthodox", "slow", "wrist"]
    return any(s in bowling_style.lower() for s in spin_keywords)


# ============================================
# VENUE & CONDITIONS
# ============================================

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


def get_home_ground_bonus(player: dict, venue_name: str) -> float:
    """
    +5% if player's team is the home team at this venue.
    Home teams benefit from crowd support and familiarity with conditions.
    """
    if not venue_name:
        return 1.0
    player_team = player.get("Team", "")
    for key, home_team in VENUE_HOME_TEAM.items():
        if key.lower() in venue_name.lower() and home_team == player_team:
            return 1.05
    return 1.0


def get_matchup_bonus(player: dict, venue_name: str = "") -> float:
    """
    Extra venue-role synergy bonus for extreme matchups.
    Star batsmen at batting paradises, spin bowlers at spin tracks, etc.
    """
    if not venue_name:
        return 1.0

    role = player.get("RoleCode", "BAT")
    tier = get_effective_tier(player)
    venue_char = get_venue_character(venue_name)

    bonus = 1.0
    if tier in ("Star", "Premium"):
        if role == "BAT" and venue_char in ("Batting Paradise", "Batting Heaven"):
            bonus = 1.10
        elif role == "BOW" and venue_char in ("Spin Paradise", "Pace-friendly"):
            bonus = 1.10
        elif role == "AR":
            bonus = 1.05
        elif role == "WK" and venue_char in ("Batting Paradise", "Batting Heaven"):
            bonus = 1.07
    elif tier in ("Value", "Budget"):
        if role == "BOW" and venue_char in ("Spin Paradise", "Pace-friendly"):
            bonus = 1.08
        elif role == "AR":
            bonus = 1.04

    return bonus


# ============================================
# WEATHER MULTIPLIER
# ============================================

def get_weather_multiplier(player: dict, venue_name: str = "", weather: dict = None) -> float:
    """Weather-based scoring multiplier using bowling style lookup."""
    if not weather or not weather.get("fantasy_impact"):
        return 1.0

    impact = weather["fantasy_impact"]
    role = player.get("RoleCode", "BAT")
    bowling_style = get_bowling_style(player).lower()

    multiplier = 1.0

    # Dew benefit — batting-side players benefit
    batting_factor = impact.get("batting_factor", 1.0)
    if role in ("BAT", "WK"):
        multiplier *= batting_factor
    elif role == "AR":
        multiplier *= (1 + (batting_factor - 1) * 0.5)

    # Swing factor — pace bowlers benefit from humid/overcast conditions
    swing = impact.get("swing_factor", 1.0)
    is_pace = _is_pace_bowler(bowling_style)
    is_spin = _is_spinner(bowling_style)

    if role == "BOW" and is_pace:
        multiplier *= swing
    elif role == "AR" and is_pace:
        multiplier *= (1 + (swing - 1) * 0.5)

    # Spin factor — spinners benefit from dry, hot conditions
    spin = impact.get("spin_factor", 1.0)
    if role == "BOW" and is_spin:
        multiplier *= spin
    elif role == "AR" and is_spin:
        multiplier *= (1 + (spin - 1) * 0.5)

    # Pace factor from wind
    pace = impact.get("pace_factor", 1.0)
    if role == "BOW" and is_pace:
        multiplier *= pace

    return round(multiplier, 3)


# ============================================
# INTEL MULTIPLIER (5-dimension, ±15%)
# ============================================

def calculate_intel_multiplier(
    player: dict,
    venue_name: str = "",
    opposing_team: str = "",
    toss_info: dict = None,
    all_players: list = None,
) -> dict:
    """
    5-dimension contextual intelligence multiplier.
    Each dimension: -3% to +3%. Combined: ±15%, clamped [0.85, 1.15].

    Dimensions:
    1. Form trend — FormFactor mapped to [-0.03, +0.03]
    2. Venue history — derived from venue-role boost strength
    3. H2H estimate — role matchup vs opposing team composition
    4. Pitch/toss fit — venue character + toss decision synergy
    5. Skill tags — bowling style specialist bonus
    """
    dims = {}
    role = player.get("RoleCode", "BAT")
    tier = get_effective_tier(player)
    bowling_style = get_bowling_style(player).lower()

    # --- Dim 1: Form Trend ---
    form = player.get("FormFactor", 1.0)
    # Map [0.5, 1.5] → [-0.03, +0.03]
    dims["form_trend"] = max(-0.03, min(0.03, (form - 1.0) * 0.06))

    # --- Dim 2: Venue History Estimate ---
    venue_char = get_venue_character(venue_name) if venue_name else "Balanced"
    role_boost = VENUE_ROLE_BOOST.get(venue_char, VENUE_ROLE_BOOST["Balanced"])
    venue_boost_val = role_boost.get(role, 1.0)
    # Map [0.8, 1.3] → [-0.03, +0.03]
    dims["venue_history"] = max(-0.03, min(0.03, (venue_boost_val - 1.05) * 0.12))

    # --- Dim 3: H2H Estimate ---
    h2h = 0.0
    if opposing_team and all_players:
        opp_players = [p for p in all_players if p.get("Team") == opposing_team]
        opp_stars = sum(1 for p in opp_players if get_effective_tier(p) in ("Star", "Premium"))
        opp_bat_count = sum(1 for p in opp_players if p.get("RoleCode") in ("BAT", "WK") and get_effective_tier(p) in ("Star", "Premium"))
        opp_bow_count = sum(1 for p in opp_players if p.get("RoleCode") == "BOW" and get_effective_tier(p) in ("Star", "Premium"))

        if role == "BOW":
            # Bowlers do well against batting-heavy teams (more runs = more wicket opportunities)
            h2h = min(0.03, opp_bat_count * 0.008)
        elif role in ("BAT", "WK"):
            # Batsmen face tougher time against bowling-heavy teams
            h2h = max(-0.03, -opp_bow_count * 0.006)
        elif role == "AR":
            # All-rounders always get a small positive
            h2h = 0.01
    dims["h2h_estimate"] = max(-0.03, min(0.03, h2h))

    # --- Dim 4: Pitch/Toss Fit ---
    toss_fit = 0.0
    if toss_info and toss_info.get("winner"):
        decision = toss_info.get("decision", "").lower()
        player_team = player.get("Team", "")

        if decision in ("bat", "batting"):
            # Toss winner bats first → batsmen from that team benefit
            if venue_char in ("Batting Paradise", "Batting Heaven", "Batting-friendly"):
                if role in ("BAT", "WK") and player_team == toss_info["winner"]:
                    toss_fit = 0.025
                elif role == "BOW" and player_team != toss_info["winner"]:
                    toss_fit = 0.015  # Bowling team bowlers get wickets
        elif decision in ("bowl", "field", "bowling"):
            # Toss winner bowls first → bowlers from that team benefit
            if venue_char in ("Pace-friendly", "Spin Paradise"):
                if role == "BOW" and player_team == toss_info["winner"]:
                    toss_fit = 0.025
                elif role in ("BAT", "WK") and player_team != toss_info["winner"]:
                    toss_fit = 0.015  # Chasing batsmen benefit from dew
    dims["toss_fit"] = max(-0.03, min(0.03, toss_fit))

    # --- Dim 5: Skill Tags ---
    skill = 0.0
    if role == "AR":
        skill = 0.01  # Dual contribution always a slight edge
    if role == "BOW":
        if _is_pace_bowler(bowling_style) and venue_char in ("Pace-friendly",):
            skill = 0.02  # Death bowler at pace-friendly
        elif _is_spinner(bowling_style) and venue_char in ("Spin Paradise", "Balanced (Spin)"):
            skill = 0.02  # Specialist spinner at spin venue
        elif _is_pace_bowler(bowling_style) and venue_char in ("Batting Paradise", "Batting Heaven"):
            skill = -0.02  # Pace bowler at flat batting track
    if tier == "Star":
        skill += 0.005  # Stars have more skills/adaptability
    dims["skill_tags"] = max(-0.03, min(0.03, skill))

    # --- Combined ---
    combined = 1.0 + sum(dims.values())
    combined = max(0.85, min(1.15, combined))

    return {**dims, "combined": round(combined, 4)}


# ============================================
# CONSISTENCY & H2H BONUSES
# ============================================

def get_consistency_bonus(player: dict) -> float:
    """
    Star players are more consistent, Budget players are volatile.
    Returns bonus points: Star +8, Premium +4, Value 0, Budget -5.
    """
    tier = get_effective_tier(player)
    return CONSISTENCY_BONUS.get(tier, 0)


def get_h2h_bonus(player: dict, opposing_team: str = "", all_players: list = None) -> float:
    """
    Estimate head-to-head advantage from role matchups.
    BOW vs batting-heavy team → up to +12
    BAT vs bowling-heavy team → up to -8
    AR always moderate positive.
    Returns points in range [-12, +12].
    """
    if not opposing_team or not all_players:
        return 0.0

    role = player.get("RoleCode", "BAT")
    opp = [p for p in all_players if p.get("Team") == opposing_team]

    if not opp:
        return 0.0

    # Count opposing team's star/premium by role
    opp_strong_bat = sum(1 for p in opp if p.get("RoleCode") in ("BAT", "WK") and get_effective_tier(p) in ("Star", "Premium"))
    opp_strong_bow = sum(1 for p in opp if p.get("RoleCode") == "BOW" and get_effective_tier(p) in ("Star", "Premium"))

    if role == "BOW":
        # More strong batsmen → more runs → more wicket opportunities
        return min(12, opp_strong_bat * 3.0)
    elif role in ("BAT", "WK"):
        # More strong bowlers → harder to score
        return max(-8, -opp_strong_bow * 2.5)
    elif role == "AR":
        # All-rounders benefit from both: bowl at batsmen + bat against bowlers
        return min(8, opp_strong_bat * 1.5 + max(0, 2 - opp_strong_bow))
    return 0.0


# ============================================
# HOT STREAK DETECTION
# ============================================

def get_hot_streak_multiplier(player: dict) -> float:
    """
    If FormFactor > 1.15, player is on a hot streak → 1.10x.
    If FormFactor < 0.85, player is cold → 0.95x.
    Otherwise 1.0.
    """
    form = player.get("FormFactor", 1.0)
    if form > 1.15:
        return 1.10
    elif form < 0.85:
        return 0.95
    return 1.0


# ============================================
# MAIN SCORING FUNCTIONS
# ============================================

def estimate_fantasy_points(
    player: dict,
    venue_name: str = "",
    platform: str = "tata_ipl",
    weather: dict = None,
    opposing_team: str = "",
    toss_info: dict = None,
    all_players: list = None,
) -> float:
    """
    Estimate fantasy points for a player.
    Routes to platform-specific scoring: My11Circle vs TATA IPL.
    """
    # Fetch weather if not provided
    if weather is None and venue_name:
        weather = get_weather_for_match(venue_name)

    if platform == "my11circle":
        return _estimate_my11circle(player, venue_name, weather, opposing_team, toss_info, all_players)
    else:
        return _estimate_tata_ipl(player, venue_name, weather, opposing_team, toss_info, all_players)


def _estimate_my11circle(
    player: dict, venue_name: str, weather: dict,
    opposing_team: str, toss_info: dict, all_players: list,
) -> float:
    """
    My11Circle scoring: tier × venue × home × matchup × intel × hot_streak × weather × form
    Fresh team every match — maximize THIS match points.
    """
    role = player.get("RoleCode", "BAT")
    tier = get_effective_tier(player)
    credits = player.get("Credits", 7.0)

    # Base score
    tier_weight = TIER_WEIGHTS.get(tier, 0.6)
    base_score = credits * 5 * tier_weight
    base = ROLE_BASE.get(role, 28)

    # Category bonus
    category = player.get("Category", "")
    category_bonus = 5 if category in ("Captain", "Vice-Captain") else (3 if category == "Retained" else 0)

    # Multipliers
    venue_char = get_venue_character(venue_name) if venue_name else "Balanced"
    role_boost = VENUE_ROLE_BOOST.get(venue_char, VENUE_ROLE_BOOST["Balanced"])
    venue_mult = role_boost.get(role, 1.0)

    matchup = get_matchup_bonus(player, venue_name)
    home_bonus = get_home_ground_bonus(player, venue_name)

    intel = calculate_intel_multiplier(player, venue_name, opposing_team, toss_info, all_players)
    intel_mult = intel["combined"]

    hot_streak = get_hot_streak_multiplier(player)
    weather_mult = get_weather_multiplier(player, venue_name, weather)
    form = player.get("FormFactor", 1.0)

    estimated = (base + base_score + category_bonus) * venue_mult * matchup * home_bonus
    estimated *= intel_mult * hot_streak * weather_mult * form

    return round(estimated, 1)


def _estimate_tata_ipl(
    player: dict, venue_name: str, weather: dict,
    opposing_team: str, toss_info: dict, all_players: list,
) -> float:
    """
    TATA IPL scoring: 3-signal composite.
    Score = 0.35 × Career Baseline + 0.40 × Recent Form + 0.25 × Venue/Matchup Fit
    + ConsistencyBonus + H2H Bonus
    × Intel × Hot Streak × Weather
    """
    role = player.get("RoleCode", "BAT")
    tier = get_effective_tier(player)
    credits = player.get("Credits", 7.0)

    # --- Signal 1: Career Baseline (0.35) ---
    tier_weight = TIER_WEIGHTS.get(tier, 0.6)
    base = ROLE_BASE.get(role, 28)
    category = player.get("Category", "")
    category_bonus = 5 if category in ("Captain", "Vice-Captain") else (3 if category == "Retained" else 0)
    career_baseline = base + credits * 5 * tier_weight + category_bonus

    # --- Signal 2: Recent Form (0.40) ---
    form_factor = player.get("FormFactor", 1.0)
    # If FormFactor is default (no real data yet), use tier-based estimate
    if form_factor == 1.0:
        form_factor = TIER_FORM_ESTIMATE.get(tier, 0.95)
    recent_form = career_baseline * form_factor

    # --- Signal 3: Venue/Matchup Fit (0.25) ---
    venue_char = get_venue_character(venue_name) if venue_name else "Balanced"
    role_boost = VENUE_ROLE_BOOST.get(venue_char, VENUE_ROLE_BOOST["Balanced"])
    venue_mult = role_boost.get(role, 1.0)
    matchup = get_matchup_bonus(player, venue_name)
    home_bonus = get_home_ground_bonus(player, venue_name)
    venue_matchup = career_baseline * venue_mult * matchup * home_bonus

    # --- 3-Signal Composite ---
    composite = 0.35 * career_baseline + 0.40 * recent_form + 0.25 * venue_matchup

    # --- Additive Bonuses ---
    composite += get_consistency_bonus(player)
    composite += get_h2h_bonus(player, opposing_team, all_players)

    # --- Multiplicative Factors ---
    intel = calculate_intel_multiplier(player, venue_name, opposing_team, toss_info, all_players)
    composite *= intel["combined"]
    composite *= get_hot_streak_multiplier(player)
    composite *= get_weather_multiplier(player, venue_name, weather)

    return round(composite, 1)


# ============================================
# CAPTAIN / VC / EFFICIENCY
# ============================================

def estimate_captain_value(player: dict, venue_name: str = "", platform: str = "tata_ipl", **kwargs) -> float:
    """Estimate points if this player is captain (2x multiplier)."""
    base = estimate_fantasy_points(player, venue_name, platform, **kwargs)
    return round(base * 2.0, 1)


def estimate_vc_value(player: dict, venue_name: str = "", platform: str = "tata_ipl", **kwargs) -> float:
    """Estimate points if this player is vice-captain (1.5x multiplier)."""
    base = estimate_fantasy_points(player, venue_name, platform, **kwargs)
    return round(base * 1.5, 1)


def points_per_credit(player: dict, venue_name: str = "", platform: str = "tata_ipl", **kwargs) -> float:
    """Calculate value efficiency: estimated points per credit spent."""
    pts = estimate_fantasy_points(player, venue_name, platform, **kwargs)
    credits = player.get("Credits", 7.0)
    if credits <= 0:
        return 0.0
    return round(pts / credits, 2)
