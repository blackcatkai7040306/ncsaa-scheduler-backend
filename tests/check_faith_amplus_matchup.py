"""Check Faith vs Amplus school matchup generation"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models import Division

def check_matchup():
    print("\nChecking Faith vs Amplus matchup...")
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Create scheduler
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    
    # Generate school matchups
    matchups = scheduler._generate_school_matchups()
    
    # Find Faith vs Amplus matchup
    print("\n" + "=" * 70)
    print("SEARCHING FOR FAITH VS AMPLUS MATCHUP")
    print("=" * 70)
    
    faith_amplus_matchup = None
    for matchup in matchups:
        school_a_name = matchup.school_a.name.lower()
        school_b_name = matchup.school_b.name.lower()
        
        if ('faith' in school_a_name and 'amplus' in school_b_name) or \
           ('amplus' in school_a_name and 'faith' in school_b_name):
            faith_amplus_matchup = matchup
            break
    
    if not faith_amplus_matchup:
        print("[ERROR] No Faith vs Amplus matchup found!")
        print("\n[DEBUG] Checking all matchups involving Faith:")
        for matchup in matchups:
            if 'faith' in matchup.school_a.name.lower() or 'faith' in matchup.school_b.name.lower():
                print(f"  - {matchup.school_a.name} vs {matchup.school_b.name} ({len(matchup.games)} games)")
        
        print("\n[DEBUG] Checking all matchups involving Amplus:")
        for matchup in matchups:
            if 'amplus' in matchup.school_a.name.lower() or 'amplus' in matchup.school_b.name.lower():
                print(f"  - {matchup.school_a.name} vs {matchup.school_b.name} ({len(matchup.games)} games)")
        return
    
    print(f"[FOUND] {faith_amplus_matchup.school_a.name} vs {faith_amplus_matchup.school_b.name}")
    print(f"[SCORE] Priority score: {faith_amplus_matchup.priority_score}")
    print(f"[GAMES] Total games in matchup: {len(faith_amplus_matchup.games)}")
    
    # Show all games
    print("\n" + "=" * 70)
    print("ALL GAMES IN MATCHUP")
    print("=" * 70)
    
    for i, (team_a, team_b, division) in enumerate(faith_amplus_matchup.games, 1):
        print(f"{i}. {team_a.id} vs {team_b.id}")
        print(f"   Division: {division.value}")
        print(f"   Coaches: {team_a.coach_name} vs {team_b.coach_name}")
        print()
    
    # Check BOY'S JV specifically
    print("=" * 70)
    print("BOY'S JV GAMES")
    print("=" * 70)
    
    boys_jv_games = [g for g in faith_amplus_matchup.games if g[2] == Division.BOYS_JV]
    print(f"Found {len(boys_jv_games)} BOY'S JV games:")
    for team_a, team_b, division in boys_jv_games:
        print(f"  - {team_a.id} vs {team_b.id}")
    
    if len(boys_jv_games) < 2:
        print("\n[ISSUE] Expected 2 BOY'S JV games (Faith has 2 teams)")
        print("[ISSUE] But only found", len(boys_jv_games))
    else:
        print("\n[OK] Found all expected BOY'S JV games")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        check_matchup()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
