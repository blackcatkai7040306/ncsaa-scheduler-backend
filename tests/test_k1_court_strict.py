"""
CRITICAL TEST: K-1 Court Strict Enforcement

Verifies that K-1 courts (8ft rims) are NEVER used by non-K-1 REC divisions.
This is a HARD CONSTRAINT that must NEVER be violated.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models import Division

def test_k1_court_strict():
    """Test that K-1 courts are NEVER used by non-K-1 REC divisions."""
    
    print("="*80)
    print("CRITICAL TEST: K-1 Court Strict Enforcement")
    print("="*80)
    
    # Load data
    print("\n[1/3] Loading data from Google Sheets...")
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Identify K-1 facilities
    k1_facilities = [f for f in facilities if f.has_8ft_rims]
    print(f"\n[2/3] Found {len(k1_facilities)} K-1 facilities (8ft rims):")
    for fac in k1_facilities:
        print(f"  - {fac.name}")
    
    # Generate schedule
    print("\n[3/3] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    # Check for violations
    print("\n" + "="*80)
    print("CHECKING FOR K-1 COURT VIOLATIONS")
    print("="*80)
    
    violations = []
    k1_court_games = []
    
    for game in schedule.games:
        # Check if this game is on a K-1 court
        if game.time_slot.facility.has_8ft_rims:
            k1_court_games.append(game)
            
            # Check if the division is NOT K-1 REC
            if game.division != Division.ES_K1_REC:
                violations.append({
                    'game': game,
                    'facility': game.time_slot.facility.name,
                    'division': game.division.value,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time
                })
    
    # Report results
    print(f"\nTotal games on K-1 courts: {len(k1_court_games)}")
    print(f"K-1 COURT VIOLATIONS: {len(violations)}")
    
    if violations:
        print("\n" + "="*80)
        print("[FAIL] K-1 COURT VIOLATIONS FOUND!")
        print("="*80)
        
        for v in violations:
            print(f"\n  VIOLATION:")
            print(f"    Facility: {v['facility']}")
            print(f"    Division: {v['division']} (should be ES K-1 REC)")
            print(f"    Date: {v['date'].strftime('%A, %B %d, %Y')}")
            print(f"    Time: {v['time'].strftime('%I:%M %p')}")
            print(f"    Game: {v['game'].home_team.id} vs {v['game'].away_team.id}")
        
        print("\n" + "="*80)
        print("TEST FAILED: K-1 courts must ONLY be used by ES K-1 REC division")
        print("="*80)
        return False
    else:
        print("\n" + "="*80)
        print("[PASS] NO K-1 COURT VIOLATIONS!")
        print("="*80)
        
        # Show breakdown of K-1 court usage
        print(f"\nK-1 Court Usage Breakdown:")
        for fac in k1_facilities:
            games_at_fac = [g for g in k1_court_games if g.time_slot.facility.name == fac.name]
            print(f"  {fac.name}: {len(games_at_fac)} games (all ES K-1 REC)")
        
        print("\n" + "="*80)
        print("TEST PASSED: K-1 courts are correctly restricted!")
        print("="*80)
        return True

if __name__ == "__main__":
    try:
        success = test_k1_court_strict()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
