"""
Test Meadows school issues: same-school matchups and facility assignment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler

def test_meadows_issues():
    print("\n" + "=" * 70)
    print("TESTING MEADOWS ISSUES")
    print("=" * 70)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find Meadows teams
    print("\n[INFO] Finding Meadows teams...")
    meadows_teams = [t for t in teams if 'meadows' in t.school.name.lower()]
    
    print(f"\n[MEADOWS TEAMS] Found {len(meadows_teams)} teams:")
    for team in meadows_teams:
        print(f"  - {team.id}")
        print(f"    School: '{team.school.name}'")
        print(f"    Division: {team.division.value}")
        print(f"    Coach: {team.coach_name}")
        print()
    
    # Check if there are multiple "Meadows" schools
    meadows_schools = set(t.school.name for t in meadows_teams)
    print(f"[INFO] Unique Meadows school names: {meadows_schools}")
    
    if len(meadows_schools) > 1:
        print(f"\n[ISSUE] Multiple school names for Meadows:")
        for school_name in meadows_schools:
            teams_for_school = [t for t in meadows_teams if t.school.name == school_name]
            print(f"  '{school_name}': {len(teams_for_school)} teams")
    
    # Find Meadows facilities
    print("\n" + "=" * 70)
    print("MEADOWS FACILITIES")
    print("=" * 70)
    meadows_facilities = [f for f in facilities if 'meadows' in f.name.lower()]
    
    if meadows_facilities:
        for facility in meadows_facilities:
            print(f"  - {facility.name}")
            print(f"    Courts: {facility.max_courts}")
    else:
        print("  [WARNING] No Meadows facilities found!")
    
    # Generate schedule
    print("\n" + "=" * 70)
    print("GENERATING SCHEDULE...")
    print("=" * 70)
    
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check for Meadows vs Meadows
    print("\n" + "=" * 70)
    print("CHECKING FOR MEADOWS VS MEADOWS")
    print("=" * 70)
    
    same_school_games = []
    for game in schedule.games:
        home_school = game.home_team.school.name.lower()
        away_school = game.away_team.school.name.lower()
        
        if 'meadows' in home_school and 'meadows' in away_school:
            # Check if it's actually the same school
            if game.home_team.school == game.away_team.school:
                same_school_games.append(game)
                print(f"\n[ISSUE] Meadows vs Meadows found!")
                print(f"  Home: {game.home_team.id} (School: '{game.home_team.school.name}')")
                print(f"  Away: {game.away_team.id} (School: '{game.away_team.school.name}')")
                print(f"  Date: {game.time_slot.date}")
                print(f"  Time: {game.time_slot.start_time}")
                print(f"  Facility: {game.time_slot.facility.name}")
    
    if not same_school_games:
        print("\n[OK] No Meadows vs Meadows games found")
    
    # Check Meadows facility usage
    print("\n" + "=" * 70)
    print("CHECKING MEADOWS FACILITY USAGE")
    print("=" * 70)
    
    meadows_games = []
    for game in schedule.games:
        if 'meadows' in game.home_team.school.name.lower() or 'meadows' in game.away_team.school.name.lower():
            meadows_games.append(game)
    
    print(f"\n[INFO] Found {len(meadows_games)} games involving Meadows")
    
    # Group by facility
    games_by_facility = {}
    for game in meadows_games:
        facility_name = game.time_slot.facility.name
        if facility_name not in games_by_facility:
            games_by_facility[facility_name] = []
        games_by_facility[facility_name].append(game)
    
    print(f"\n[INFO] Meadows plays at {len(games_by_facility)} different facilities:")
    for facility_name, games in games_by_facility.items():
        print(f"\n  {facility_name}: {len(games)} games")
        is_meadows_facility = 'meadows' in facility_name.lower()
        print(f"    Is Meadows facility: {is_meadows_facility}")
        
        if not is_meadows_facility:
            print(f"    [ISSUE] Meadows playing away from their gym:")
            for game in games[:3]:  # Show first 3
                meadows_team = game.home_team if 'meadows' in game.home_team.school.name.lower() else game.away_team
                print(f"      - {meadows_team.id} on {game.time_slot.date}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Meadows teams: {len(meadows_teams)}")
    print(f"Unique school names: {len(meadows_schools)}")
    print(f"Meadows vs Meadows games: {len(same_school_games)}")
    print(f"Facilities used: {len(games_by_facility)}")
    
    issues_found = len(same_school_games) + (1 if len(meadows_schools) > 1 else 0)
    
    if issues_found > 0:
        print(f"\n[FAIL] Found {issues_found} issues!")
        return False
    else:
        print("\n[PASS] No issues found!")
        return True

if __name__ == "__main__":
    try:
        success = test_meadows_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
