"""
Comprehensive test for ALL critical client issues.

This test verifies that EVERY constraint is working for ALL teams/schools/facilities.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models.models import Division
from collections import defaultdict
from datetime import datetime

def test_all_critical_issues():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE CRITICAL ISSUES TEST")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams, {len(facilities)} facilities")
    
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
    # ISSUE 1: Older divisions on K-1 courts
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 1: OLDER DIVISIONS ON K-1 COURTS")
    print("=" * 80)
    
    k1_facilities = [f for f in facilities if f.has_8ft_rims]
    print(f"\n[INFO] K-1 facilities: {len(k1_facilities)}")
    for f in k1_facilities:
        print(f"  - {f.name}")
    
    k1_violations = []
    for game in schedule.games:
        if game.time_slot.facility.has_8ft_rims:
            if game.home_team.division != Division.ES_K1_REC:
                k1_violations.append({
                    'facility': game.time_slot.facility.name,
                    'division': game.home_team.division.value,
                    'home': game.home_team.id,
                    'away': game.away_team.id,
                    'date': game.time_slot.date
                })
    
    if k1_violations:
        print(f"\n[FAIL] {len(k1_violations)} older divisions on K-1 courts:")
        for v in k1_violations[:5]:
            print(f"  - {v['division']} at {v['facility']} on {v['date']}")
        all_passed = False
    else:
        print("\n[PASS] No older divisions on K-1 courts")
    
    # ========================================================================
    # ISSUE 2: Schools spread out over different days
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 2: SCHOOLS SPREAD OUT OVER DIFFERENT DAYS")
    print("=" * 80)
    
    # Group games by school and opponent
    school_matchups = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        home_school = game.home_team.school.name
        away_school = game.away_team.school.name
        matchup_key = tuple(sorted([home_school, away_school]))
        school_matchups[matchup_key]['games'].append(game)
        school_matchups[matchup_key]['dates'] = school_matchups[matchup_key].get('dates', set())
        school_matchups[matchup_key]['dates'].add(game.time_slot.date)
    
    spread_violations = []
    for matchup_key, data in school_matchups.items():
        if len(data['dates']) > 1:
            spread_violations.append({
                'schools': matchup_key,
                'num_dates': len(data['dates']),
                'dates': sorted(data['dates']),
                'num_games': len(data['games'])
            })
    
    if spread_violations:
        print(f"\n[FAIL] {len(spread_violations)} school matchups spread across multiple days:")
        for v in spread_violations[:5]:
            print(f"  - {v['schools'][0]} vs {v['schools'][1]}")
            print(f"    {v['num_games']} games on {v['num_dates']} different days: {v['dates']}")
        all_passed = False
    else:
        print("\n[PASS] All school matchups on single days")
    
    # ========================================================================
    # ISSUE 3: Teams playing across town (cross-cluster)
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 3: TEAMS PLAYING ACROSS TOWN")
    print("=" * 80)
    
    same_cluster = 0
    cross_cluster = 0
    no_cluster_data = 0
    
    for game in schedule.games:
        home_cluster = game.home_team.cluster
        away_cluster = game.away_team.cluster
        
        if not home_cluster or not away_cluster:
            no_cluster_data += 1
        elif home_cluster == away_cluster:
            same_cluster += 1
        else:
            cross_cluster += 1
    
    total_with_data = same_cluster + cross_cluster
    if total_with_data > 0:
        same_cluster_pct = (same_cluster / total_with_data) * 100
        print(f"\n[INFO] Geographic clustering:")
        print(f"  Same cluster: {same_cluster} ({same_cluster_pct:.1f}%)")
        print(f"  Cross cluster: {cross_cluster} ({100-same_cluster_pct:.1f}%)")
        print(f"  No cluster data: {no_cluster_data}")
        
        if same_cluster_pct < 70:
            print(f"\n[FAIL] Only {same_cluster_pct:.1f}% same-cluster matchups (target: 70%+)")
            all_passed = False
        else:
            print(f"\n[PASS] Good geographic clustering ({same_cluster_pct:.1f}%)")
    else:
        print(f"\n[WARNING] No cluster data available for analysis")
        print(f"  Games without cluster data: {no_cluster_data}")
    
    # ========================================================================
    # ISSUE 4: Insufficient games at school facilities
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 4: INSUFFICIENT GAMES AT SCHOOL FACILITIES")
    print("=" * 80)
    
    # Find schools with facilities
    schools_with_facilities = {}
    for facility in facilities:
        for team in teams:
            if team.school.name.lower() in facility.name.lower():
                if team.school.name not in schools_with_facilities:
                    schools_with_facilities[team.school.name] = {
                        'facility': facility,
                        'teams': []
                    }
                if team not in schools_with_facilities[team.school.name]['teams']:
                    schools_with_facilities[team.school.name]['teams'].append(team)
    
    print(f"\n[INFO] Schools with facilities: {len(schools_with_facilities)}")
    
    facility_usage = {}
    for game in schedule.games:
        facility_name = game.time_slot.facility.name
        game_date = game.time_slot.date
        
        if facility_name not in facility_usage:
            facility_usage[facility_name] = defaultdict(list)
        facility_usage[facility_name][game_date].append(game)
    
    insufficient_games = []
    for school_name, data in schools_with_facilities.items():
        facility = data['facility']
        num_teams = len(data['teams'])
        
        # Check games at this facility
        if facility.name in facility_usage:
            for game_date, games in facility_usage[facility.name].items():
                # Count games involving this school
                school_games = [g for g in games if 
                               g.home_team.school.name == school_name or 
                               g.away_team.school.name == school_name]
                
                if len(school_games) < num_teams and len(school_games) > 0:
                    insufficient_games.append({
                        'school': school_name,
                        'facility': facility.name,
                        'date': game_date,
                        'expected_games': num_teams,
                        'actual_games': len(school_games)
                    })
    
    if insufficient_games:
        print(f"\n[WARNING] {len(insufficient_games)} instances of insufficient games at school facilities:")
        for v in insufficient_games[:5]:
            print(f"  - {v['school']} at {v['facility']} on {v['date']}")
            print(f"    Expected {v['expected_games']} games, got {v['actual_games']}")
    else:
        print("\n[PASS] School facilities have adequate games")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    tests = [
        ("K-1 court restriction", len(k1_violations) == 0),
        ("School matchup clustering", len(spread_violations) == 0),
        ("Geographic clustering", same_cluster_pct >= 70 if total_with_data > 0 else False),
        ("Facility usage", len(insufficient_games) == 0)
    ]
    
    for test_name, passed in tests:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
    
    if all_passed:
        print("\n" + "=" * 80)
        print("ALL CRITICAL ISSUES RESOLVED!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("CRITICAL ISSUES FOUND - SEE DETAILS ABOVE")
        print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_all_critical_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
