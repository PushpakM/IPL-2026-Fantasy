import openpyxl
import pandas as pd
from typing import Dict, List, Tuple

class AdvancedFantasyTeamBuilder:
    def __init__(self, players_file: str, strategy_file: str):
        self.players_df = pd.read_excel(players_file, sheet_name='All Players')
        self.strategy_df = pd.read_excel(strategy_file, sheet_name='Strategy Dashboard')
        self.my11_rules = {'WK': (1, 4), 'BAT': (1, 6), 'AR': (1, 6), 'BOW': (1, 6)}
        self.tata_rules = {'WK': (1, 2), 'BAT': (3, 5), 'AR': (1, 3), 'BOW': (3, 5)}
        print("✓ Advanced Team Builder initialized")
    
    def get_available_players(self, team1: str, team2: str) -> pd.DataFrame:
        teams = [team1, team2]
        available = self.players_df[
            (self.players_df['Team'].isin(teams)) & 
            (self.players_df['Availability'] == 'Available')
        ]
        return available
    
    def validate_team_composition(self, team: Dict, rules: Dict) -> Tuple[bool, List[str]]:
        errors = []
        
        for role, (min_count, max_count) in rules.items():
            actual_count = len(team.get(role, []))
            if actual_count < min_count:
                errors.append(f"❌ {role}: Need {min_count}, got {actual_count}")
            if actual_count > max_count:
                errors.append(f"❌ {role}: Max {max_count}, got {actual_count}")
        
        total = sum(len(v) for k, v in team.items() if isinstance(v, list))
        if total != 11:
            errors.append(f"❌ Total: Need 11, got {total}")
        
        return len(errors) == 0, errors
    
    def build_optimized_my11circle_team(self, team1: str, team2: str, captain_pref: str = None):
        available = self.get_available_players(team1, team2)
        
        team = {
            'CAPTAIN': captain_pref or (available.iloc[0]['Player Name'] if len(available) > 0 else None),
            'VICE_CAPTAIN': available.iloc[1]['Player Name'] if len(available) > 1 else None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        is_valid, errors = self.validate_team_composition(team, self.my11_rules)
        return team, is_valid, errors
    
    def build_optimized_tata_ipl_team(self, team1: str, team2: str, captain_pref: str = None):
        available = self.get_available_players(team1, team2)
        
        team = {
            'CAPTAIN': captain_pref or (available.iloc[0]['Player Name'] if len(available) > 0 else None),
            'VICE_CAPTAIN': available.iloc[1]['Player Name'] if len(available) > 1 else None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        is_valid, errors = self.validate_team_composition(team, self.tata_rules)
        return team, is_valid, errors
    
    def export_teams_to_excel(self, my11_team: Dict, tata_team: Dict, match_num: int, output_file='Generated_Teams.xlsx'):
        wb = openpyxl.Workbook()
        
        ws1 = wb.active
        ws1.title = f"Match {match_num} - My11Circle"
        ws1['A1'] = f"Match {match_num} - My11Circle Team"
        
        row = 3
        ws1[f'A{row}'] = "Captain"
        ws1[f'B{row}'] = my11_team['CAPTAIN']
        row += 1
        ws1[f'A{row}'] = "Vice-Captain"
        ws1[f'B{row}'] = my11_team['VICE_CAPTAIN']
        
        ws2 = wb.create_sheet(f"Match {match_num} - TATA IPL")
        ws2['A1'] = f"Match {match_num} - TATA IPL Fantasy Team"
        
        row = 3
        ws2[f'A{row}'] = "Captain"
        ws2[f'B{row}'] = tata_team['CAPTAIN']
        row += 1
        ws2[f'A{row}'] = "Vice-Captain"
        ws2[f'B{row}'] = tata_team['VICE_CAPTAIN']
        
        wb.save(output_file)
        print(f"✓ Teams exported to {output_file}")

if __name__ == "__main__":
    builder = AdvancedFantasyTeamBuilder(
        'IPL_2026_Players_Comprehensive.xlsx',
        'IPL_2026_Fantasy_Team_Builder.xlsx'
    )
    
    my11_team, is_valid, errors = builder.build_optimized_my11circle_team(
        'RCB', 'SRH', captain_pref='Virat Kohli'
    )
    
    tata_team, is_valid_tata, errors_tata = builder.build_optimized_tata_ipl_team(
        'RCB', 'SRH', captain_pref='Travis Head'
    )
    
    print("\n🏏 MY11CIRCLE TEAM")
    print(f"  Captain: {my11_team['CAPTAIN']}")
    print(f"  Valid: {is_valid}")
    
    print("\n🏏 TATA IPL FANTASY TEAM")
    print(f"  Captain: {tata_team['CAPTAIN']}")
    print(f"  Valid: {is_valid_tata}")
    
    builder.export_teams_to_excel(my11_team, tata_team, match_num=1)
