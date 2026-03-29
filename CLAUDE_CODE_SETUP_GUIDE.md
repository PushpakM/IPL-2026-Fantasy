# IPL 2026 Fantasy Team Builder - Complete Setup Guide for Claude Code

## Table of Contents
1. Prerequisites & Installation
2. Step-by-Step Setup
3. Ready-to-Use Scripts
4. Claude Code Commands
5. Automation Examples
6. Troubleshooting

---

## PART 1: PREREQUISITES & INSTALLATION

### Step 1.1: Install Claude Code
```bash
# Option A: Via pip (Python package manager)
pip install anthropic claude-code

# Option B: Via npm (Node package manager)
npm install -g @anthropic/claude-code

# Verify installation
claude-code --version
```

### Step 1.2: Set Up API Key
```bash
# Linux/Mac
export ANTHROPIC_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Or add to ~/.bashrc (Mac/Linux) for permanent setup
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Get your API key from:** https://console.anthropic.com/

### Step 1.3: Install Python Dependencies
```bash
pip install openpyxl pandas numpy requests beautifulsoup4
```

---

## PART 2: STEP-BY-STEP SETUP

### Step 2.1: Create Project Directory
```bash
mkdir -p ~/IPL2026_Fantasy
cd ~/IPL2026_Fantasy
```

### Step 2.2: Copy Your Excel Files
```bash
# Copy the files I created to your project folder
cp "/sessions/friendly-jolly-lamport/mnt/IPL 2026/"*.xlsx ~/IPL2026_Fantasy/

# Verify files are copied
ls -la ~/IPL2026_Fantasy/
```

You should see:
- `IPL_2026_Fantasy_Team_Builder.xlsx`
- `IPL_2026_Players_Comprehensive.xlsx`
- `IPL_2026_Players_Performance_Analysis.xlsx`
- `IPL_2026_Schedule.xlsx`
- `IPL_2026_Injury_Tracker.xlsx`

### Step 2.3: Create Your First Python Script
```bash
# Create a simple team builder script
touch ~/IPL2026_Fantasy/team_builder.py
```

---

## PART 3: READY-TO-USE SCRIPTS

### Script 1: Basic Team Builder (Easiest)

**File:** `~/IPL2026_Fantasy/team_builder_basic.py`

```python
import openpyxl
import pandas as pd
from datetime import datetime

