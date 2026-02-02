"""
Check tier matchups to verify competitive balance.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict

def check_tier_matchups():
    print("\n" + "=" * 70)
    print("CHECKING TIER MATCHUPS")
    print("=" * 70)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    # Find Faith and Doral Saddle schools
    print("\n[INFO] Finding Faith and Doral Saddle schools...")
    
    faith_school = None
    doral_saddle_school = None
    
    for team in teams:
        if 'faith' in team.school.name.lower():
            faith_school = team.school
        if 'doral' in team.school.name.lower() and 'saddle' in team.school.name.lower():
            doral_saddle_school = team.school
    
    if faith_school:
        print(f"\n[FAITH]")
        print(f"  School: {faith_school.name}")
        print(f"  Tier: {faith_school.tier.value if faith_school.tier else 'NOT SET'}")
        print(f"  Cluster: {faith_school.cluster.value if faith_school.cluster else 'NOT SET'}")
    
    if doral_saddle_school:
        print(f"\n[DORAL SADDLE]")
        print(f"  School: {doral_saddle_school.name}")
        print(f"  Tier: {doral_saddle_school.tier.value if doral_saddle_school.tier else 'NOT SET'}")
        print(f"  Cluster: {doral_saddle_school.cluster.value if doral_saddle_school.cluster else 'NOT SET'}")
    
    if faith_school and doral_saddle_school:
        print(f"\n[ANALYSIS]")
        same_tier = faith_school.tier == doral_saddle_school.tier if (faith_school.tier and doral_saddle_school.tier) else False
        same_cluster = faith_school.cluster == doral_saddle_school.cluster if (faith_school.cluster and doral_saddle_school.cluster) else False
        
        print(f"  Same Tier: {'YES' if same_tier else 'NO'}")
        print(f"  Same Cluster: {'YES' if same_cluster else 'NO'}")
        
        if not same_tier and same_cluster:
            print(f"\n  [ISSUE] Different tiers but same cluster!")
            print(f"  This creates competitive imbalance.")
    
    # Generate schedule and check all tier mismatches
    print("\n" + "=" * 70)
    print("GENERATING SCHEDULE TO CHECK ALL TIER MATCHUPS")
    print("=" * 70)
    
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    
    # Check all school matchups
    matchups = scheduler._generate_school_matchups()
    
    tier_mismatch_count = 0
    tier_match_count = 0
    no_tier_data_count = 0
    
    print(f"\n[INFO] Analyzing {len(matchups)} school matchups...")
    
    tier_mismatches = []
    
    for matchup in matchups:
        school_a = matchup.school_a
        school_b = matchup.school_b
        
        if not school_a.tier or not school_b.tier:
            no_tier_data_count += 1
            continue
        
        if school_a.tier == school_b.tier:
            tier_match_count += 1
        else:
            tier_mismatch_count += 1
            tier_mismatches.append({
                'school_a': school_a.name,
                'tier_a': school_a.tier.value,
                'cluster_a': school_a.cluster.value if school_a.cluster else 'N/A',
                'school_b': school_b.name,
                'tier_b': school_b.tier.value,
                'cluster_b': school_b.cluster.value if school_b.cluster else 'N/A',
                'same_cluster': school_a.cluster == school_b.cluster if (school_a.cluster and school_b.cluster) else False
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("TIER MATCHING SUMMARY")
    print("=" * 70)
    print(f"Total matchups: {len(matchups)}")
    print(f"Same tier matchups: {tier_match_count}")
    print(f"Different tier matchups: {tier_mismatch_count}")
    print(f"No tier data: {no_tier_data_count}")
    
    if tier_match_count + tier_mismatch_count > 0:
        tier_match_percentage = (tier_match_count / (tier_match_count + tier_mismatch_count)) * 100
        print(f"\nTier matching rate: {tier_match_percentage:.1f}%")
    
    # Show some tier mismatches
    if tier_mismatches:
        print(f"\n[TIER MISMATCHES] Showing first 10:")
        for i, mismatch in enumerate(tier_mismatches[:10], 1):
            print(f"\n{i}. {mismatch['school_a']} ({mismatch['tier_a']}, {mismatch['cluster_a']})")
            print(f"   vs")
            print(f"   {mismatch['school_b']} ({mismatch['tier_b']}, {mismatch['cluster_b']})")
            if mismatch['same_cluster']:
                print(f"   [Same cluster but different tiers]")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        check_tier_matchups()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
