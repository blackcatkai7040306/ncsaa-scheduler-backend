"""
Test: Court-Level School Matchup Reservation

Verifies that once a court is used by a school matchup (e.g., Faith vs Mater East),
NO other school matchup can use that court on the same night.

This ensures weeknight courts are dedicated to a single school matchup.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, time
from collections import defaultdict
from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler

def test_court_reservation():
    """Test that courts are reserved for single school matchup per night."""
    
    print("="*80)
    print("TEST: Court-Level School Matchup Reservation")
    print("="*80)
    
    # Load data
    print("\n[1/3] Loading data from Google Sheets...")
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Generate schedule
    print("\n[2/3] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    # Analyze weeknight court usage
    print("\n[3/3] Analyzing weeknight court usage...")
    
    # Group games by (date, facility, court)
    court_usage = defaultdict(list)  # {(date, facility, court): [(school_a, school_b), ...]}
    
    for game in schedule.games:
        if game.time_slot.date.weekday() < 5:  # Weeknight only
            court_key = (
                game.time_slot.date,
                game.time_slot.facility.name,
                game.time_slot.court_number
            )
            matchup = tuple(sorted([game.home_team.school.name, game.away_team.school.name]))
            court_usage[court_key].append(matchup)
    
    # Check for violations
    violations = []
    for court_key, matchups in court_usage.items():
        unique_matchups = set(matchups)
        if len(unique_matchups) > 1:
            date, facility, court = court_key
            violations.append({
                'date': date,
                'facility': facility,
                'court': court,
                'matchups': unique_matchups
            })
    
    # Report results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} court(s) with mixed school matchups:\n")
        
        for v in violations:
            print(f"  {v['date'].strftime('%A, %B %d, %Y')}")
            print(f"  {v['facility']} - Court {v['court']}")
            print(f"  Mixed matchups:")
            for matchup in v['matchups']:
                print(f"    - {matchup[0]} vs {matchup[1]}")
            print()
        
        print("="*80)
        print("TEST FAILED: Courts should be reserved for single school matchup")
        print("="*80)
        return False
    else:
        print("\n[PASS] All weeknight courts are reserved for single school matchup!")
        print("\nVerified:")
        print(f"  - {len(court_usage)} court-nights checked")
        print(f"  - 0 violations found")
        print("\n" + "="*80)
        print("TEST PASSED: Court reservation working correctly!")
        print("="*80)
        return True

if __name__ == "__main__":
    try:
        success = test_court_reservation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
