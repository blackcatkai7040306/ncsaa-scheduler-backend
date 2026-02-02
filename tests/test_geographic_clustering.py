"""
Test to verify geographic clustering is working correctly.
Client feedback: "Teams are traveling to the other side of town to play each other"
"""

import sys
import os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler


def test_geographic_clustering():
    """
    Test that teams are matched with nearby opponents (same cluster).
    """
    print("\n" + "=" * 70)
    print("TESTING GEOGRAPHIC CLUSTERING")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data from Google Sheets...")
    reader = SheetsReader()
    teams = reader.load_teams()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"   Loaded {len(teams)} teams, {len(facilities)} facilities")
    
    # Check cluster distribution
    print("\n2. Analyzing cluster distribution...")
    teams_by_cluster = defaultdict(list)
    teams_no_cluster = []
    
    for team in teams:
        if team.cluster:
            teams_by_cluster[team.cluster.value].append(team)
        else:
            teams_no_cluster.append(team)
    
    print(f"\n   Teams by cluster:")
    for cluster, cluster_teams in sorted(teams_by_cluster.items()):
        print(f"     {cluster}: {len(cluster_teams)} teams")
    
    if teams_no_cluster:
        print(f"\n   WARNING: {len(teams_no_cluster)} teams have NO cluster assigned!")
        print(f"   Sample teams without cluster:")
        for team in teams_no_cluster[:10]:
            print(f"     - {team.school.name} ({team.coach_name}) in {team.division.value}")
    
    # Generate schedule
    print("\n3. Generating schedule with school-based algorithm...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    print(f"   Generated {len(schedule.games)} games")
    
    # Analyze matchups by cluster
    print("\n4. Analyzing geographic matchups...")
    same_cluster_games = 0
    cross_cluster_games = 0
    no_cluster_games = 0
    
    cross_cluster_examples = []
    
    for game in schedule.games:
        home_cluster = game.home_team.cluster
        away_cluster = game.away_team.cluster
        
        if not home_cluster or not away_cluster:
            no_cluster_games += 1
        elif home_cluster == away_cluster:
            same_cluster_games += 1
        else:
            cross_cluster_games += 1
            if len(cross_cluster_examples) < 10:
                cross_cluster_examples.append({
                    'home': game.home_team.school.name,
                    'home_cluster': home_cluster.value,
                    'away': game.away_team.school.name,
                    'away_cluster': away_cluster.value,
                    'division': game.division.value,
                    'date': game.time_slot.date
                })
    
    total_with_cluster = same_cluster_games + cross_cluster_games
    
    print(f"\n   Same cluster matchups: {same_cluster_games} ({same_cluster_games*100//total_with_cluster if total_with_cluster > 0 else 0}%)")
    print(f"   Cross-cluster matchups: {cross_cluster_games} ({cross_cluster_games*100//total_with_cluster if total_with_cluster > 0 else 0}%)")
    print(f"   Games with missing cluster data: {no_cluster_games}")
    
    if cross_cluster_examples:
        print(f"\n   Examples of cross-cluster matchups:")
        for ex in cross_cluster_examples:
            print(f"     {ex['home']} ({ex['home_cluster']}) vs {ex['away']} ({ex['away_cluster']})")
            print(f"       Division: {ex['division']}, Date: {ex['date']}")
    
    # Check if clustering weight is effective
    print("\n5. Recommendations:")
    
    if teams_no_cluster:
        print(f"   [CRITICAL] {len(teams_no_cluster)} teams have no cluster assigned!")
        print(f"   Action: Update Google Sheet 'TIERS, CLUSTERS' to assign clusters to all schools")
    
    if cross_cluster_games > same_cluster_games:
        print(f"   [WARNING] More cross-cluster ({cross_cluster_games}) than same-cluster ({same_cluster_games}) games!")
        print(f"   Action: Increase geographic_cluster weight in config.py")
        print(f"   Current weight: 60, Recommended: 200+")
    elif same_cluster_games < total_with_cluster * 0.7:
        print(f"   [INFO] Only {same_cluster_games*100//total_with_cluster}% same-cluster matchups")
        print(f"   Target: 70%+ same-cluster matchups for good geographic clustering")
        print(f"   Action: Increase geographic_cluster weight in config.py")
    else:
        print(f"   [PASS] Good geographic clustering: {same_cluster_games*100//total_with_cluster}% same-cluster")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_geographic_clustering()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
