"""
Test that K-1 courts (8ft rims) are ONLY used by K-1 REC division.

This ensures older divisions (JV, competitive, 2-3 REC) are NOT scheduled
on courts meant for younger children.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models.models import Division

def test_k1_court_restriction():
    print("\n" + "=" * 80)
    print("TESTING K-1 COURT RESTRICTION")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find K-1 facilities
    k1_facilities = [f for f in facilities if f.has_8ft_rims]
    
    print(f"\n[INFO] Found {len(k1_facilities)} facilities with 8ft rims (K-1 courts):")
    for facility in k1_facilities:
        print(f"  - {facility.name}")
    
    if not k1_facilities:
        print("\n[WARNING] No K-1 facilities found. Test cannot proceed.")
        return True
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check K-1 court usage
    print("\n" + "=" * 80)
    print("CHECKING K-1 COURT USAGE")
    print("=" * 80)
    
    violations = []
    k1_court_games = []
    
    for game in schedule.games:
        facility = game.time_slot.facility
        
        # If this is a K-1 court
        if facility.has_8ft_rims:
            k1_court_games.append(game)
            
            # Check if the game is K-1 REC division
            home_div = game.home_team.division
            away_div = game.away_team.division
            
            if home_div != Division.ES_K1_REC or away_div != Division.ES_K1_REC:
                violations.append({
                    'facility': facility.name,
                    'home_team': game.home_team.id,
                    'home_division': home_div.value,
                    'away_team': game.away_team.id,
                    'away_division': away_div.value,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time
                })
    
    print(f"\n[INFO] Total games on K-1 courts: {len(k1_court_games)}")
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} violations (older divisions on K-1 courts):")
        
        # Group by facility
        from collections import defaultdict
        by_facility = defaultdict(list)
        for v in violations:
            by_facility[v['facility']].append(v)
        
        for facility_name, facility_violations in by_facility.items():
            print(f"\n  {facility_name}: {len(facility_violations)} violations")
            for v in facility_violations[:5]:  # Show first 5
                print(f"    - {v['home_division']} game on {v['date']}")
                print(f"      {v['home_team']} vs {v['away_team']}")
        
        return False
    else:
        print("\n[PASS] All K-1 courts are ONLY used by K-1 REC division")
    
    # Verify K-1 REC games are scheduled correctly
    print("\n" + "=" * 80)
    print("CHECKING K-1 REC DIVISION GAMES")
    print("=" * 80)
    
    k1_rec_games = [g for g in schedule.games 
                    if g.home_team.division == Division.ES_K1_REC]
    
    print(f"\n[INFO] Total K-1 REC games: {len(k1_rec_games)}")
    
    # Check if K-1 REC games are on K-1 courts
    k1_rec_on_k1_courts = [g for g in k1_rec_games 
                           if g.time_slot.facility.has_8ft_rims]
    k1_rec_on_regular_courts = [g for g in k1_rec_games 
                                if not g.time_slot.facility.has_8ft_rims]
    
    print(f"  - On K-1 courts (8ft rims): {len(k1_rec_on_k1_courts)}")
    print(f"  - On regular courts: {len(k1_rec_on_regular_courts)}")
    
    if k1_rec_on_regular_courts:
        print(f"\n[WARNING] {len(k1_rec_on_regular_courts)} K-1 REC games on regular courts")
        print("  This is allowed but not ideal. K-1 courts may be fully booked.")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"K-1 facilities: {len(k1_facilities)}")
    print(f"Games on K-1 courts: {len(k1_court_games)}")
    print(f"K-1 REC games total: {len(k1_rec_games)}")
    print(f"K-1 REC on K-1 courts: {len(k1_rec_on_k1_courts)}")
    
    if violations:
        print(f"\n[FAIL] {len(violations)} older divisions scheduled on K-1 courts")
        return False
    else:
        print("\n[PASS] K-1 courts are properly restricted to K-1 REC division")
        return True

if __name__ == "__main__":
    try:
        success = test_k1_court_restriction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
