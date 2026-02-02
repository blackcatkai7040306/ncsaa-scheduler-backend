"""
Test for coach conflicts - coaches scheduled at multiple places at same time.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict
from datetime import datetime

def test_coach_conflicts():
    print("\n" + "=" * 70)
    print("TESTING FOR COACH CONFLICTS")
    print("=" * 70)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find coaches with multiple teams
    print("\n[INFO] Finding coaches with multiple teams...")
    coaches_teams = defaultdict(list)
    for team in teams:
        coaches_teams[team.coach_name].append(team)
    
    multi_team_coaches = {coach: teams_list for coach, teams_list in coaches_teams.items() if len(teams_list) > 1}
    
    print(f"[INFO] Found {len(multi_team_coaches)} coaches with multiple teams")
    
    # Show Ferrell specifically
    print("\n" + "=" * 70)
    print("FERRELL'S TEAMS")
    print("=" * 70)
    ferrell_teams = [t for t in teams if 'ferrell' in t.coach_name.lower()]
    for team in ferrell_teams:
        print(f"  - {team.id}")
        print(f"    School: {team.school.name}")
        print(f"    Division: {team.division.value}")
        print()
    
    # Generate schedule
    print("=" * 70)
    print("GENERATING SCHEDULE...")
    print("=" * 70)
    
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check for coach conflicts
    print("\n" + "=" * 70)
    print("CHECKING FOR COACH CONFLICTS")
    print("=" * 70)
    
    coach_time_slots = defaultdict(list)  # coach_name -> [(date, time, team, facility, court)]
    
    for game in schedule.games:
        # Track home team coach
        date_time = (game.time_slot.date, game.time_slot.start_time)
        coach_time_slots[game.home_team.coach_name].append({
            'date': game.time_slot.date,
            'time': game.time_slot.start_time,
            'team': game.home_team.id,
            'facility': game.time_slot.facility.name,
            'court': game.time_slot.court_number,
            'opponent': game.away_team.id
        })
        
        # Track away team coach
        coach_time_slots[game.away_team.coach_name].append({
            'date': game.time_slot.date,
            'time': game.time_slot.start_time,
            'team': game.away_team.id,
            'facility': game.time_slot.facility.name,
            'court': game.time_slot.court_number,
            'opponent': game.home_team.id
        })
    
    # Find conflicts
    conflicts_found = 0
    ferrell_conflicts = []
    
    for coach, slots in coach_time_slots.items():
        # Group by date and time
        time_groups = defaultdict(list)
        for slot in slots:
            key = (slot['date'], slot['time'])
            time_groups[key].append(slot)
        
        # Check for conflicts (same coach, same time, different courts)
        for (date, time), games in time_groups.items():
            if len(games) > 1:
                conflicts_found += 1
                print(f"\n[CONFLICT] Coach {coach} has {len(games)} games at {date} {time}:")
                for game in games:
                    print(f"  - {game['team']} vs {game['opponent']}")
                    print(f"    at {game['facility']} - Court {game['court']}")
                
                if 'ferrell' in coach.lower():
                    ferrell_conflicts.append({
                        'coach': coach,
                        'date': date,
                        'time': time,
                        'games': games
                    })
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total coach conflicts: {conflicts_found}")
    print(f"Ferrell conflicts: {len(ferrell_conflicts)}")
    
    if ferrell_conflicts:
        print("\n[FERRELL SPECIFIC CONFLICTS]")
        for conflict in ferrell_conflicts:
            print(f"  Date: {conflict['date']}, Time: {conflict['time']}")
            for game in conflict['games']:
                print(f"    - {game['team']} at {game['facility']} Court {game['court']}")
    
    if conflicts_found > 0:
        print(f"\n[FAIL] Found {conflicts_found} coach conflicts!")
        return False
    else:
        print("\n[PASS] No coach conflicts found!")
        return True

if __name__ == "__main__":
    try:
        success = test_coach_conflicts()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
