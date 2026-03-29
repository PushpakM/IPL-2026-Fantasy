import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_data_path(filename):
    return BASE_DIR / filename


def load_players():
    """Load all 200 players from the comprehensive player database."""
    df = pd.read_excel(get_data_path("IPL_2026_Players_Comprehensive.xlsx"), sheet_name="All Players")
    # Standardize role names for consistency
    role_map = {"Batsman": "BAT", "Bowler": "BOW", "All-rounder": "AR", "Wicketkeeper": "WK"}
    df["RoleCode"] = df["Role"].map(role_map)
    return df


def load_performance():
    """Load performance tiers and estimated fantasy credits."""
    df = pd.read_excel(
        get_data_path("IPL_2026_Players_Performance_Analysis.xlsx"),
        sheet_name="Player Performance Summary",
    )
    # Parse credit range into min/max numeric values
    if "Est. Fantasy Credits" in df.columns:
        credits = df["Est. Fantasy Credits"].astype(str).str.split("-", expand=True)
        df["CreditMin"] = pd.to_numeric(credits[0], errors="coerce")
        df["CreditMax"] = pd.to_numeric(credits.get(1, credits[0]), errors="coerce")
        df["Credits"] = ((df["CreditMin"] + df["CreditMax"]) / 2).round(1)
    return df


def load_schedule():
    """Load IPL 2026 schedule (70 league matches)."""
    df = pd.read_excel(
        get_data_path("IPL_2026_Schedule.xlsx"),
        sheet_name="IPL 2026 Schedule",
        header=2,  # Row 3 has the actual column headers
    )
    # Drop any fully empty rows and non-numeric match numbers (e.g., "LEGEND:" rows)
    df = df.dropna(subset=["Match #"])
    df["Match #"] = pd.to_numeric(df["Match #"], errors="coerce")
    df = df.dropna(subset=["Match #"])
    df["Match #"] = df["Match #"].astype(int)
    # Parse date
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y", errors="coerce")
    # Extract team1 and team2 from "RCB vs SRH" format
    teams = df["Match"].str.split(" vs ", expand=True)
    df["Team1"] = teams[0].str.strip()
    df["Team2"] = teams[1].str.strip() if 1 in teams.columns else None
    # Extract venue name (before comma)
    df["VenueName"] = df["Venue / City"].str.split(",").str[0].str.strip()
    df["Phase"] = pd.to_numeric(df["Phase"], errors="coerce")
    return df


def load_injuries():
    """Load injury tracker with status and availability info."""
    df = pd.read_excel(
        get_data_path("IPL_2026_Injury_Tracker.xlsx"),
        sheet_name="IPL 2026 Injury Tracker",
        header=2,  # Row 3 has headers
    )
    df = df.dropna(subset=["Player"])
    return df


def load_venue_data():
    """Load venue intelligence for all 10+ IPL grounds."""
    df = pd.read_excel(
        get_data_path("IPL_2026_Fantasy_Team_Builder.xlsx"),
        sheet_name="Venue Intelligence",
        header=2,  # Row 3 has headers (Venue, City, Avg 1st Inn Score, ...)
    )
    df = df.dropna(subset=["Venue"])
    return df


def load_points_system():
    """Load the fantasy points system from the rules file."""
    # This data is structured with section headers, so we return raw rows
    # for the scorer module to parse
    points = {
        "batting": {
            "playing_xi": 4,
            "per_run": 1,
            "boundary_4": 1,
            "six": 2,
            "milestone_25": 4,
            "milestone_50": 8,
            "milestone_75": 12,
            "century": 16,
            "duck": -2,
            "sr_below_50": -6,
            "sr_50_60": -4,
            "sr_60_70": -2,
            "sr_70_130": 0,
            "sr_130_150": 2,
            "sr_150_170": 4,
            "sr_170_plus": 6,
        },
        "bowling": {
            "wicket": 25,
            "bowled_lbw_bonus": 8,
            "dot_ball": 1,
            "maiden": 12,
            "haul_3w": 4,
            "haul_4w": 8,
            "haul_5w": 12,
            "econ_below_5": 6,
            "econ_5_6": 4,
            "econ_6_7": 2,
            "econ_7_10": 0,
            "econ_10_11": -2,
            "econ_11_12": -4,
            "econ_12_plus": -6,
        },
        "fielding": {
            "catch": 8,
            "catch_3_bonus": 4,
            "stumping": 12,
            "run_out_direct": 12,
            "run_out_indirect": 6,
        },
        "multipliers": {
            "captain": 2.0,
            "vice_captain": 1.5,
            "triple_captain": 3.0,
        },
    }
    return points


def load_enriched_players():
    """Load players merged with performance data and injury status."""
    players = load_players()
    performance = load_performance()
    injuries = load_injuries()

    # Merge performance data (tiers, credits)
    perf_cols = ["Player Name", "Performance Tier", "Credits", "CreditMin", "CreditMax", "Category"]
    perf_available = [c for c in perf_cols if c in performance.columns]
    merged = players.merge(
        performance[perf_available],
        on="Player Name",
        how="left",
        suffixes=("", "_perf"),
    )

    # Fill missing credits with defaults based on role
    default_credits = {"BAT": 7.0, "BOW": 6.5, "AR": 7.5, "WK": 7.0}
    for _, row in merged[merged["Credits"].isna()].iterrows():
        merged.loc[merged["Player Name"] == row["Player Name"], "Credits"] = default_credits.get(
            row["RoleCode"], 7.0
        )

    # Fill missing tiers
    merged["Performance Tier"] = merged["Performance Tier"].fillna("Value")

    # Mark injured players from the injury tracker
    injured_names = set(injuries["Player"].dropna().tolist())
    merged["IsInjured"] = merged["Player Name"].isin(injured_names)
    merged["IsAvailable"] = (merged["Availability"] == "Available") & (~merged["IsInjured"])

    return merged
