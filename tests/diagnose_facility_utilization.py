"""
Diagnostic script to analyze facility utilization and identify scheduling gaps.

This helps understand why teams aren't getting 8 games and why facilities are under-utilized.
"""
import sys
sys.path.insert(0, 'app')

from services.sheets_reader import SheetsReader
from services.scheduler_v2 import SchoolBasedScheduler
from core.config import SATURDAY_START_TIME, SATURDAY_END_TIME, WEEKNIGHT_START_TIME, WEEKNIGHT_END_TIME, GAME_DURATION_MINUTES
from datetime import datetime, timedelta, time

def count_available_slots(start_time: time, end_time: time) -> int:
    """Count how many game slots fit in a time range."""
    slots = 0
    current = datetime.combine(datetime.min, start_time)
    end_dt = datetime.combine(datetime.min, end_time)
    
    while current < end_dt:
        next_time = current + timedelta(minutes=GAME_DURATION_MINUTES)
        if next_time.time() <= end_time:
            slots += 1
        current = next_time
    
    return slots

def main():
    print("=== FACILITY UTILIZATION DIAGNOSTIC ===\n")
    
    # Load data
    reader = SheetsReader()
    data = reader.load_all_data()
    
    # Generate schedule
    print("Generating schedule...\n")
    scheduler = SchoolBasedScheduler(
        teams=data['teams'],
        facilities=data['facilities'],
        rules=data['rules'],
        season_start=data['rules']['season_start'],
        season_end=data['rules']['season_end']
    )
    
    schedule = scheduler.optimize_schedule()
    
    print(f"\n=== SCHEDULE SUMMARY ===")
    print(f"Total games scheduled: {len(schedule.games)}")
    print(f"Total teams: {len(data['teams'])}")
    print(f"Expected total games: {len(data['teams']) * 4} (if all teams play 8 games)")
    print(f"Actual vs Expected: {len(schedule.games)} / {len(data['teams']) * 4} = {len(schedule.games) / (len(data['teams']) * 4) * 100:.1f}%\n")
    
    # Count team games
    from collections import defaultdict
    team_game_counts = defaultdict(int)
    for game in schedule.games:
        team_game_counts[game.home_team.id] += 1
        team_game_counts[game.away_team.id] += 1
    
    teams_with_8 = sum(1 for count in team_game_counts.values() if count == 8)
    teams_under_8 = sum(1 for count in team_game_counts.values() if count < 8)
    
    print(f"=== TEAM GAME COUNT ===")
    print(f"Teams with 8 games: {teams_with_8} / {len(data['teams'])} ({teams_with_8 / len(data['teams']) * 100:.1f}%)")
    print(f"Teams under 8 games: {teams_under_8}")
    
    if teams_under_8 > 0:
        print(f"\nTeams needing more games:")
        for team_id, count in sorted(team_game_counts.items(), key=lambda x: x[1]):
            if count < 8:
                team = next(t for t in data['teams'] if t.id == team_id)
                print(f"  {team.school.name} ({team.division.value}): {count} games (need {8 - count} more)")
    
    print(f"\n=== FACILITY UTILIZATION ===\n")
    
    # Analyze by date and facility
    games_by_date_facility = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for game in schedule.games:
        date = game.time_slot.date
        facility = game.time_slot.facility.name
        court = game.time_slot.court_number
        games_by_date_facility[date][facility][court] += 1
    
    # Calculate available slots for each facility
    facility_info = {f.name: f for f in data['facilities']}
    
    total_slots_available = 0
    total_slots_used = 0
    
    for date in sorted(games_by_date_facility.keys()):
        day_name = date.strftime('%A, %B %d')
        is_saturday = date.weekday() == 5
        is_weeknight = date.weekday() < 5
        
        if is_saturday:
            slots_per_court = count_available_slots(SATURDAY_START_TIME, SATURDAY_END_TIME)
        elif is_weeknight:
            slots_per_court = count_available_slots(WEEKNIGHT_START_TIME, WEEKNIGHT_END_TIME)
        else:
            continue
        
        print(f"\n{day_name} ({'Saturday' if is_saturday else 'Weeknight'}):")
        print(f"  Time slots per court: {slots_per_court}")
        
        for facility_name in sorted(games_by_date_facility[date].keys()):
            if facility_name not in facility_info:
                continue
            
            facility = facility_info[facility_name]
            courts = games_by_date_facility[date][facility_name]
            
            # Available capacity
            total_available = facility.max_courts * slots_per_court
            total_used = sum(courts.values())
            utilization_pct = (total_used / total_available * 100) if total_available > 0 else 0
            
            total_slots_available += total_available
            total_slots_used += total_used
            
            print(f"\n  {facility_name}:")
            print(f"    Courts available: {facility.max_courts}")
            print(f"    Total slots available: {total_available} ({facility.max_courts} courts × {slots_per_court} slots)")
            print(f"    Total games scheduled: {total_used}")
            print(f"    Utilization: {utilization_pct:.1f}%")
            
            # Show per-court breakdown
            for court_num in sorted(courts.keys()):
                games = courts[court_num]
                court_util = (games / slots_per_court * 100) if slots_per_court > 0 else 0
                status = "✅ FULL" if games >= slots_per_court else f"❌ UNDER ({games}/{slots_per_court})"
                print(f"      Court {court_num}: {games} games ({court_util:.1f}%) {status}")
            
            # Identify unused courts
            used_courts = set(courts.keys())
            all_courts = set(range(1, facility.max_courts + 1))
            unused_courts = all_courts - used_courts
            if unused_courts:
                print(f"      ⚠️  Unused courts: {sorted(unused_courts)} (0 games scheduled)")
    
    print(f"\n=== OVERALL UTILIZATION ===")
    overall_util = (total_slots_used / total_slots_available * 100) if total_slots_available > 0 else 0
    print(f"Total slots available: {total_slots_available}")
    print(f"Total slots used: {total_slots_used}")
    print(f"Overall utilization: {overall_util:.1f}%")
    print(f"Wasted capacity: {total_slots_available - total_slots_used} slots ({100 - overall_util:.1f}%)\n")
    
    if overall_util < 70:
        print("⚠️  WARNING: Facility utilization is LOW (<70%)")
        print("   This means teams can't get 8 games because we're not using available space!\n")

if __name__ == "__main__":
    main()
