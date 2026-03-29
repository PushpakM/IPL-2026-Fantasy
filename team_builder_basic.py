import openpyxl
import pandas as pd
from datetime import datetime

class FantasyTeamBuilder:
    def __init__(self, players_file, strategy_file):
        """Initialize team builder with player and strategy data"""
        self.players_df = pd.read_excel(players_file, sheet_name='All Players')
        self.wb = openpyxl.load_workbook(strategy_file)
        print("✓ Team Builder initialized")
        print(f"✓ Loaded {len(self.players_df)} players")
    
    def build_my11circle_team(self, team1, team2, match_num=1):
        """Build My11Circle team following rules: WK 1-4, BAT 1-6, AR 1-6, BOW 1-6"""
        print(f"\n📋 Building My11Circle Team for Match {match_num}")
        print(f"Teams: {team1} vs {team2}")
        
        team1_players = self.players_df[self.players_df['Team'] == team1]
        team2_players = self.players_df[self.players_df['Team'] == team2]
        
        team = {
            'CAPTAIN': None,
            'VICE_CAPTAIN': None,
            'WK': [],
            'BAT': [],
            'AR': [],
            'BOW': []
        }
        
        all_available = pd.concat([team1_players, team2_players])
        all_available = all_available[all_available['Availability'] == 'Available']
        
        if len(all_available) > 0:
            team['CAPTAIN'] = all_available.iloc[0]['Player Name']
            print(f"⭐ Captain: {team['CAPTAIN']} ({all_available.iloc[0]['Team']})")
        
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
        
        team1_players = self.players_df[self.players_df['Team'] == team1]
        team2_players = self.players_df[self.players_df['Team'] == team2]
        all_available = pd.concat([team1_players, team2_players])
        all_available = all_available[all_available['Availability'] == 'Available']
        
        if len(all_available) > 1:
            team['CAPTAIN'] = all_available.iloc[0]['Player Name']
            team['VICE_CAPTAIN'] = all_available.iloc[1]['Player Name']
            print(f"⭐ Captain: {team['CAPTAIN']}")
            print(f"✪ Vice-Captain: {team['VICE_CAPTAIN']}")
        
        return team
    
    def display_team(self, team, league_name="My11Circle"):
        """Display the built team"""
        print(f"\n🏏 {league_name} TEAM")
        print(f"  Captain: {team.get('CAPTAIN', 'Not set')} (2x points)")
        print(f"  Vice-Captain: {team.get('VICE_CAPTAIN', 'Not set')} (1.5x points)")

if __name__ == "__main__":
    builder = FantasyTeamBuilder(
        'IPL_2026_Players_Comprehensive.xlsx',
        'IPL_2026_Fantasy_Team_Builder.xlsx'
    )
    
    my11_team = builder.build_my11circle_team('RCB', 'SRH', match_num=1)
    tata_team = builder.build_tata_ipl_team('RCB', 'SRH', match_num=1)
    
    builder.display_team(my11_team, "My11Circle")
    builder.display_team(tata_team, "TATA IPL Fantasy")
    
    print("\n✓ Teams built successfully!")
