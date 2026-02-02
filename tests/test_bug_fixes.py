"""
Test script to verify the critical bug fixes:
1. Teams cannot be scheduled in multiple locations at the same time
2. Teams from the same school cannot play simultaneously
3. Teams play each other at most 2 times
"""

import sys
import os
from collections import defaultdict
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler import ScheduleOptimizer

def test_schedule_constraints():
    """Test that the schedule meets all critical constraints."""
    print("=" * 80)
    print("TESTING CRITICAL BUG FIXES")
    print("=" * 80)
    
    # Load data from Google Sheets
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    
    try:
        rules = reader.load_rules()
        teams = reader.load_teams()
        facilities = reader.load_facilities()
        
        print(f"   Loaded {len(teams)} teams, {len(facilities)} facilities")
        
        # Generate schedule
        print("\n2. Generating schedule...")
        optimizer = ScheduleOptimizer(teams, facilities, rules)
        schedule = optimizer.optimize_schedule()
        
        print(f"   Generated {len(schedule.games)} games")
        
        # Test 1: Check for team double-booking
        print("\n3. Testing for team double-booking...")
        team_time_slots = defaultdict(set)
        double_booking_errors = []
        
        for game in schedule.games:
            time_slot_key = (game.time_slot.date, game.time_slot.start_time)
            
            # Check home team
            if time_slot_key in team_time_slots[game.home_team.id]:
                double_booking_errors.append({
                    'team': game.home_team.id,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time,
                    'facility': game.time_slot.facility.name
                })
            team_time_slots[game.home_team.id].add(time_slot_key)
            
            # Check away team
            if time_slot_key in team_time_slots[game.away_team.id]:
                double_booking_errors.append({
                    'team': game.away_team.id,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time,
                    'facility': game.time_slot.facility.name
                })
            team_time_slots[game.away_team.id].add(time_slot_key)
        
        if double_booking_errors:
            print(f"   [FAIL] Found {len(double_booking_errors)} double-booking errors:")
            for error in double_booking_errors[:10]:
                print(f"      Team {error['team']} scheduled at {error['date']} {error['time']} at {error['facility']}")
        else:
            print("   [PASS] No team double-booking detected!")
        
        # Test 2: Check for facility/court conflicts
        print("\n4. Testing for facility/court conflicts...")
        facility_slots = defaultdict(set)
        facility_errors = []
        
        for game in schedule.games:
            slot_key = (game.time_slot.date, game.time_slot.start_time, 
                       game.time_slot.facility.name, game.time_slot.court_number)
            
            if slot_key in facility_slots:
                facility_errors.append({
                    'facility': game.time_slot.facility.name,
                    'court': game.time_slot.court_number,
                    'date': game.time_slot.date,
                    'time': game.time_slot.start_time
                })
            facility_slots[slot_key].add(True)
        
        facility_error_count = len(facility_errors)
        if facility_error_count > 0:
            print(f"   [FAIL] Found {facility_error_count} facility/court conflicts:")
            for error in facility_errors[:10]:
                print(f"      {error['facility']} Court {error['court']} at {error['date']} {error['time']}")
        else:
            print("   [PASS] No facility/court conflicts detected!")
        
        # Test 3: Check for same-school conflicts
        print("\n5. Testing for same-school conflicts...")
        same_school_errors = []
        
        for game in schedule.games:
            time_slot_key = (game.time_slot.date, game.time_slot.start_time)
            
            # Check if any other game has teams from same schools at same time
            for other_game in schedule.games:
                if other_game.id == game.id:
                    continue
                
                other_time_slot_key = (other_game.time_slot.date, other_game.time_slot.start_time)
                if other_time_slot_key == time_slot_key:
                    # Same time slot
                    schools_in_game = {game.home_team.school.name, game.away_team.school.name}
                    schools_in_other = {other_game.home_team.school.name, other_game.away_team.school.name}
                    
                    # Check for overlap
                    if schools_in_game & schools_in_other:
                        same_school_errors.append({
                            'school': list(schools_in_game & schools_in_other)[0],
                            'date': game.time_slot.date,
                            'time': game.time_slot.start_time,
                            'game1': f"{game.home_team.school.name} vs {game.away_team.school.name}",
                            'game2': f"{other_game.home_team.school.name} vs {other_game.away_team.school.name}"
                        })
        
        if same_school_errors:
            print(f"   [FAIL] Found {len(same_school_errors)} same-school conflicts:")
            for error in same_school_errors[:20]:  # Show first 20
                print(f"      School {error['school']} has teams playing at {error['date']} {error['time']}")
                print(f"         Game 1: {error['game1']}")
                print(f"         Game 2: {error['game2']}")
        else:
            print("   [PASS] No same-school conflicts detected!")
        
        # Test 4: Check for excessive rematches
        print("\n6. Testing for excessive rematches...")
        matchup_count = defaultdict(int)
        
        for game in schedule.games:
            matchup_key = tuple(sorted([game.home_team.id, game.away_team.id]))
            matchup_count[matchup_key] += 1
        
        excessive_rematches = [(k, v) for k, v in matchup_count.items() if v > 2]
        
        if excessive_rematches:
            print(f"   [FAIL] Found {len(excessive_rematches)} excessive rematches:")
            for matchup_key, count in excessive_rematches[:10]:
                print(f"      Teams {matchup_key[0]} vs {matchup_key[1]}: {count} games (max 2 allowed)")
        else:
            print("   [PASS] No excessive rematches detected!")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_errors = facility_error_count + len(double_booking_errors) + len(same_school_errors) + len(excessive_rematches)
        
        if total_errors == 0:
            print("[PASS] All critical bug fix tests passed!")
            print("=" * 80)
            return True
        else:
            print(f"[FAIL] TESTS FAILED with {total_errors} errors")
            print(f"  - Facility/court conflicts: {facility_error_count}")
            print(f"  - Team double-booking: {len(double_booking_errors)}")
            print(f"  - Same-school conflicts: {len(same_school_errors)}")
            print(f"  - Excessive rematches: {len(excessive_rematches)}")
            print("=" * 80)
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_schedule_constraints()
    sys.exit(0 if success else 1)
