"""
Report which schools are missing cluster assignments.
This helps the client know what needs to be updated in Google Sheets.
"""

import sys
import os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader


def report_missing_clusters():
    """
    Generate a report of schools missing cluster assignments.
    """
    print("\n" + "=" * 70)
    print("SCHOOLS MISSING CLUSTER ASSIGNMENTS")
    print("=" * 70)
    print("\nThis report shows which schools need cluster assignments")
    print("in the Google Sheet: 'TIERS, CLUSTERS, RIVALS, DO NOT PLAY'")
    
    # Load data
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    teams = reader.load_teams()
    
    print(f"   Loaded {len(teams)} teams")
    
    # Group by school
    schools_with_cluster = set()
    schools_without_cluster = set()
    school_teams = defaultdict(list)
    
    for team in teams:
        school_name = team.school.name
        school_teams[school_name].append(team)
        
        if team.cluster:
            schools_with_cluster.add(school_name)
        else:
            schools_without_cluster.add(school_name)
    
    # Remove schools that have at least one team with a cluster
    schools_without_cluster = schools_without_cluster - schools_with_cluster
    
    print(f"\n2. Analysis:")
    print(f"   Schools with cluster: {len(schools_with_cluster)}")
    print(f"   Schools WITHOUT cluster: {len(schools_without_cluster)}")
    
    if schools_without_cluster:
        print(f"\n3. SCHOOLS NEEDING CLUSTER ASSIGNMENT:")
        print(f"   Please update these {len(schools_without_cluster)} schools in Google Sheet:\n")
        
        for school_name in sorted(schools_without_cluster):
            teams_count = len(school_teams[school_name])
            divisions = [t.division.value for t in school_teams[school_name]]
            print(f"   - {school_name}")
            print(f"     Teams: {teams_count}")
            print(f"     Divisions: {', '.join(set(divisions))}")
            print()
        
        print("\n4. INSTRUCTIONS:")
        print("   a. Open Google Sheet: 'TIERS, CLUSTERS, RIVALS, DO NOT PLAY'")
        print("   b. Find each school listed above")
        print("   c. In the 'Cluster' column, assign one of:")
        print("      - East")
        print("      - West")
        print("      - North")
        print("      - Henderson")
        print("   d. Save the sheet")
        print("   e. Re-run the scheduler")
        
        print("\n5. CLUSTER GUIDELINES:")
        print("   - East: Schools in eastern Las Vegas")
        print("   - West: Schools in western Las Vegas")
        print("   - North: Schools in northern Las Vegas")
        print("   - Henderson: Schools in Henderson area")
        print("   - Assign based on school location to minimize travel")
    else:
        print("\n   [PASS] All schools have cluster assignments!")
    
    print("\n" + "=" * 70)
    print("REPORT COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = report_missing_clusters()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Report failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
