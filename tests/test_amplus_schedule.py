"""
Test Amplus school schedule to verify back-to-back games and single-night clustering.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict

def test_amplus_schedule():
    print("\n" + "=" * 70)
    print("TESTING AMPLUS SCHEDULE")
    print("=" * 70)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find Amplus teams
    print("\n[INFO] Finding Amplus teams...")
    amplus_teams = [t for t in teams if 'amplus' in t.school.name.lower()]
    
    print(f"\n[AMPLUS TEAMS] Found {len(amplus_teams)} teams:")
    for team in amplus_teams:
        print(f"  - {team.id}")
        print(f"    Division: {team.division.value}")
        print(f"    Coach: {team.coach_name}")
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
    
    # Find all Amplus games
    print("\n" + "=" * 70)
    print("AMPLUS GAMES ANALYSIS")
    print("=" * 70)
    
    amplus_games = []
    for game in schedule.games:
        if 'amplus' in game.home_team.school.name.lower() or 'amplus' in game.away_team.school.name.lower():
            amplus_games.append(game)
    
    print(f"\n[INFO] Found {len(amplus_games)} games involving Amplus")
    
    # Group by date
    games_by_date = defaultdict(list)
    for game in amplus_games:
        date_key = game.time_slot.date
        games_by_date[date_key].append(game)
    
    print(f"\n[INFO] Amplus plays on {len(games_by_date)} different dates")
    
    # Analyze each date
    issues_found = 0
    
    for date in sorted(games_by_date.keys()):
        games = games_by_date[date]
        print(f"\n{'=' * 70}")
        print(f"DATE: {date} ({len(games)} games)")
        print('=' * 70)
        
        # Group by opponent school
        games_by_opponent = defaultdict(list)
        for game in games:
            if 'amplus' in game.home_team.school.name.lower():
                opponent = game.away_team.school.name
            else:
                opponent = game.home_team.school.name
            games_by_opponent[opponent].append(game)
        
        print(f"\nOpponents on this date: {list(games_by_opponent.keys())}")
        
        # Check for simultaneous games (same time, different courts)
        games_by_time = defaultdict(list)
        for game in games:
            time_key = game.time_slot.start_time
            games_by_time[time_key].append(game)
        
        for time, time_games in sorted(games_by_time.items()):
            if len(time_games) > 1:
                print(f"\n[ISSUE] {len(time_games)} Amplus games at {time}:")
                issues_found += 1
                for game in time_games:
                    amplus_team = game.home_team if 'amplus' in game.home_team.school.name.lower() else game.away_team
                    opponent = game.away_team if 'amplus' in game.home_team.school.name.lower() else game.home_team
                    print(f"  - {amplus_team.id} vs {opponent.id}")
                    print(f"    at {game.time_slot.facility.name} - Court {game.time_slot.court_number}")
            else:
                game = time_games[0]
                amplus_team = game.home_team if 'amplus' in game.home_team.school.name.lower() else game.away_team
                opponent = game.away_team if 'amplus' in game.home_team.school.name.lower() else game.home_team
                print(f"\n[OK] {time}: {amplus_team.id} vs {opponent.id}")
                print(f"     at {game.time_slot.facility.name} - Court {game.time_slot.court_number}")
    
    # Check if multiple opponents on different nights
    print("\n" + "=" * 70)
    print("OPPONENT ANALYSIS")
    print("=" * 70)
    
    all_opponents = defaultdict(list)  # opponent -> list of dates
    for date, games in games_by_date.items():
        for game in games:
            if 'amplus' in game.home_team.school.name.lower():
                opponent = game.away_team.school.name
            else:
                opponent = game.home_team.school.name
            all_opponents[opponent].append(date)
    
    for opponent, dates in all_opponents.items():
        unique_dates = sorted(set(dates))
        if len(unique_dates) > 1:
            print(f"\n[ISSUE] Amplus vs {opponent} on {len(unique_dates)} different nights:")
            issues_found += 1
            for date in unique_dates:
                games_on_date = [g for g in games_by_date[date] 
                                if opponent in (g.home_team.school.name, g.away_team.school.name)]
                print(f"  - {date}: {len(games_on_date)} games")
        else:
            games_count = len([g for g in games_by_date[unique_dates[0]] 
                             if opponent in (g.home_team.school.name, g.away_team.school.name)])
            print(f"\n[OK] Amplus vs {opponent}: {games_count} games on {unique_dates[0]}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Amplus games: {len(amplus_games)}")
    print(f"Dates Amplus plays: {len(games_by_date)}")
    print(f"Issues found: {issues_found}")
    
    if issues_found > 0:
        print(f"\n[FAIL] Found {issues_found} scheduling issues!")
        return False
    else:
        print("\n[PASS] No scheduling issues found!")
        return True

if __name__ == "__main__":
    try:
        success = test_amplus_schedule()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
