"""Check Faith school matchup on Monday, January 5, 2026"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from datetime import date

def check_faith_matchup():
    print("\nChecking Faith school matchup...")
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find Faith teams
    print("\n" + "=" * 70)
    print("FAITH SCHOOL TEAMS")
    print("=" * 70)
    faith_teams = [t for t in teams if 'faith' in t.school.name.lower()]
    for team in faith_teams:
        print(f"  - {team.id}")
        print(f"    School: '{team.school.name}'")
        print(f"    Division: {team.division.value}")
        print(f"    Coach: {team.coach_name}")
        print()
    
    # Find Amplus teams
    print("\n" + "=" * 70)
    print("AMPLUS SCHOOL TEAMS")
    print("=" * 70)
    amplus_teams = [t for t in teams if 'amplus' in t.school.name.lower()]
    for team in amplus_teams:
        print(f"  - {team.id} (Division: {team.division.value}, Coach: {team.coach_name})")
    
    print(f"\n[INFO] Faith has {len(faith_teams)} teams")
    print(f"[INFO] Amplus has {len(amplus_teams)} teams")
    
    # Check if Faith has 3+ divisions
    faith_divisions = set(t.division for t in faith_teams)
    print(f"\n[INFO] Faith plays in {len(faith_divisions)} divisions:")
    for div in faith_divisions:
        print(f"  - {div.value}")
    
    # Check Faith's facility
    print("\n" + "=" * 70)
    print("FAITH FACILITIES")
    print("=" * 70)
    faith_facilities = [f for f in facilities if 'faith' in f.name.lower()]
    for facility in faith_facilities:
        print(f"  - {facility.name} (Courts: {facility.max_courts})")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    if len(faith_teams) < 3:
        print(f"[ISSUE] Faith only has {len(faith_teams)} teams, but client expects 3 divisions")
        print("[NOTE] This might be a data issue in Google Sheets")
    else:
        print(f"[OK] Faith has {len(faith_teams)} teams across {len(faith_divisions)} divisions")
    
    # Check if Faith vs Amplus is a valid matchup
    if len(faith_teams) == 2 and len(amplus_teams) == 2:
        print("[OK] Faith (2 teams) vs Amplus (2 teams) = 2 games scheduled")
        print("[NOTE] This matches the screenshot (2 games on Monday)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        check_faith_matchup()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
