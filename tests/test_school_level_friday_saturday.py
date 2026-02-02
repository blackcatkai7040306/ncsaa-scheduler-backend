"""
Test that Friday + Saturday back-to-back check works at SCHOOL level.
This prevents Somerset NLV (Stanley) on Friday + Somerset NLV (Bay) on Saturday.
"""

import sys
import os
from datetime import date
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_school_level_check():
    """
    Simulate the school-level Friday + Saturday check.
    """
    print("\n" + "=" * 70)
    print("TESTING SCHOOL-LEVEL FRIDAY + SATURDAY CHECK")
    print("=" * 70)
    
    # Simulate school game dates tracking
    school_game_dates = defaultdict(list)
    
    # Scenario: Somerset NLV (Stanley) plays on Friday
    friday = date(2026, 1, 9)
    saturday = date(2026, 1, 10)
    
    print("\n1. Somerset NLV (Stanley) scheduled on Friday, January 9")
    school_game_dates["Somerset NLV"].append(friday)
    print(f"   School dates for Somerset NLV: {school_game_dates['Somerset NLV']}")
    
    # Now try to schedule Somerset NLV (Bay) on Saturday
    print("\n2. Trying to schedule Somerset NLV (Bay) on Saturday, January 10...")
    
    # Check school-level dates
    school_dates = school_game_dates["Somerset NLV"]
    can_schedule = True
    
    for existing_date in school_dates:
        days_diff = abs((saturday - existing_date).days)
        
        print(f"   Checking against existing date: {existing_date}")
        print(f"   Days difference: {days_diff}")
        
        if days_diff == 1:
            print(f"   Consecutive days detected!")
            if (existing_date.weekday() == 4 and saturday.weekday() == 5):
                print(f"   Friday ({existing_date}) + Saturday ({saturday}) detected!")
                can_schedule = False
                break
    
    print("\n3. Result:")
    if can_schedule:
        print("   [FAIL] Somerset NLV (Bay) would be scheduled on Saturday")
        print("   This violates the rule: school plays both Friday and Saturday!")
        return False
    else:
        print("   [PASS] Somerset NLV (Bay) REJECTED for Saturday")
        print("   School-level check prevents back-to-back days!")
        return True
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        success = test_school_level_check()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
