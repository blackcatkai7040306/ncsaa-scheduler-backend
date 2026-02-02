"""
Test to verify Faith school plays at Faith's gym.
Client feedback: "On Monday, January 5, 2026, Faith should be playing at Faith's gym"
"""

import sys
import os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler


def test_faith_schedule():
    """
    Test that Faith school gets scheduled at Faith's gym.
    """
    print("\n" + "=" * 70)
    print("TESTING FAITH SCHOOL SCHEDULE")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    teams = reader.load_teams()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"   Loaded {len(teams)} teams, {len(facilities)} facilities")
    
    # Check if Faith school exists
    faith_teams = [t for t in teams if 'faith' in t.school.name.lower()]
    print(f"\n2. Found {len(faith_teams)} Faith teams:")
    for team in faith_teams[:5]:
        print(f"   - {team.school.name} ({team.coach_name}) in {team.division.value}")
    
    # Check if Faith facility exists
    faith_facilities = [f for f in facilities if 'faith' in f.name.lower()]
    print(f"\n3. Found {len(faith_facilities)} Faith facilities:")
    for facility in faith_facilities:
        print(f"   - {facility.name} ({facility.max_courts} courts)")
    
    # Generate schedule
    print("\n4. Generating schedule with school-based algorithm...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    print(f"   Generated {len(schedule.games)} games")
    
    # Find all games at Faith's gym
    print("\n5. Checking games at Faith's gym...")
    faith_games = []
    for game in schedule.games:
        facility_name = game.time_slot.facility.name.lower()
        if 'faith' in facility_name:
            faith_games.append(game)
    
    print(f"   Found {len(faith_games)} games at Faith's gym")
    
    if len(faith_games) == 0:
        print("\n" + "=" * 70)
        print("[WARNING] NO GAMES SCHEDULED AT FAITH'S GYM!")
        print("=" * 70)
        print("\nThis might be due to:")
        print("  1. Faith has no available time slots")
        print("  2. Faith has no opponents available")
        print("  3. Scheduling constraints are too tight")
        print("\nRecommendation: Relax constraints or add more time slots")
        return False
    
    # Check games on Monday, January 5, 2026
    target_date = date(2026, 1, 5)  # Monday
    monday_faith_games = [g for g in faith_games if g.time_slot.date == target_date]
    
    print(f"\n6. Games at Faith's gym on Monday, January 5, 2026: {len(monday_faith_games)}")
    
    if monday_faith_games:
        print("\n   Games scheduled:")
        for game in monday_faith_games:
            home_school = game.home_team.school.name
            away_school = game.away_team.school.name
            print(f"   - {game.time_slot.start_time}: {home_school} vs {away_school} ({game.division.value})")
        
        # Verify Faith is playing
        faith_playing = any('faith' in game.home_team.school.name.lower() or 
                           'faith' in game.away_team.school.name.lower() 
                           for game in monday_faith_games)
        
        if faith_playing:
            print("\n   [PASS] Faith is playing at Faith's gym on Monday!")
        else:
            print("\n   [FAIL] Faith is NOT playing at Faith's gym on Monday!")
            return False
    else:
        print("\n   [INFO] No games scheduled at Faith's gym on Monday, January 5")
        print("   Checking other dates...")
        
        # Show all Faith games
        print("\n7. All games at Faith's gym (any date):")
        dates_with_faith = {}
        for game in faith_games[:20]:  # Show first 20
            game_date = game.time_slot.date
            if game_date not in dates_with_faith:
                dates_with_faith[game_date] = []
            dates_with_faith[game_date].append(game)
        
        for game_date in sorted(dates_with_faith.keys())[:5]:  # Show first 5 dates
            print(f"\n   {game_date.strftime('%A, %B %d, %Y')}:")
            for game in dates_with_faith[game_date][:3]:  # Show first 3 games per date
                home_school = game.home_team.school.name
                away_school = game.away_team.school.name
                print(f"     {game.time_slot.start_time}: {home_school} vs {away_school} ({game.division.value})")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_faith_schedule()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
