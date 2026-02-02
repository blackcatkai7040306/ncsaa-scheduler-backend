"""
Comprehensive test to verify ALL systemic fixes apply to ALL schools.

This test ensures we're not just fixing specific examples (Meadows, Faith, etc.)
but that the fixes work for EVERY school in the system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict
from datetime import date

def test_all_systemic_fixes():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SYSTEMIC FIX VERIFICATION")
    print("Testing that ALL fixes apply to ALL schools, not just specific examples")
    print("=" * 80)
    
    # Load data
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams from {len(set(t.school.name for t in teams))} schools")
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    all_passed = True
    
    # ========================================================================
    # TEST 1: NO SAME-SCHOOL MATCHUPS (for ANY school)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: NO SAME-SCHOOL MATCHUPS")
    print("=" * 80)
    
    same_school_violations = []
    for game in schedule.games:
        if game.home_team.school.name == game.away_team.school.name:
            same_school_violations.append({
                'school': game.home_team.school.name,
                'home': game.home_team.id,
                'away': game.away_team.id,
                'date': game.time_slot.date,
                'facility': game.time_slot.facility.name
            })
    
    if same_school_violations:
        print(f"\n[FAIL] Found {len(same_school_violations)} same-school matchups:")
        schools_affected = set(v['school'] for v in same_school_violations)
        for school in schools_affected:
            school_violations = [v for v in same_school_violations if v['school'] == school]
            print(f"\n  {school}: {len(school_violations)} violations")
            for v in school_violations[:3]:  # Show first 3
                print(f"    - {v['home']} vs {v['away']} on {v['date']}")
        all_passed = False
    else:
        print("\n[PASS] No same-school matchups found across ALL schools")
    
    # ========================================================================
    # TEST 2: HOME FACILITY = HOME TEAM (for ALL schools with facilities)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: HOME FACILITY = HOME TEAM")
    print("=" * 80)
    
    # Find all schools with facilities
    schools_with_facilities = {}
    for facility in facilities:
        for team in teams:
            # Check if facility name contains school name
            if team.school.name.lower() in facility.name.lower():
                if team.school.name not in schools_with_facilities:
                    schools_with_facilities[team.school.name] = []
                if facility not in schools_with_facilities[team.school.name]:
                    schools_with_facilities[team.school.name].append(facility)
    
    print(f"\n[INFO] Found {len(schools_with_facilities)} schools with home facilities")
    
    home_facility_violations = []
    for game in schedule.games:
        facility_name = game.time_slot.facility.name.lower()
        
        # Check if this facility belongs to any school
        for school_name, school_facilities in schools_with_facilities.items():
            for facility in school_facilities:
                if facility.name == game.time_slot.facility.name:
                    # This facility belongs to school_name
                    # Check if school_name is the home team
                    if game.home_team.school.name != school_name:
                        home_facility_violations.append({
                            'facility_school': school_name,
                            'home_team_school': game.home_team.school.name,
                            'away_team_school': game.away_team.school.name,
                            'facility': facility.name,
                            'date': game.time_slot.date
                        })
    
    if home_facility_violations:
        print(f"\n[FAIL] Found {len(home_facility_violations)} home facility violations:")
        schools_affected = set(v['facility_school'] for v in home_facility_violations)
        for school in schools_affected:
            school_violations = [v for v in home_facility_violations if v['facility_school'] == school]
            print(f"\n  {school}: {len(school_violations)} violations")
            print(f"    Their facility used by other schools:")
            for v in school_violations[:3]:
                print(f"      - {v['home_team_school']} (home) vs {v['away_team_school']} at {v['facility']}")
        all_passed = False
    else:
        print("\n[PASS] All home facilities correctly assigned to home teams")
    
    # ========================================================================
    # TEST 3: NO SCHOOL PLAYS ON MULTIPLE COURTS SIMULTANEOUSLY
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: NO SIMULTANEOUS GAMES ON DIFFERENT COURTS")
    print("=" * 80)
    
    # Group games by date and time
    games_by_datetime = defaultdict(list)
    for game in schedule.games:
        key = (game.time_slot.date, game.time_slot.start_time)
        games_by_datetime[key].append(game)
    
    simultaneous_violations = []
    for (game_date, start_time), games in games_by_datetime.items():
        # Group by school
        schools_playing = defaultdict(list)
        for game in games:
            schools_playing[game.home_team.school.name].append(game)
            schools_playing[game.away_team.school.name].append(game)
        
        # Check if any school has multiple games at same time
        for school_name, school_games in schools_playing.items():
            if len(school_games) > 1:
                # Check if on different courts
                courts = set((g.time_slot.facility.name, g.time_slot.court_number) for g in school_games)
                if len(courts) > 1:
                    simultaneous_violations.append({
                        'school': school_name,
                        'date': game_date,
                        'time': start_time,
                        'num_games': len(school_games),
                        'courts': courts
                    })
    
    if simultaneous_violations:
        print(f"\n[FAIL] Found {len(simultaneous_violations)} simultaneous court violations:")
        schools_affected = set(v['school'] for v in simultaneous_violations)
        for school in schools_affected:
            school_violations = [v for v in simultaneous_violations if v['school'] == school]
            print(f"\n  {school}: {len(school_violations)} violations")
            for v in school_violations[:2]:
                print(f"    - {v['date']} at {v['time']}: {v['num_games']} games on {len(v['courts'])} courts")
        all_passed = False
    else:
        print("\n[PASS] No school plays on multiple courts simultaneously")
    
    # ========================================================================
    # TEST 4: NO WEEKNIGHT DOUBLEHEADERS (for ANY team)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 4: NO WEEKNIGHT DOUBLEHEADERS")
    print("=" * 80)
    
    # Group games by team and date
    team_games_by_date = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        team_games_by_date[game.home_team.id][game.time_slot.date].append(game)
        team_games_by_date[game.away_team.id][game.time_slot.date].append(game)
    
    weeknight_doubleheader_violations = []
    for team_id, dates in team_games_by_date.items():
        for game_date, games in dates.items():
            # Check if weeknight (Monday-Friday = 0-4)
            if game_date.weekday() < 5 and len(games) > 1:
                team = next(t for t in teams if t.id == team_id)
                weeknight_doubleheader_violations.append({
                    'team': team_id,
                    'school': team.school.name,
                    'date': game_date,
                    'num_games': len(games)
                })
    
    if weeknight_doubleheader_violations:
        print(f"\n[FAIL] Found {len(weeknight_doubleheader_violations)} weeknight doubleheaders:")
        schools_affected = set(v['school'] for v in weeknight_doubleheader_violations)
        for school in schools_affected:
            school_violations = [v for v in weeknight_doubleheader_violations if v['school'] == school]
            print(f"\n  {school}: {len(school_violations)} violations")
            for v in school_violations[:2]:
                print(f"    - {v['team']}: {v['num_games']} games on {v['date']} (weeknight)")
        all_passed = False
    else:
        print("\n[PASS] No weeknight doubleheaders found")
    
    # ========================================================================
    # TEST 5: NO FRIDAY + SATURDAY BACK-TO-BACK (for ANY school)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 5: NO FRIDAY + SATURDAY BACK-TO-BACK")
    print("=" * 80)
    
    # Group games by school and date
    school_games_by_date = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        school_games_by_date[game.home_team.school.name][game.time_slot.date].append(game)
        school_games_by_date[game.away_team.school.name][game.time_slot.date].append(game)
    
    friday_saturday_violations = []
    for school_name, dates in school_games_by_date.items():
        date_list = sorted(dates.keys())
        for i in range(len(date_list) - 1):
            date1 = date_list[i]
            date2 = date_list[i + 1]
            
            # Check if Friday (4) followed by Saturday (5)
            if date1.weekday() == 4 and date2.weekday() == 5:
                if (date2 - date1).days == 1:
                    friday_saturday_violations.append({
                        'school': school_name,
                        'friday': date1,
                        'saturday': date2
                    })
    
    if friday_saturday_violations:
        print(f"\n[FAIL] Found {len(friday_saturday_violations)} Friday+Saturday violations:")
        for v in friday_saturday_violations[:10]:
            print(f"  - {v['school']}: plays {v['friday']} (Fri) and {v['saturday']} (Sat)")
        all_passed = False
    else:
        print("\n[PASS] No Friday+Saturday back-to-back violations")
    
    # ========================================================================
    # TEST 6: NO COACH CONFLICTS (for ANY coach)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 6: NO COACH CONFLICTS")
    print("=" * 80)
    
    # Find coaches with multiple teams
    coaches_teams = defaultdict(list)
    for team in teams:
        if team.coach_name:
            coaches_teams[team.coach_name].append(team)
    
    multi_team_coaches = {coach: teams_list for coach, teams_list in coaches_teams.items() if len(teams_list) > 1}
    print(f"\n[INFO] Found {len(multi_team_coaches)} coaches with multiple teams")
    
    # Track coach schedules
    coach_schedules = defaultdict(list)
    for game in schedule.games:
        if game.home_team.coach_name:
            coach_schedules[game.home_team.coach_name].append({
                'game': game,
                'team': game.home_team.id,
                'datetime': (game.time_slot.date, game.time_slot.start_time),
                'court': (game.time_slot.facility.name, game.time_slot.court_number)
            })
        if game.away_team.coach_name:
            coach_schedules[game.away_team.coach_name].append({
                'game': game,
                'team': game.away_team.id,
                'datetime': (game.time_slot.date, game.time_slot.start_time),
                'court': (game.time_slot.facility.name, game.time_slot.court_number)
            })
    
    coach_conflicts = []
    for coach_name, schedule_items in coach_schedules.items():
        # Group by datetime
        by_datetime = defaultdict(list)
        for item in schedule_items:
            by_datetime[item['datetime']].append(item)
        
        # Check for conflicts
        for datetime, items in by_datetime.items():
            if len(items) > 1:
                # Check if on different courts
                courts = set(item['court'] for item in items)
                if len(courts) > 1:
                    coach_conflicts.append({
                        'coach': coach_name,
                        'datetime': datetime,
                        'num_games': len(items),
                        'courts': courts
                    })
    
    if coach_conflicts:
        print(f"\n[FAIL] Found {len(coach_conflicts)} coach conflicts:")
        coaches_affected = set(c['coach'] for c in coach_conflicts)
        for coach in coaches_affected:
            coach_violations = [c for c in coach_conflicts if c['coach'] == coach]
            print(f"\n  {coach}: {len(coach_violations)} conflicts")
            for v in coach_violations[:2]:
                print(f"    - {v['datetime'][0]} at {v['datetime'][1]}: {v['num_games']} games on {len(v['courts'])} courts")
        all_passed = False
    else:
        print("\n[PASS] No coach conflicts found")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    tests = [
        ("Same-school matchups", len(same_school_violations) == 0),
        ("Home facility assignment", len(home_facility_violations) == 0),
        ("Simultaneous courts", len(simultaneous_violations) == 0),
        ("Weeknight doubleheaders", len(weeknight_doubleheader_violations) == 0),
        ("Friday+Saturday back-to-back", len(friday_saturday_violations) == 0),
        ("Coach conflicts", len(coach_conflicts) == 0)
    ]
    
    for test_name, passed in tests:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
    
    if all_passed:
        print("\n" + "=" * 80)
        print("ALL SYSTEMIC FIXES VERIFIED ACROSS ALL SCHOOLS!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("SOME ISSUES FOUND - SEE DETAILS ABOVE")
        print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_all_systemic_fixes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
