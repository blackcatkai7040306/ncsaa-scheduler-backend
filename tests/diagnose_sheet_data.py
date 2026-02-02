"""
Diagnostic script to analyze Google Sheet data and identify potential issues.

This script will:
1. Load all data from Google Sheets
2. Count unique schools in team list vs TIERS/CLUSTERS tab
3. Identify schools missing cluster data
4. Report school name normalization results
5. Check for potential data quality issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from collections import defaultdict

def diagnose_sheet_data():
    print("\n" + "=" * 80)
    print("GOOGLE SHEET DATA DIAGNOSTIC")
    print("=" * 80)
    
    reader = SheetsReader()
    
    # Load all data
    print("\n[1/5] Loading data from Google Sheets...")
    teams = reader.load_teams()
    schools_dict = reader.load_schools()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"  - Loaded {len(teams)} teams")
    print(f"  - Loaded {len(schools_dict)} schools")
    print(f"  - Loaded {len(facilities)} facilities")
    
    # Analyze unique school names in team list
    print("\n[2/5] Analyzing school names in team list...")
    raw_school_names = set()
    normalized_school_names = set()
    school_team_count = defaultdict(int)
    
    for team in teams:
        raw_name = team.id.split('_')[0]  # Get school part before underscore
        # Extract school name from team ID (format: "School Name (Coach)")
        if '(' in raw_name:
            raw_name = raw_name.split('(')[0].strip()
        
        raw_school_names.add(raw_name)
        normalized_school_names.add(team.school.name)
        school_team_count[team.school.name] += 1
    
    print(f"  - Raw school name variations: {len(raw_school_names)}")
    print(f"  - Normalized school names: {len(normalized_school_names)}")
    print(f"  - Schools in TIERS/CLUSTERS tab: {len(schools_dict)}")
    
    # Find schools missing cluster data
    print("\n[3/5] Checking for missing cluster data...")
    schools_with_cluster = []
    schools_without_cluster = []
    
    for school_name in sorted(normalized_school_names):
        if school_name in schools_dict:
            school = schools_dict[school_name]
            if school.cluster:
                schools_with_cluster.append(school_name)
            else:
                schools_without_cluster.append(school_name)
        else:
            schools_without_cluster.append(school_name)
    
    print(f"  - Schools WITH cluster: {len(schools_with_cluster)}")
    print(f"  - Schools WITHOUT cluster: {len(schools_without_cluster)}")
    
    if schools_without_cluster:
        print(f"\n  Schools missing cluster data ({len(schools_without_cluster)}):")
        for school in schools_without_cluster[:20]:
            team_count = school_team_count[school]
            print(f"    - {school} ({team_count} teams)")
        if len(schools_without_cluster) > 20:
            print(f"    ... and {len(schools_without_cluster) - 20} more")
    
    # Check tier data
    print("\n[4/5] Checking tier data...")
    schools_with_tier = []
    schools_without_tier = []
    
    for school_name in sorted(normalized_school_names):
        if school_name in schools_dict:
            school = schools_dict[school_name]
            if school.tier:
                schools_with_tier.append(school_name)
            else:
                schools_without_tier.append(school_name)
        else:
            schools_without_tier.append(school_name)
    
    print(f"  - Schools WITH tier: {len(schools_with_tier)}")
    print(f"  - Schools WITHOUT tier: {len(schools_without_tier)}")
    
    # Sample raw vs normalized names
    print("\n[5/5] Sample school name normalization:")
    sample_count = 0
    for raw_name in sorted(raw_school_names):
        # Find corresponding normalized name
        normalized = reader._normalize_school_name(raw_name)
        if raw_name != normalized:
            print(f"  '{raw_name}' -> '{normalized}'")
            sample_count += 1
            if sample_count >= 15:
                break
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    cluster_coverage = (len(schools_with_cluster) / len(normalized_school_names) * 100) if normalized_school_names else 0
    tier_coverage = (len(schools_with_tier) / len(normalized_school_names) * 100) if normalized_school_names else 0
    
    print(f"Total teams: {len(teams)}")
    print(f"Unique schools (after normalization): {len(normalized_school_names)}")
    print(f"Schools in TIERS/CLUSTERS tab: {len(schools_dict)}")
    print(f"Cluster coverage: {cluster_coverage:.1f}%")
    print(f"Tier coverage: {tier_coverage:.1f}%")
    
    if cluster_coverage < 100:
        print(f"\n[WARNING] {len(schools_without_cluster)} schools are missing cluster data!")
        print("This will cause cross-town travel issues.")
    
    if tier_coverage < 100:
        print(f"\n[WARNING] {len(schools_without_tier)} schools are missing tier data!")
        print("This will affect competitive balance.")
    
    # Check for potential data quality issues
    print("\n" + "=" * 80)
    print("DATA QUALITY CHECKS")
    print("=" * 80)
    
    # Check 1: Schools with very few teams
    print("\n[CHECK 1] Schools with only 1-2 teams:")
    small_schools = [(name, count) for name, count in school_team_count.items() if count <= 2]
    if small_schools:
        for school, count in sorted(small_schools)[:10]:
            print(f"  - {school}: {count} team(s)")
        if len(small_schools) > 10:
            print(f"  ... and {len(small_schools) - 10} more")
    else:
        print("  [PASS] All schools have 3+ teams")
    
    # Check 2: Facilities with K-1 courts
    print("\n[CHECK 2] Facilities with K-1 courts (8ft rims):")
    k1_facilities = [f for f in facilities if f.has_8ft_rims]
    if k1_facilities:
        for facility in k1_facilities:
            print(f"  - {facility.name}")
    else:
        print("  [WARNING] No K-1 facilities found!")
    
    # Check 3: Teams in each division
    print("\n[CHECK 3] Teams per division:")
    division_count = defaultdict(int)
    for team in teams:
        division_count[team.division.value] += 1
    
    for division in sorted(division_count.keys()):
        print(f"  - {division}: {division_count[division]} teams")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        diagnose_sheet_data()
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
