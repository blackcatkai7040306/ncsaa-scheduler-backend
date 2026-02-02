"""
Test for client's final feedback issues:
1. Faith playing against itself
2. Sloan Canyon playing at home but being the away team
3. Sloan Canyon team playing at Skye Canyon instead of their own gym
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler


def test_client_final_feedback():
    """
    Test for specific issues reported by client.
    """
    print("\n" + "=" * 70)
    print("TESTING CLIENT FINAL FEEDBACK ISSUES")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    teams = reader.load_teams()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"   Loaded {len(teams)} teams, {len(facilities)} facilities")
    
    # Generate schedule
    print("\n2. Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    print(f"   Generated {len(schedule.games)} games")
    
    # Issue 1: Faith playing against itself
    print("\n3. Checking for same-school matchups (Faith vs Faith)...")
    same_school_games = []
    
    for game in schedule.games:
        home_school = game.home_team.school.name
        away_school = game.away_team.school.name
        
        if home_school == away_school:
            same_school_games.append({
                'home': game.home_team.school.name,
                'home_coach': game.home_team.coach_name,
                'away': game.away_team.school.name,
                'away_coach': game.away_team.coach_name,
                'division': game.division.value,
                'date': game.time_slot.date,
                'time': game.time_slot.start_time,
                'facility': game.time_slot.facility.name
            })
    
    if same_school_games:
        print(f"   [FAIL] Found {len(same_school_games)} same-school matchups!")
        for game in same_school_games[:10]:
            print(f"\n   {game['home']} vs {game['away']} [SAME SCHOOL!]")
            print(f"   Home: {game['home_coach']}, Away: {game['away_coach']}")
            print(f"   Division: {game['division']}")
            print(f"   Date: {game['date']}, Time: {game['time']}")
            print(f"   Facility: {game['facility']}")
    else:
        print(f"   [PASS] No same-school matchups found")
    
    # Issue 2: Sloan Canyon at home but being away team
    print("\n4. Checking home/away team assignments...")
    wrong_home_away = []
    
    for game in schedule.games:
        facility_name = game.time_slot.facility.name.lower()
        home_school = game.home_team.school.name.lower()
        away_school = game.away_team.school.name.lower()
        
        # Check if facility belongs to away team (wrong!)
        if 'sloan canyon' in facility_name and 'sloan canyon' in away_school and 'sloan canyon' not in home_school:
            wrong_home_away.append({
                'facility': game.time_slot.facility.name,
                'home': game.home_team.school.name,
                'away': game.away_team.school.name,
                'division': game.division.value,
                'date': game.time_slot.date,
                'time': game.time_slot.start_time
            })
    
    if wrong_home_away:
        print(f"   [FAIL] Found {len(wrong_home_away)} games with wrong home/away!")
        for game in wrong_home_away[:10]:
            print(f"\n   Facility: {game['facility']}")
            print(f"   Home: {game['home']} (should be Sloan Canyon!)")
            print(f"   Away: {game['away']} (is actually Sloan Canyon!)")
            print(f"   Division: {game['division']}")
            print(f"   Date: {game['date']}, Time: {game['time']}")
    else:
        print(f"   [PASS] All home/away assignments correct")
    
    # Issue 3: Sloan Canyon playing at other gyms
    print("\n5. Checking if Sloan Canyon plays at their own gym...")
    sloan_canyon_games = []
    sloan_canyon_at_home = 0
    sloan_canyon_away = 0
    
    for game in schedule.games:
        home_school = game.home_team.school.name.lower()
        away_school = game.away_team.school.name.lower()
        facility_name = game.time_slot.facility.name.lower()
        
        # Check if Sloan Canyon is playing
        if 'sloan canyon' in home_school or 'sloan canyon' in away_school:
            sloan_canyon_games.append(game)
            
            # Check if at Sloan Canyon facility
            if 'sloan canyon' in facility_name:
                sloan_canyon_at_home += 1
            else:
                sloan_canyon_away += 1
                if sloan_canyon_away <= 10:
                    print(f"\n   Sloan Canyon playing at: {game.time_slot.facility.name}")
                    if 'sloan canyon' in home_school:
                        print(f"     {game.home_team.school.name} (home) vs {game.away_team.school.name}")
                    else:
                        print(f"     {game.home_team.school.name} vs {game.away_team.school.name} (away)")
                    print(f"     Division: {game.division.value}, Date: {game.time_slot.date}")
    
    print(f"\n   Total Sloan Canyon games: {len(sloan_canyon_games)}")
    print(f"   At Sloan Canyon facility: {sloan_canyon_at_home}")
    print(f"   At other facilities: {sloan_canyon_away}")
    
    if sloan_canyon_at_home == 0:
        print(f"   [WARNING] Sloan Canyon NEVER plays at their own gym!")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    issues_found = 0
    
    if same_school_games:
        print(f"[FAIL] Issue 1: {len(same_school_games)} same-school matchups")
        issues_found += 1
    else:
        print(f"[PASS] Issue 1: No same-school matchups")
    
    if wrong_home_away:
        print(f"[FAIL] Issue 2: {len(wrong_home_away)} wrong home/away assignments")
        issues_found += 1
    else:
        print(f"[PASS] Issue 2: All home/away assignments correct")
    
    if sloan_canyon_at_home == 0:
        print(f"[FAIL] Issue 3: Sloan Canyon never plays at home")
        issues_found += 1
    elif sloan_canyon_away > sloan_canyon_at_home * 2:
        print(f"[WARNING] Issue 3: Sloan Canyon plays away too often ({sloan_canyon_away} away vs {sloan_canyon_at_home} home)")
    else:
        print(f"[PASS] Issue 3: Sloan Canyon plays at home {sloan_canyon_at_home} times")
    
    print("=" * 70)
    
    return issues_found == 0


if __name__ == "__main__":
    try:
        success = test_client_final_feedback()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
