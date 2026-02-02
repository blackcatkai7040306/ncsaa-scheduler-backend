"""
Test that same-school matchups are COMPLETELY prevented at ALL levels.

This test verifies THREE layers of protection:
1. Matchup generation (don't create same-school matchups)
2. Matchup scoring (return -inf for same-school)
3. Team pairing (don't pair teams from same school)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler

def test_same_school_prevention():
    print("\n" + "=" * 80)
    print("TESTING SAME-SCHOOL MATCHUP PREVENTION")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams from {len(set(t.school.name for t in teams))} schools")
    
    # Check for schools with multiple teams
    from collections import defaultdict
    teams_by_school = defaultdict(list)
    for team in teams:
        teams_by_school[team.school.name].append(team)
    
    multi_team_schools = {school: teams_list for school, teams_list in teams_by_school.items() if len(teams_list) > 1}
    
    print(f"\n[INFO] Found {len(multi_team_schools)} schools with multiple teams:")
    for school, school_teams in sorted(multi_team_schools.items()):
        print(f"  - {school}: {len(school_teams)} teams")
    
    # Generate matchups
    print("\n" + "=" * 80)
    print("LAYER 1: MATCHUP GENERATION")
    print("=" * 80)
    
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    matchups = scheduler._generate_school_matchups()
    
    print(f"\n[INFO] Generated {len(matchups)} school matchups")
    
    # Check for same-school matchups
    same_school_matchups = []
    for matchup in matchups:
        if matchup.school_a.name == matchup.school_b.name:
            same_school_matchups.append(matchup)
    
    if same_school_matchups:
        print(f"\n[FAIL] Found {len(same_school_matchups)} same-school matchups:")
        for matchup in same_school_matchups[:5]:
            print(f"  - {matchup.school_a.name} vs {matchup.school_b.name}")
            print(f"    Games: {len(matchup.games)}")
        return False
    else:
        print("\n[PASS] No same-school matchups in generated matchups")
    
    # Check matchup scoring
    print("\n" + "=" * 80)
    print("LAYER 2: MATCHUP SCORING")
    print("=" * 80)
    
    # Test scoring for schools with multiple teams
    test_schools = list(multi_team_schools.keys())[:5]  # Test first 5
    
    all_scores_correct = True
    for school_name in test_schools:
        school_obj = next(t.school for t in teams if t.school.name == school_name)
        
        # Try to score a same-school matchup
        score = scheduler._calculate_school_matchup_score(school_obj, school_obj, [])
        
        if score != float('-inf'):
            print(f"\n[FAIL] {school_name} vs {school_name} scored {score} (should be -inf)")
            all_scores_correct = False
        else:
            print(f"[PASS] {school_name} vs {school_name} correctly scored as -inf")
    
    if not all_scores_correct:
        return False
    
    # Generate full schedule
    print("\n" + "=" * 80)
    print("LAYER 3: FULL SCHEDULE GENERATION")
    print("=" * 80)
    
    print("\n[INFO] Generating full schedule...")
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check for same-school games
    same_school_games = []
    for game in schedule.games:
        if game.home_team.school.name == game.away_team.school.name:
            same_school_games.append(game)
    
    if same_school_games:
        print(f"\n[FAIL] Found {len(same_school_games)} same-school games:")
        
        # Group by school
        games_by_school = defaultdict(list)
        for game in same_school_games:
            games_by_school[game.home_team.school.name].append(game)
        
        for school, games in games_by_school.items():
            print(f"\n  {school}: {len(games)} violations")
            for game in games[:3]:
                print(f"    - {game.home_team.id} vs {game.away_team.id}")
                print(f"      Date: {game.time_slot.date}")
                print(f"      Facility: {game.time_slot.facility.name}")
        
        return False
    else:
        print("\n[PASS] No same-school games in final schedule")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("[PASS] Layer 1: Matchup generation - no same-school matchups")
    print("[PASS] Layer 2: Matchup scoring - same-school returns -inf")
    print("[PASS] Layer 3: Full schedule - no same-school games")
    print("\n" + "=" * 80)
    print("ALL LAYERS VERIFIED - SAME-SCHOOL PREVENTION WORKING!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_same_school_prevention()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
