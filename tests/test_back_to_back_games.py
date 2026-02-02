"""
Test to verify games are scheduled back-to-back on the same court.
Client feedback: "You have their schools spread out across 3 courts at the same time 
instead of back to back to back."
"""

import sys
import os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler


def test_back_to_back_scheduling():
    """
    Test that school matchups are scheduled back-to-back on the same court,
    not spread across multiple courts simultaneously.
    """
    print("\n" + "=" * 70)
    print("TESTING BACK-TO-BACK GAME SCHEDULING")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    teams = reader.load_teams()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"   Loaded {len(teams)} teams, {len(facilities)} facilities")
    
    # Generate schedule
    print("\n2. Generating schedule with school-based algorithm...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    print(f"   Generated {len(schedule.games)} games")
    
    # Group games by school matchup
    print("\n3. Analyzing game scheduling patterns...")
    matchups = defaultdict(list)
    
    for game in schedule.games:
        home_school = game.home_team.school.name
        away_school = game.away_team.school.name
        matchup_key = tuple(sorted([home_school, away_school]))
        matchups[matchup_key].append(game)
    
    # Analyze each matchup
    back_to_back_count = 0
    simultaneous_count = 0
    mixed_count = 0
    
    bad_examples = []
    good_examples = []
    
    for matchup_key, games in matchups.items():
        if len(games) < 2:
            continue  # Single game matchups don't matter
        
        # Group games by date and facility
        by_date_facility = defaultdict(list)
        for game in games:
            key = (game.time_slot.date, game.time_slot.facility.name)
            by_date_facility[key].append(game)
        
        for (date, facility), facility_games in by_date_facility.items():
            if len(facility_games) < 2:
                continue
            
            # Sort by start time
            facility_games.sort(key=lambda g: g.time_slot.start_time)
            
            # Check if games are on same court
            courts = [g.time_slot.court_number for g in facility_games]
            times = [g.time_slot.start_time for g in facility_games]
            
            # Check if all on same court
            if len(set(courts)) == 1:
                # All on same court - check if back-to-back
                is_back_to_back = True
                for i in range(len(times) - 1):
                    time1 = times[i]
                    time2 = times[i + 1]
                    # Calculate time difference
                    from datetime import datetime, timedelta
                    dt1 = datetime.combine(date, time1)
                    dt2 = datetime.combine(date, time2)
                    diff_minutes = (dt2 - dt1).total_seconds() / 60
                    
                    if diff_minutes != 60:  # Should be exactly 60 minutes apart
                        is_back_to_back = False
                        break
                
                if is_back_to_back:
                    back_to_back_count += 1
                    if len(good_examples) < 3:
                        good_examples.append({
                            'schools': f"{matchup_key[0]} vs {matchup_key[1]}",
                            'date': date,
                            'facility': facility,
                            'court': courts[0],
                            'times': times,
                            'divisions': [g.division.value for g in facility_games]
                        })
                else:
                    mixed_count += 1
            elif len(set(times)) == 1:
                # Same time, different courts - BAD!
                simultaneous_count += 1
                if len(bad_examples) < 5:
                    bad_examples.append({
                        'schools': f"{matchup_key[0]} vs {matchup_key[1]}",
                        'date': date,
                        'facility': facility,
                        'courts': courts,
                        'time': times[0],
                        'divisions': [g.division.value for g in facility_games]
                    })
            else:
                mixed_count += 1
    
    # Report results
    print(f"\n4. Results:")
    print(f"   Back-to-back on same court: {back_to_back_count} matchups")
    print(f"   Simultaneous on different courts: {simultaneous_count} matchups [BAD!]")
    print(f"   Mixed/other patterns: {mixed_count} matchups")
    
    if good_examples:
        print(f"\n5. Examples of CORRECT back-to-back scheduling:")
        for ex in good_examples:
            print(f"\n   {ex['schools']}")
            print(f"   Date: {ex['date']}, Facility: {ex['facility']}, Court: {ex['court']}")
            for i, (time, div) in enumerate(zip(ex['times'], ex['divisions'])):
                print(f"     Game {i+1}: {time} - {div}")
    
    if bad_examples:
        print(f"\n6. Examples of INCORRECT simultaneous scheduling:")
        for ex in bad_examples:
            print(f"\n   {ex['schools']} [PROBLEM!]")
            print(f"   Date: {ex['date']}, Facility: {ex['facility']}")
            print(f"   All at {ex['time']} on courts: {ex['courts']}")
            for i, (court, div) in enumerate(zip(ex['courts'], ex['divisions'])):
                print(f"     Court {court}: {div}")
        
        print("\n" + "=" * 70)
        print("[FAIL] Found simultaneous scheduling on multiple courts!")
        print("=" * 70)
        return False
    else:
        print("\n" + "=" * 70)
        print("[PASS] All games are scheduled back-to-back on same court!")
        print("=" * 70)
        return True


if __name__ == "__main__":
    try:
        success = test_back_to_back_scheduling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
