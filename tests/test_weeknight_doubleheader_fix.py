"""
Test that NO team plays a doubleheader (2+ games) on any weeknight.

This is a CRITICAL constraint that must apply to ALL teams.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict

def test_weeknight_doubleheader():
    print("\n" + "=" * 80)
    print("TESTING WEEKNIGHT DOUBLEHEADER CONSTRAINT")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams")
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check for weeknight doubleheaders
    print("\n" + "=" * 80)
    print("CHECKING FOR WEEKNIGHT DOUBLEHEADERS")
    print("=" * 80)
    
    # Group games by team and date
    team_games_by_date = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        game_date = game.time_slot.date
        
        # Add to home team's schedule
        team_games_by_date[game.home_team.id][game_date].append({
            'game': game,
            'role': 'home',
            'opponent': game.away_team.id,
            'time': game.time_slot.start_time,
            'facility': game.time_slot.facility.name,
            'court': game.time_slot.court_number
        })
        
        # Add to away team's schedule
        team_games_by_date[game.away_team.id][game_date].append({
            'game': game,
            'role': 'away',
            'opponent': game.home_team.id,
            'time': game.time_slot.start_time,
            'facility': game.time_slot.facility.name,
            'court': game.time_slot.court_number
        })
    
    # Find weeknight doubleheaders
    violations = []
    for team_id, dates in team_games_by_date.items():
        for game_date, games in dates.items():
            # Check if weeknight (Monday-Friday = 0-4)
            if game_date.weekday() < 5 and len(games) > 1:
                team = next(t for t in teams if t.id == team_id)
                violations.append({
                    'team_id': team_id,
                    'school': team.school.name,
                    'division': team.division.value,
                    'coach': team.coach_name,
                    'date': game_date,
                    'day_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][game_date.weekday()],
                    'num_games': len(games),
                    'games': games
                })
    
    print(f"\n[INFO] Total teams: {len(teams)}")
    print(f"[INFO] Teams with games: {len(team_games_by_date)}")
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} weeknight doubleheader violations:")
        
        # Group by school
        violations_by_school = defaultdict(list)
        for v in violations:
            violations_by_school[v['school']].append(v)
        
        for school, school_violations in sorted(violations_by_school.items()):
            print(f"\n  {school}: {len(school_violations)} violations")
            for v in school_violations:
                print(f"\n    Team: {v['team_id']}")
                print(f"    Division: {v['division']}")
                print(f"    Coach: {v['coach']}")
                print(f"    Date: {v['date']} ({v['day_of_week']})")
                print(f"    Games: {v['num_games']}")
                for i, game_info in enumerate(v['games'], 1):
                    print(f"      Game {i}: {game_info['time']} at {game_info['facility']} - Court {game_info['court']}")
                    print(f"              vs {game_info['opponent']} ({game_info['role']})")
        
        return False
    else:
        print("\n[PASS] No weeknight doubleheaders found")
    
    # Show weeknight game distribution
    print("\n" + "=" * 80)
    print("WEEKNIGHT GAME DISTRIBUTION")
    print("=" * 80)
    
    weeknight_games = [g for g in schedule.games if g.time_slot.date.weekday() < 5]
    print(f"\n[INFO] Total weeknight games: {len(weeknight_games)}")
    
    # Count teams with 1 game on weeknights
    teams_with_weeknight_games = set()
    for game in weeknight_games:
        teams_with_weeknight_games.add(game.home_team.id)
        teams_with_weeknight_games.add(game.away_team.id)
    
    print(f"[INFO] Teams playing on weeknights: {len(teams_with_weeknight_games)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total teams: {len(teams)}")
    print(f"Total games: {len(schedule.games)}")
    print(f"Weeknight games: {len(weeknight_games)}")
    print(f"Weeknight doubleheaders: {len(violations)}")
    
    if violations:
        print(f"\n[FAIL] {len(violations)} teams have weeknight doubleheaders")
        return False
    else:
        print("\n[PASS] No team plays more than 1 game on any weeknight")
        return True

if __name__ == "__main__":
    try:
        success = test_weeknight_doubleheader()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
