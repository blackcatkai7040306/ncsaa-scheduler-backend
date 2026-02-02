"""
Test that ES 2-3 REC games (1 ref) are ONLY scheduled at start or end of day.

This ensures they don't disrupt the 2-referee flow for other divisions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models.models import Division
from app.core.config import (
    WEEKNIGHT_START_TIME, WEEKNIGHT_END_TIME,
    SATURDAY_START_TIME, SATURDAY_END_TIME,
    GAME_DURATION_MINUTES
)
from datetime import datetime, timedelta, date, time

def get_time_slots_for_date(game_date: date):
    """Get all available time slots for a given date."""
    day_of_week = game_date.weekday()
    
    if day_of_week < 5:  # Weeknight
        time_slots = []
        current_time = WEEKNIGHT_START_TIME
        while current_time < WEEKNIGHT_END_TIME:
            end_time = (datetime.combine(date.min, current_time) + timedelta(minutes=GAME_DURATION_MINUTES)).time()
            if end_time <= WEEKNIGHT_END_TIME:
                time_slots.append(current_time)
            current_time = end_time
        return time_slots
    elif day_of_week == 5:  # Saturday
        time_slots = []
        current_time = SATURDAY_START_TIME
        while current_time < SATURDAY_END_TIME:
            end_time = (datetime.combine(date.min, current_time) + timedelta(minutes=GAME_DURATION_MINUTES)).time()
            if end_time <= SATURDAY_END_TIME:
                time_slots.append(current_time)
            current_time = end_time
        return time_slots
    else:
        return []

def test_es23_rec_timing():
    print("\n" + "=" * 80)
    print("TESTING ES 2-3 REC TIMING CONSTRAINT")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find ES 2-3 REC teams
    es23_teams = [t for t in teams if t.division == Division.ES_23_REC]
    
    print(f"\n[INFO] Found {len(es23_teams)} ES 2-3 REC teams")
    
    if not es23_teams:
        print("\n[WARNING] No ES 2-3 REC teams found. Test cannot proceed.")
        return True
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check ES 2-3 REC game timing
    print("\n" + "=" * 80)
    print("CHECKING ES 2-3 REC GAME TIMING")
    print("=" * 80)
    
    es23_games = [g for g in schedule.games 
                  if g.home_team.division == Division.ES_23_REC]
    
    print(f"\n[INFO] Total ES 2-3 REC games: {len(es23_games)}")
    
    violations = []
    start_of_day_games = []
    end_of_day_games = []
    
    for game in es23_games:
        game_date = game.time_slot.date
        game_time = game.time_slot.start_time
        
        # Get all time slots for this date
        time_slots = get_time_slots_for_date(game_date)
        
        if not time_slots:
            continue
        
        # Check if this is start or end of day
        is_start = (game_time == time_slots[0])
        is_end = (game_time == time_slots[-1])
        
        if is_start:
            start_of_day_games.append(game)
        elif is_end:
            end_of_day_games.append(game)
        else:
            # This is a middle-of-day game (violation!)
            violations.append({
                'game': game,
                'date': game_date,
                'time': game_time,
                'facility': game.time_slot.facility.name,
                'court': game.time_slot.court_number,
                'home_team': game.home_team.id,
                'away_team': game.away_team.id,
                'time_slots': time_slots,
                'position': time_slots.index(game_time) + 1 if game_time in time_slots else -1,
                'total_slots': len(time_slots)
            })
    
    print(f"\n[INFO] ES 2-3 REC game distribution:")
    print(f"  - Start of day: {len(start_of_day_games)}")
    print(f"  - End of day: {len(end_of_day_games)}")
    print(f"  - Middle of day (violations): {len(violations)}")
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} ES 2-3 REC games in middle of day:")
        
        for v in violations[:10]:  # Show first 10
            print(f"\n  {v['date']} at {v['time']}")
            print(f"    Facility: {v['facility']} - Court {v['court']}")
            print(f"    Game: {v['home_team']} vs {v['away_team']}")
            print(f"    Position: Slot {v['position']} of {v['total_slots']}")
            print(f"    Day slots: {v['time_slots'][0]} (start) ... {v['time_slots'][-1]} (end)")
        
        if len(violations) > 10:
            print(f"\n  ... and {len(violations) - 10} more violations")
        
        return False
    else:
        print("\n[PASS] All ES 2-3 REC games are at start or end of day")
    
    # Show some examples
    if start_of_day_games:
        print(f"\n[INFO] Example start-of-day ES 2-3 REC games:")
        for game in start_of_day_games[:3]:
            print(f"  - {game.time_slot.date} at {game.time_slot.start_time}")
            print(f"    {game.home_team.id} vs {game.away_team.id}")
    
    if end_of_day_games:
        print(f"\n[INFO] Example end-of-day ES 2-3 REC games:")
        for game in end_of_day_games[:3]:
            print(f"  - {game.time_slot.date} at {game.time_slot.start_time}")
            print(f"    {game.home_team.id} vs {game.away_team.id}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"ES 2-3 REC teams: {len(es23_teams)}")
    print(f"ES 2-3 REC games: {len(es23_games)}")
    print(f"Start of day: {len(start_of_day_games)}")
    print(f"End of day: {len(end_of_day_games)}")
    print(f"Middle of day (violations): {len(violations)}")
    
    if violations:
        print(f"\n[FAIL] ES 2-3 REC games found in middle of day")
        return False
    else:
        print("\n[PASS] All ES 2-3 REC games at day boundaries (start or end)")
        return True

if __name__ == "__main__":
    try:
        success = test_es23_rec_timing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
