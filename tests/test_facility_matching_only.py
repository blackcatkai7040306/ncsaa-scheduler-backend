"""
Quick test to verify facility matching logic is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scheduler_v2 import SchoolBasedScheduler


def test_facility_matching():
    """
    Test that facility matching works correctly for all edge cases.
    """
    print("\n" + "=" * 70)
    print("TESTING FACILITY MATCHING LOGIC")
    print("=" * 70)
    
    # Create a mock scheduler instance
    scheduler = type('obj', (object,), {})()
    scheduler._facility_belongs_to_school = SchoolBasedScheduler._facility_belongs_to_school.__get__(scheduler, type(scheduler))
    
    # Test cases based on client feedback
    test_cases = [
        # Pinecrest Sloan Canyon variants (with typo "Pincrest")
        ('Pincrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon', True, 'Base school'),
        ('Pincrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon Blue', True, 'Blue team'),
        ('Pincrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon Black', True, 'Black team'),
        ('Pincrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon White', True, 'White team'),
        ('Pincrest Sloan Canyon - MAIN GYM', 'Pinecrest Sloan Canyon', True, 'Main gym'),
        
        # Pinecrest Sloan Canyon (correct spelling)
        ('Pinecrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon', True, 'Correct spelling'),
        ('Pinecrest Sloan Canyon - K-1 GYM', 'Pinecrest Sloan Canyon Blue', True, 'Correct + Blue'),
        
        # Faith variants
        ('Faith Lutheran - GYM', 'Faith', True, 'Faith base'),
        ('Faith Lutheran - GYM', 'Faith 6A', True, 'Faith 6A'),
        ('Faith Lutheran - GYM', 'Faith 7A', True, 'Faith 7A'),
        
        # Somerset variants
        ('Somerset Skye Canyon - MPR', 'Somerset Skye Canyon', True, 'Somerset exact'),
        ('Somerset Sky Pointe - GYM', 'Somerset Sky Pointe', True, 'Sky Pointe'),
        
        # Negative cases (should NOT match)
        ('Las Vegas Basketball Center', 'Pinecrest Sloan Canyon', False, 'Neutral facility'),
        ('Somerset Skye Canyon - MPR', 'Pinecrest Sloan Canyon', False, 'Different schools'),
        ('Faith Lutheran - GYM', 'Somerset Skye Canyon', False, 'Completely different'),
        ('Skye Canyon - GYM', 'Somerset Skye Canyon', False, 'Partial match only'),
    ]
    
    print("\n1. Running test cases...")
    passed = 0
    failed = 0
    
    for facility, school, expected, description in test_cases:
        result = scheduler._facility_belongs_to_school(facility, school)
        status = 'PASS' if result == expected else 'FAIL'
        
        if result == expected:
            passed += 1
            print(f"   [PASS] {description}")
            print(f"          {school} at {facility}")
        else:
            failed += 1
            print(f"   [FAIL] {description}")
            print(f"          {school} at {facility}")
            print(f"          Expected: {expected}, Got: {result}")
    
    print(f"\n2. Results:")
    print(f"   Passed: {passed}/{len(test_cases)}")
    print(f"   Failed: {failed}/{len(test_cases)}")
    
    print("\n" + "=" * 70)
    if failed == 0:
        print("[SUCCESS] All facility matching tests passed!")
        print("=" * 70)
        return True
    else:
        print("[FAILURE] Some tests failed!")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = test_facility_matching()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
