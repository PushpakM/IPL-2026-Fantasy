from typing import Dict, List, Tuple

# Platform-specific team composition rules
PLATFORM_RULES = {
    "my11circle": {
        "total_players": 11,
        "roles": {"WK": (1, 4), "BAT": (3, 6), "AR": (1, 4), "BOW": (3, 6)},
        "max_per_team": 7,
        "max_overseas": 4,
        "credit_budget": 100,
    },
    "tata_ipl": {
        "total_players": 11,
        "roles": {"WK": (1, 2), "BAT": (3, 5), "AR": (1, 3), "BOW": (3, 5)},
        "max_per_team": 7,
        "max_overseas": 4,
        "credit_budget": 100,
    },
}


def validate_team(players: list, platform: str = "tata_ipl") -> Tuple[bool, List[str]]:
    """
    Validate a fantasy team against platform rules.

    Args:
        players: list of dicts, each with keys: Player Name, Team, RoleCode, Credits, IsAvailable
        platform: 'my11circle' or 'tata_ipl'

    Returns:
        (is_valid, list of error messages)
    """
    rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["tata_ipl"])
    errors = []

    # Total player count
    if len(players) != rules["total_players"]:
        errors.append(f"Need exactly {rules['total_players']} players, got {len(players)}")

    # Role composition
    role_counts = {}
    for p in players:
        role = p.get("RoleCode", "BAT")
        role_counts[role] = role_counts.get(role, 0) + 1

    for role, (min_count, max_count) in rules["roles"].items():
        actual = role_counts.get(role, 0)
        if actual < min_count:
            errors.append(f"{role}: need at least {min_count}, got {actual}")
        if actual > max_count:
            errors.append(f"{role}: max {max_count}, got {actual}")

    # Max players from one team
    team_counts = {}
    for p in players:
        team = p.get("Team", "")
        team_counts[team] = team_counts.get(team, 0) + 1
    for team, count in team_counts.items():
        if count > rules["max_per_team"]:
            errors.append(f"Max {rules['max_per_team']} from {team}, got {count}")

    # Credit budget
    total_credits = sum(p.get("Credits", 0) for p in players)
    if total_credits > rules["credit_budget"]:
        errors.append(f"Credit budget exceeded: {total_credits:.1f} / {rules['credit_budget']}")

    # Availability check
    unavailable = [p["Player Name"] for p in players if not p.get("IsAvailable", True)]
    if unavailable:
        errors.append(f"Unavailable players selected: {', '.join(unavailable)}")

    return len(errors) == 0, errors


def get_valid_role_combinations(platform: str = "tata_ipl") -> List[Dict[str, int]]:
    """
    Generate all valid role count combinations for a platform.
    Returns list of dicts like {'WK': 1, 'BAT': 4, 'AR': 2, 'BOW': 4}.
    """
    rules = PLATFORM_RULES[platform]["roles"]
    total = PLATFORM_RULES[platform]["total_players"]
    combos = []

    roles = list(rules.keys())
    ranges = [range(rules[r][0], rules[r][1] + 1) for r in roles]

    def _generate(idx, current, remaining):
        if idx == len(roles):
            if remaining == 0:
                combos.append(dict(zip(roles, current)))
            return
        min_v, max_v = rules[roles[idx]]
        for v in range(min_v, min(max_v, remaining) + 1):
            _generate(idx + 1, current + [v], remaining - v)

    _generate(0, [], total)
    return combos
