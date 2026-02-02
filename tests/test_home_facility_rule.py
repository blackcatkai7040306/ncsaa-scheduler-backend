"""
Test to verify Rule #10: The host school is always the home team.

This test ensures that if a game is at a school's facility, that school is the home team.
Example: If a game is at Faith's gym, Faith must be the home team.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict


def test_home_facility_rule():
    """
    Test that the host school is always the home team (Rule #10).
    """
    print("\n" + "=" * 70)
    print("TESTING RULE #10: Host School is Always Home Team")
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
    
    # Check home facility rule
    print("\n3. Checking home facility rule (Rule #10)...")
    violations = []
    
    # Group games by facility
    games_by_facility = defaultdict(list)
    for game in schedule.games:
        games_by_facility[game.time_slot.facility.name].append(game)
    
    # For each facility, check if the facility name matches a school
    for facility_name, facility_games in games_by_facility.items():
        # Check each game at this facility
        for game in facility_games:
            home_school = game.home_team.school.name
            away_school = game.away_team.school.name
            
            # Check if facility name matches a school name
            facility_lower = facility_name.lower()
            home_school_lower = home_school.lower()
            away_school_lower = away_school.lower()
            
            # If facility matches away school, that's a violation
            if away_school_lower in facility_lower and home_school_lower not in facility_lower:
                violations.append({
                    'facility': facility_name,
                    'home_team': home_school,
                    'away_team': away_school,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time,
                    'division': game.division.value
                })
    
    # Report results
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} home facility violations:\n")
        for v in violations[:10]:
            print(f"  Facility: {v['facility']}")
            print(f"  Home: {v['home_team']} (should be home)")
            print(f"  Away: {v['away_team']} (is actually home)")
            print(f"  Date/Time: {v['date']} at {v['time']}")
            print(f"  Division: {v['division']}")
            print()
        
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more violations")
        
        print("\n" + "=" * 70)
        print("TEST FAILED - Home facility rule violated!")
        print("=" * 70)
        return False
    else:
        print("\n[PASS] All games at school facilities have that school as home team!")
        print("Rule #10 is correctly enforced.")
        
        # Show some examples
        print("\nExamples of correct home facility assignments:")
        example_count = 0
        for facility_name, facility_games in sorted(games_by_facility.items()):
            for game in facility_games[:1]:  # Show first game at each facility
                home_school = game.home_team.school.name
                facility_lower = facility_name.lower()
                home_school_lower = home_school.lower()
                
                if home_school_lower in facility_lower:
                    print(f"  [OK] {facility_name}: {home_school} (home) vs {game.away_team.school.name} (away)")
                    example_count += 1
                    if example_count >= 5:
                        break
            if example_count >= 5:
                break
        
        print("\n" + "=" * 70)
        print("TEST PASSED")
        print("=" * 70)
        return True


if __name__ == "__main__":
    try:
        success = test_home_facility_rule()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