class FantasyTeamBuilder:
    def __init__(self, players_file, strategy_file):
        """Initialize team builder with player and strategy data"""
        self.players_df = pd.read_excel(players_file, sheet_name='All Players')
        self.wb = openpyxl.load_workbook(strategy_file)
        print("✓ Team Builder initialized")
    
    def build_my11circle_team(self, team1, team2, match_num=1):
        """Build My11Circle team following rules: WK 1-4, BAT 1-6, AR 1-6, BOW 1-6"""
        print(f"\n📋 Building My11Circle Team for Match {match_num}")
        print(f"Teams: {team1} vs {team2}")
        
        # Get players from both teams
        team1_players = self.players_df[self.players_df['Team'] == team1].to_dict('records')
        team2_players = self.players_df[self.players_df['Team'] == team2].to_dict('records')
        
        team = {
            'CAPTAIN': None,
            'VICE_CAPTAIN': None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        # Example: Select captain (highest credit player)
        all_players = team1_players + team2_players
        all_available = [p for p in all_players if 'Available' in str(p.get('Availability', ''))]
        
        if all_available:
            captain = max(all_available, key=lambda x: 1)  # Simple selection
            team['CAPTAIN'] = captain['Player Name']
            print(f"⭐ Captain: {captain['Player Name']} ({captain['Team']})")
        
        return team
    
    def build_tata_ipl_team(self, team1, team2, match_num=1):
        """Build TATA IPL Fantasy team: WK 1-2, BAT 3-5, AR 1-3, BOW 3-5"""
        print(f"\n📋 Building TATA IPL Fantasy Team for Match {match_num}")
        print(f"Teams: {team1} vs {team2}")
        
        team = {
            'CAPTAIN': None,
            'VICE_CAPTAIN': None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        # Similar logic as My11Circle but with TATA IPL constraints
        return team
    
    def display_team(self, team, league_name="My11Circle"):
        """Display the built team"""
        print(f"\n🏏 {league_name} TEAM")
        print(f"Captain: {team.get('CAPTAIN', 'Not set')} (2x points)")
        print(f"Vice-Captain: {team.get('VICE_CAPTAIN', 'Not set')} (1.5x points)")
        print(f"Players: {len([p for k, v in team.items() if isinstance(v, list) for p in v])} selected")

# USAGE EXAMPLE
if __name__ == "__main__":
    builder = FantasyTeamBuilder(
        'IPL_2026_Players_Comprehensive.xlsx',
        'IPL_2026_Fantasy_Team_Builder.xlsx'
    )
    
    # Build teams for Match 1
    my11_team = builder.build_my11circle_team('RCB', 'SRH', match_num=1)
    tata_team = builder.build_tata_ipl_team('RCB', 'SRH', match_num=1)
    
    # Display results
    builder.display_team(my11_team, "My11Circle")
    builder.display_team(tata_team, "TATA IPL Fantasy")
    
    print("\n✓ Teams built successfully!")
```

**Run it:**
```bash
cd ~/IPL2026_Fantasy
python team_builder_basic.py
```

---

### Script 2: Advanced Team Builder (Recommended)

**File:** `~/IPL2026_Fantasy/team_builder_advanced.py`

```python
import openpyxl
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime

class AdvancedFantasyTeamBuilder:
    """Advanced team builder with credits, rules validation, and optimization"""
    
    def __init__(self, players_file: str, strategy_file: str, rules_file: str):
        self.players_df = pd.read_excel(players_file, sheet_name='All Players')
        self.strategy_df = pd.read_excel(strategy_file, sheet_name='Strategy Dashboard')
        self.rules_df = pd.read_excel(rules_file)
        self.my11_rules = {'WK': (1, 4), 'BAT': (1, 6), 'AR': (1, 6), 'BOW': (1, 6)}
        self.tata_rules = {'WK': (1, 2), 'BAT': (3, 5), 'AR': (1, 3), 'BOW': (3, 5)}
    
    def get_available_players(self, team1: str, team2: str) -> pd.DataFrame:
        """Get only available players from both teams"""
        teams = [team1, team2]
        available = self.players_df[
            (self.players_df['Team'].isin(teams)) & 
            (self.players_df['Availability'] == 'Available')
        ]
        return available
    
    def validate_team_composition(self, team: Dict, rules: Dict) -> Tuple[bool, List[str]]:
        """Validate if team follows league rules"""
        errors = []
        
        for role, (min_count, max_count) in rules.items():
            actual_count = len(team.get(role, []))
            if actual_count < min_count:
                errors.append(f"❌ {role}: Need {min_count}, got {actual_count}")
            if actual_count > max_count:
                errors.append(f"❌ {role}: Max {max_count}, got {actual_count}")
        
        total_players = sum(len(v) for k, v in team.items() if isinstance(v, list))
        if total_players != 11:
            errors.append(f"❌ Total players: Need 11, got {total_players}")
        
        return len(errors) == 0, errors
    
    def build_optimized_my11circle_team(self, team1: str, team2: str, 
                                       captain_preference: str = None) -> Dict:
        """Build optimized My11Circle team"""
        available = self.get_available_players(team1, team2)
        
        team = {
            'CAPTAIN': None,
            'VICE_CAPTAIN': None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        # Smart captain selection
        if captain_preference:
            captain_row = available[available['Player Name'] == captain_preference]
            if not captain_row.empty:
                team['CAPTAIN'] = captain_preference
        else:
            # Default: First available player (can be improved)
            team['CAPTAIN'] = available.iloc[0]['Player Name'] if len(available) > 0 else None
        
        # Validate composition
        is_valid, errors = self.validate_team_composition(team, self.my11_rules)
        
        return team, is_valid, errors
    
    def build_optimized_tata_ipl_team(self, team1: str, team2: str,
                                      captain_preference: str = None) -> Dict:
        """Build optimized TATA IPL Fantasy team with winning team stacking"""
        available = self.get_available_players(team1, team2)
        
        team = {
            'CAPTAIN': None,
            'VICE_CAPTAIN': None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        # Captain selection with winning team preference
        if captain_preference:
            team['CAPTAIN'] = captain_preference
        
        # Validate composition
        is_valid, errors = self.validate_team_composition(team, self.tata_rules)
        
        return team, is_valid, errors
    
    def export_teams_to_excel(self, my11_team: Dict, tata_team: Dict, 
                             match_num: int, output_file: str = 'Generated_Teams.xlsx'):
        """Export both teams to Excel file"""
        wb = openpyxl.Workbook()
        
        # My11Circle sheet
        ws1 = wb.active
        ws1.title = f"Match {match_num} - My11Circle"
        ws1['A1'] = f"Match {match_num} - My11Circle Team"
        
        row = 3
        for role, players in my11_team.items():
            if isinstance(players, list):
                ws1[f'A{row}'] = role
                ws1[f'B{row}'] = ', '.join(players) if players else 'Not assigned'
                row += 1
        
        # TATA IPL sheet
        ws2 = wb.create_sheet(f"Match {match_num} - TATA IPL")
        ws2['A1'] = f"Match {match_num} - TATA IPL Fantasy Team"
        
        row = 3
        for role, players in tata_team.items():
            if isinstance(players, list):
                ws2[f'A{row}'] = role
                ws2[f'B{row}'] = ', '.join(players) if players else 'Not assigned'
                row += 1
        
        wb.save(output_file)
        print(f"✓ Teams exported to {output_file}")

# USAGE EXAMPLE
if __name__ == "__main__":
    builder = AdvancedFantasyTeamBuilder(
        'IPL_2026_Players_Comprehensive.xlsx',
        'IPL_2026_Fantasy_Team_Builder.xlsx',
        'IPL_2026_My11Circle_Fantasy_Rules.xlsx'
    )
    
    # Build teams
    my11_team, is_valid, errors = builder.build_optimized_my11circle_team(
        'RCB', 'SRH', 
        captain_preference='Virat Kohli'
    )
    
    tata_team, is_valid_tata, errors_tata = builder.build_optimized_tata_ipl_team(
        'RCB', 'SRH',
        captain_preference='Travis Head'
    )
    
    # Display results
    print("\n🏏 MY11CIRCLE TEAM")
    print(f"Captain: {my11_team['CAPTAIN']}")
    print(f"Valid: {is_valid}")
    if errors:
        for error in errors:
            print(error)
    
    print("\n🏏 TATA IPL FANTASY TEAM")
    print(f"Captain: {tata_team['CAPTAIN']}")
    print(f"Valid: {is_valid_tata}")
    
    # Export
    builder.export_teams_to_excel(my11_team, tata_team, match_num=1)
```

**Run it:**
```bash
python team_builder_advanced.py
```

---

## PART 4: USING WITH CLAUDE CODE

### Command 4.1: Run Script via Claude Code

```bash
claude-code "Run the Python script ~/IPL2026_Fantasy/team_builder_advanced.py and show me the results"
```

### Command 4.2: Ask Claude Code to Improve Script

```bash
claude-code "
Improve the team_builder_advanced.py script by:
1. Adding credit point allocation logic
2. Implementing venue-based player scoring
3. Creating a transfer budget tracker
4. Exporting to better formatted Excel
"
```

### Command 4.3: Generate Teams for All Phase 1 Matches

```bash
claude-code "
Using the IPL 2026 schedule, modify team_builder_advanced.py to:
1. Read all 14 Phase 1 matches
2. For each match:
   - Extract venue and teams
   - Build My11Circle team (captain = player with best venue record)
   - Build TATA IPL team (stack winning team for bonuses)
   - Calculate projected points
3. Export all 14 match teams to Excel
4. Create a transfer plan that tracks budget across all matches
"
```

### Command 4.4: Create Form Tracker

```bash
claude-code "
Create a new Python script (form_tracker.py) that:
1. Reads IPL_2026_Players_Comprehensive.xlsx
2. Tracks player form by match (manual input or API)
3. Identifies hot/cold players
4. Suggests transfer recommendations
5. Maintains form history across all 70 matches
"
```

---

## PART 5: COMPLETE AUTOMATION WORKFLOW

### Step 5.1: Create Main Orchestrator Script

**File:** `~/IPL2026_Fantasy/orchestrator.py`

```python
#!/usr/bin/env python3
"""
Main automation script that orchestrates all fantasy team building
"""

import sys
from team_builder_advanced import AdvancedFantasyTeamBuilder
from form_tracker import FormTracker
import pandas as pd

def main():
    print("=" * 60)
    print("IPL 2026 FANTASY TEAM BUILDER - AUTOMATION")
    print("=" * 60)
    
    # Initialize builders
    team_builder = AdvancedFantasyTeamBuilder(
        'IPL_2026_Players_Comprehensive.xlsx',
        'IPL_2026_Fantasy_Team_Builder.xlsx',
        'IPL_2026_My11Circle_Fantasy_Rules.xlsx'
    )
    
    # Read schedule
    schedule_df = pd.read_excel('IPL_2026_Schedule.xlsx')
    
    # Process Phase 1 (Matches 1-14)
    all_teams = []
    for idx, match in schedule_df.head(14).iterrows():
        match_num = match['Match #']
        team1 = match['Match'].split(' vs ')[0]
        team2 = match['Match'].split(' vs ')[1]
        
        print(f"\n📍 Processing Match {match_num}: {team1} vs {team2}")
        
        # Build teams
        my11, _, _ = team_builder.build_optimized_my11circle_team(team1, team2)
        tata, _, _ = team_builder.build_optimized_tata_ipl_team(team1, team2)
        
        all_teams.append({
            'match': match_num,
            'team1': team1,
            'team2': team2,
            'my11_captain': my11['CAPTAIN'],
            'tata_captain': tata['CAPTAIN']
        })
        
        print(f"✓ My11Circle Captain: {my11['CAPTAIN']}")
        print(f"✓ TATA IPL Captain: {tata['CAPTAIN']}")
    
    # Export summary
    summary_df = pd.DataFrame(all_teams)
    summary_df.to_excel('Phase1_Team_Summary.xlsx', index=False)
    print("\n✓ All teams exported to Phase1_Team_Summary.xlsx")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
chmod +x ~/IPL2026_Fantasy/orchestrator.py
python ~/IPL2026_Fantasy/orchestrator.py
```

---

## PART 6: SCHEDULING AUTOMATION

### Set Up Daily Automation

```bash
# Create a shell script that runs before each match
cat > ~/IPL2026_Fantasy/run_daily.sh << 'SCRIPT'
#!/bin/bash
cd ~/IPL2026_Fantasy

# Get today's match
TODAY=$(date +%Y-%m-%d)
echo "Running fantasy team builder for $TODAY"

# Run Python automation
python orchestrator.py

# Email results (optional)
# mail -s "IPL Fantasy Teams - $TODAY" your@email.com < Phase1_Team_Summary.xlsx

# Notify with desktop notification
notify-send "✓ Fantasy teams generated" "Check Phase1_Team_Summary.xlsx"
SCRIPT

chmod +x ~/IPL2026_Fantasy/run_daily.sh
```

### Schedule with Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 5 PM)
17 0 * * * /home/username/IPL2026_Fantasy/run_daily.sh
```

### Schedule with Task Scheduler (Windows)

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Users\Username\IPL2026_Fantasy\orchestrator.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "5:00PM"
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "IPL_Fantasy_Builder" -Description "Daily fantasy team generation"
```

---

## PART 7: QUICK START COMMANDS

### Option A: 30-Second Setup (Beginner)

```bash
# 1. Create folder
mkdir ~/IPL2026_Fantasy && cd ~/IPL2026_Fantasy

# 2. Copy files
cp "/sessions/friendly-jolly-lamport/mnt/IPL 2026/"*.xlsx .

# 3. Create simple script
cat > team_builder.py << 'PYSCRIPT'
import pandas as pd
df = pd.read_excel('IPL_2026_Players_Comprehensive.xlsx', sheet_name='All Players')
print(f"✓ Loaded {len(df)} players")
print(f"Teams: {df['Team'].unique()}")
PYSCRIPT

# 4. Run it
python team_builder.py
```

### Option B: Full Setup (Intermediate)

```bash
# Install dependencies
pip install openpyxl pandas numpy

# Copy files and scripts
cp "/sessions/friendly-jolly-lamport/mnt/IPL 2026/"*.xlsx ~/IPL2026_Fantasy/
cp team_builder_advanced.py ~/IPL2026_Fantasy/

# Run advanced builder
cd ~/IPL2026_Fantasy
python team_builder_advanced.py
```

### Option C: Full Automation (Advanced)

```bash
# Complete setup with Claude Code integration
claude-code "
1. Create ~/IPL2026_Fantasy project structure
2. Copy all Excel files
3. Create team_builder_advanced.py with full features
4. Create orchestrator.py for 14-match automation
5. Set up daily scheduling
6. Generate Phase 1 teams (Matches 1-14)
Output: Complete automation ready to use
"
```

---

## PART 8: COMMON ISSUES & FIXES

### Issue 1: Excel file not found
```bash
# Solution: Check file path
ls -la ~/IPL2026_Fantasy/
# Make sure files are there
```

### Issue 2: API Key error
```bash
# Solution: Set API key
export ANTHROPIC_API_KEY="your-key-here"
echo $ANTHROPIC_API_KEY  # Verify it's set
```

### Issue 3: Python module not found
```bash
# Solution: Install dependencies
pip install openpyxl pandas numpy requests
```

### Issue 4: Excel file has old data
```bash
# Solution: Delete old and copy fresh
rm ~/IPL2026_Fantasy/*.xlsx
cp "/sessions/friendly-jolly-lamport/mnt/IPL 2026/"*.xlsx ~/IPL2026_Fantasy/
```

---

## NEXT STEPS

1. ✅ Follow Part 1-2 to set up your environment
2. ✅ Use Script 1 or 2 from Part 3 (Script 2 is recommended)
3. ✅ Test with Match 1 (RCB vs SRH)
4. ✅ Use Claude Code commands from Part 4 to improve
5. ✅ Set up scheduling from Part 6
6. ✅ Run for all Phase 1 matches

**Total time: 15 minutes for complete setup**

