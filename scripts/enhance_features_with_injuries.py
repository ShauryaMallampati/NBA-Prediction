"""
Enhanced Feature Engineering with Injury Impact
Incorporates ESPN injury data into prediction features
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class InjuryFeatureEngineer:
    """Add injury impact features to game predictions"""
    
    def __init__(self):
        self.star_players = self._define_star_players()
        
    def _define_star_players(self) -> dict:
        """Define star players by team (top 3 players per team)"""
        # This would ideally come from player stats/PER/usage rate
        # For now, defining key players per team
        return {
            'ATL': ['Trae Young', 'Dejounte Murray', 'Clint Capela'],
            'BOS': ['Jayson Tatum', 'Jaylen Brown', 'Kristaps Porzingis'],
            'BKN': ['Mikal Bridges', 'Cam Thomas', 'Spencer Dinwiddie'],
            'CHA': ['LaMelo Ball', 'Terry Rozier', 'Gordon Hayward'],
            'CHI': ['DeMar DeRozan', 'Zach LaVine', 'Nikola Vucevic'],
            'CLE': ['Donovan Mitchell', 'Darius Garland', 'Evan Mobley'],
            'DAL': ['Luka Doncic', 'Kyrie Irving', 'Christian Wood'],
            'DEN': ['Nikola Jokic', 'Jamal Murray', 'Michael Porter Jr.'],
            'DET': ['Cade Cunningham', 'Jaden Ivey', 'Bojan Bogdanovic'],
            'GSW': ['Stephen Curry', 'Klay Thompson', 'Draymond Green'],
            'HOU': ['Alperen Sengun', 'Jalen Green', 'Fred VanVleet'],
            'IND': ['Tyrese Haliburton', 'Pascal Siakam', 'Myles Turner'],
            'LAC': ['Kawhi Leonard', 'Paul George', 'Russell Westbrook'],
            'LAL': ['LeBron James', 'Anthony Davis', "D'Angelo Russell"],
            'MEM': ['Ja Morant', 'Jaren Jackson Jr.', 'Desmond Bane'],
            'MIA': ['Jimmy Butler', 'Bam Adebayo', 'Tyler Herro'],
            'MIL': ['Giannis Antetokounmpo', 'Damian Lillard', 'Khris Middleton'],
            'MIN': ['Anthony Edwards', 'Karl-Anthony Towns', 'Rudy Gobert'],
            'NOP': ['Zion Williamson', 'Brandon Ingram', 'CJ McCollum'],
            'NYK': ['Jalen Brunson', 'Julius Randle', 'RJ Barrett'],
            'OKC': ['Shai Gilgeous-Alexander', 'Chet Holmgren', 'Jalen Williams'],
            'ORL': ['Paolo Banchero', 'Franz Wagner', 'Wendell Carter Jr.'],
            'PHI': ['Joel Embiid', 'Tyrese Maxey', 'Tobias Harris'],
            'PHX': ['Kevin Durant', 'Devin Booker', 'Bradley Beal'],
            'POR': ['Damian Lillard', 'Anfernee Simons', 'Jerami Grant'],
            'SAC': ["De'Aaron Fox", 'Domantas Sabonis', 'Keegan Murray'],
            'SAS': ['Victor Wembanyama', 'Keldon Johnson', 'Devin Vassell'],
            'TOR': ['Pascal Siakam', 'Scottie Barnes', 'OG Anunoby'],
            'UTA': ['Lauri Markkanen', 'Jordan Clarkson', 'Walker Kessler'],
            'WAS': ['Kyle Kuzma', 'Jordan Poole', 'Tyus Jones'],
        }
    
    def load_injury_data(self, date: str) -> pd.DataFrame:
        """Load injury data for given date"""
        injury_path = Path(f"data/espn/injuries_{date}.csv")
        
        if not injury_path.exists():
            print(f"⚠️  No injury data found for {date}")
            return pd.DataFrame()
        
        df = pd.read_csv(injury_path)
        print(f"✅ Loaded {len(df)} injury reports")
        return df
    
    def calculate_injury_impact(self, team: str, injuries_df: pd.DataFrame) -> dict:
        """Calculate injury impact score for a team"""
        
        if injuries_df.empty:
            return {
                'injured_star_count': 0,
                'total_injured': 0,
                'injury_impact_score': 0.0,
                'key_injuries': []
            }
        
        team_injuries = injuries_df[injuries_df['team'] == team]
        
        # Count star players out
        star_players = self.star_players.get(team, [])
        injured_stars = []
        
        for _, injury in team_injuries.iterrows():
            player_name = injury['player_name']
            status = injury['status']
            
            # Check if it's a star player
            is_star = any(star.lower() in player_name.lower() for star in star_players)
            
            # Only count as injured if Out or Day-To-Day
            is_out = 'out' in status.lower() or 'day-to-day' in status.lower()
            
            if is_star and is_out:
                injured_stars.append({
                    'name': player_name,
                    'status': status,
                    'details': injury.get('details', '')
                })
        
        # Calculate impact score
        # Star player out = -0.15 per player (significant impact)
        # Regular player out = -0.03 per player
        injured_star_count = len(injured_stars)
        total_injured = len(team_injuries)
        regular_injured = total_injured - injured_star_count
        
        impact_score = -(injured_star_count * 0.15 + regular_injured * 0.03)
        
        return {
            'injured_star_count': injured_star_count,
            'total_injured': total_injured,
            'injury_impact_score': impact_score,
            'key_injuries': injured_stars
        }
    
    def add_injury_features(self, games_df: pd.DataFrame, date: str) -> pd.DataFrame:
        """Add injury features to games dataframe"""
        
        print(f"\n🏥 Adding injury features for {date}...")
        
        # Load injury data
        injuries_df = self.load_injury_data(date)
        
        # Add injury features for home and away teams
        injury_features = []
        
        for _, game in games_df.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            
            home_impact = self.calculate_injury_impact(home_team, injuries_df)
            away_impact = self.calculate_injury_impact(away_team, injuries_df)
            
            injury_features.append({
                'game_id': game.get('game_id', ''),
                'home_injured_stars': home_impact['injured_star_count'],
                'home_total_injured': home_impact['total_injured'],
                'home_injury_impact': home_impact['injury_impact_score'],
                'away_injured_stars': away_impact['injured_star_count'],
                'away_total_injured': away_impact['total_injured'],
                'away_injury_impact': away_impact['injury_impact_score'],
                'injury_advantage': home_impact['injury_impact_score'] - away_impact['injury_impact_score'],
            })
            
            # Log key injuries
            if home_impact['key_injuries']:
                print(f"  ⚠️  {home_team} missing: {', '.join([inj['name'] for inj in home_impact['key_injuries']])}")
            if away_impact['key_injuries']:
                print(f"  ⚠️  {away_team} missing: {', '.join([inj['name'] for inj in away_impact['key_injuries']])}")
        
        injury_df = pd.DataFrame(injury_features)
        
        # Merge with games
        if 'game_id' in games_df.columns and 'game_id' in injury_df.columns:
            result = games_df.merge(injury_df, on='game_id', how='left')
        else:
            result = pd.concat([games_df.reset_index(drop=True), injury_df], axis=1)
        
        print(f"✅ Added {len(injury_df.columns)} injury features")
        
        return result
    
    def enhance_prediction_features(self, features_df: pd.DataFrame, date: str) -> pd.DataFrame:
        """Enhance existing features with injury data"""
        
        print("\n" + "="*80)
        print("ENHANCING FEATURES WITH INJURY DATA")
        print("="*80)
        
        # Load injury data
        injuries_df = self.load_injury_data(date)
        
        if injuries_df.empty:
            print("⚠️  No injury data available, returning original features")
            return features_df
        
        # Add injury columns if they don't exist
        injury_cols = [
            'home_injured_stars', 'home_total_injured', 'home_injury_impact',
            'away_injured_stars', 'away_total_injured', 'away_injury_impact',
            'injury_advantage'
        ]
        
        for col in injury_cols:
            if col not in features_df.columns:
                features_df[col] = 0.0
        
        # Calculate injury impact for each team
        for idx, row in features_df.iterrows():
            if 'home_team' in row and 'away_team' in row:
                home_impact = self.calculate_injury_impact(row['home_team'], injuries_df)
                away_impact = self.calculate_injury_impact(row['away_team'], injuries_df)
                
                features_df.at[idx, 'home_injured_stars'] = home_impact['injured_star_count']
                features_df.at[idx, 'home_total_injured'] = home_impact['total_injured']
                features_df.at[idx, 'home_injury_impact'] = home_impact['injury_impact_score']
                features_df.at[idx, 'away_injured_stars'] = away_impact['injured_star_count']
                features_df.at[idx, 'away_total_injured'] = away_impact['total_injured']
                features_df.at[idx, 'away_injury_impact'] = away_impact['injury_impact_score']
                features_df.at[idx, 'injury_advantage'] = home_impact['injury_impact_score'] - away_impact['injury_impact_score']
        
        print(f"✅ Enhanced features with injury data")
        print(f"   Teams with injured stars: {(features_df['home_injured_stars'] > 0).sum() + (features_df['away_injured_stars'] > 0).sum()}")
        print(f"   Average injury impact: Home={features_df['home_injury_impact'].mean():.3f}, Away={features_df['away_injury_impact'].mean():.3f}")
        
        return features_df


def main():
    """Test injury feature engineering"""
    
    engineer = InjuryFeatureEngineer()
    
    # Load today's games
    today = datetime.now().strftime("%Y-%m-%d")
    games_path = Path(f"data/schedules/games_{today}.csv")
    
    if not games_path.exists():
        print(f"❌ No games found for {today}")
        return
    
    games_df = pd.read_csv(games_path)
    print(f"\n✅ Loaded {len(games_df)} games for {today}")
    
    # Add injury features
    enhanced_df = engineer.add_injury_features(games_df, today)
    
    # Save enhanced data
    output_path = Path(f"data/schedules/games_with_injuries_{today}.csv")
    enhanced_df.to_csv(output_path, index=False)
    print(f"\n✅ Saved enhanced data to {output_path}")
    
    # Show summary
    print("\n" + "="*80)
    print("INJURY IMPACT SUMMARY")
    print("="*80)
    
    for _, game in enhanced_df.iterrows():
        home = game['home_team']
        away = game['away_team']
        home_stars = game.get('home_injured_stars', 0)
        away_stars = game.get('away_injured_stars', 0)
        advantage = game.get('injury_advantage', 0)
        
        if home_stars > 0 or away_stars > 0:
            print(f"\n{away} @ {home}:")
            if home_stars > 0:
                print(f"  {home}: {home_stars} star(s) injured (impact: {game.get('home_injury_impact', 0):.3f})")
            if away_stars > 0:
                print(f"  {away}: {away_stars} star(s) injured (impact: {game.get('away_injury_impact', 0):.3f})")
            print(f"  Advantage: {'Home' if advantage > 0 else 'Away'} ({abs(advantage):.3f})")


if __name__ == "__main__":
    main()
