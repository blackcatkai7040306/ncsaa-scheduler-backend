"""
Diagnose why Faith only has 1 game on Monday, January 5.
Check what matchups are available for Faith and their game counts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler

def diagnose_faith():
    print("="*80)
    print("DIAGNOSING FAITH MATCHUPS")
    print("="*80)
    
    # Load data
    print("\n[1/3] Loading data...")
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find Faith teams
    faith_teams = [t for t in teams if 'faith' in t.school.name.lower()]
    print(f"\n[2/3] Faith has {len(faith_teams)} teams:")
    for team in faith_teams:
        print(f"  - {team.id} ({team.division.value}) - Coach: {team.coach_name}")
    
    # Initialize scheduler to generate matchups
    print("\n[3/3] Generating matchups...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    
    # Find all matchups involving Faith
    faith_matchups = []
    for matchup in scheduler.matchups:
        if 'faith' in matchup.school_a.name.lower() or 'faith' in matchup.school_b.name.lower():
            faith_matchups.append(matchup)
    
    print(f"\nFound {len(faith_matchups)} matchups involving Faith:")
    print("\n" + "="*80)
    
    # Sort by number of games (descending)
    faith_matchups.sort(key=lambda m: len(m.games), reverse=True)
    
    for i, matchup in enumerate(faith_matchups[:20], 1):  # Show top 20
        school_a = matchup.school_a.name
        school_b = matchup.school_b.name
        num_games = len(matchup.games)
        priority = matchup.priority_score
        
        print(f"\n{i}. {school_a} vs {school_b}")
        print(f"   Games: {num_games}")
        print(f"   Priority Score: {priority:.1f}")
        
        # Show divisions
        divisions = {}
        for team_a, team_b, div in matchup.games:
            if div.value not in divisions:
                divisions[div.value] = 0
            divisions[div.value] += 1
        
        print(f"   Divisions: {', '.join([f'{div} ({count})' for div, count in divisions.items()])}")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Check Faith's home facility
    faith_facilities = [f for f in facilities if 'faith' in f.name.lower()]
    print(f"\nFaith's facilities: {len(faith_facilities)}")
    for fac in faith_facilities:
        print(f"  - {fac.name} ({fac.max_courts} courts)")
    
    # Check weight calculation
    print("\n" + "="*80)
    print("WEIGHT CALCULATION TEST")
    print("="*80)
    
    num_faith_teams = len(faith_teams)
    print(f"\nFaith has {num_faith_teams} teams")
    print("\nWeight calculation for different matchup sizes:")
    
    for num_games in [1, 2, 3, 4, 5, 6, 7, 8]:
        if num_games >= num_faith_teams:
            weight = 1000 + (num_games * 10)
            priority = "HIGHEST"
        elif num_games >= 3:
            weight = 500 + (num_games * 10)
            priority = "HIGH"
        else:
            weight = 10 + (num_games * 5)
            priority = "LOW"
        
        print(f"  {num_games} games: weight = {weight} ({priority})")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    # Find best matchups for Faith
    best_matchups = [m for m in faith_matchups if len(m.games) >= 3]
    print(f"\nMatchups with 3+ games: {len(best_matchups)}")
    
    if best_matchups:
        print("\nTop 5 matchups Faith should host:")
        for i, matchup in enumerate(best_matchups[:5], 1):
            school_a = matchup.school_a.name
            school_b = matchup.school_b.name
            num_games = len(matchup.games)
            print(f"  {i}. {school_a} vs {school_b} ({num_games} games)")
    else:
        print("\n[WARNING] No matchups with 3+ games found!")
        print("Faith might not have enough teams in common divisions with other schools.")

if __name__ == "__main__":
    try:
        diagnose_faith()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
