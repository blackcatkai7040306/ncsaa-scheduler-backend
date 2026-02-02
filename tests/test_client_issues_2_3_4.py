"""
Test client's specific issues:
2. Teams spread out over different days instead of grouped together
3. Teams playing across town
4. Faith first night only 1 game instead of 3
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from collections import defaultdict

def test_client_issues():
    print("\n" + "=" * 80)
    print("TESTING CLIENT'S SPECIFIC ISSUES")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams from {len(set(t.school.name for t in teams))} schools")
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # ========================================================================
    # ISSUE 2: Teams spread out over different days
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 2: TEAMS SPREAD OUT OVER DIFFERENT DAYS")
    print("=" * 80)
    
    # Group games by school and date
    school_games_by_date = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        home_school = game.home_team.school.name
        away_school = game.away_team.school.name
        game_date = game.time_slot.date
        
        school_games_by_date[home_school][game_date].append(game)
        school_games_by_date[away_school][game_date].append(game)
    
    # Find schools playing on multiple days
    schools_multiple_days = []
    for school, dates in school_games_by_date.items():
        if len(dates) > 1:
            schools_multiple_days.append({
                'school': school,
                'num_days': len(dates),
                'dates': sorted(dates.keys()),
                'games_per_day': {date: len(games) for date, games in dates.items()}
            })
    
    print(f"\n[INFO] Schools playing on multiple days: {len(schools_multiple_days)} / {len(school_games_by_date)}")
    
    # Show examples
    for school_info in sorted(schools_multiple_days, key=lambda x: x['num_days'], reverse=True)[:10]:
        print(f"\n  {school_info['school']}: {school_info['num_days']} different days")
        for date in school_info['dates']:
            print(f"    - {date}: {school_info['games_per_day'][date]} games")
    
    # ========================================================================
    # ISSUE 3: Teams playing across town
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 3: TEAMS PLAYING ACROSS TOWN")
    print("=" * 80)
    
    cross_cluster_games = []
    same_cluster_games = []
    missing_cluster_games = []
    
    for game in schedule.games:
        home_cluster = game.home_team.cluster
        away_cluster = game.away_team.cluster
        
        if not home_cluster or not away_cluster:
            missing_cluster_games.append(game)
        elif home_cluster == away_cluster:
            same_cluster_games.append(game)
        else:
            cross_cluster_games.append({
                'home_school': game.home_team.school.name,
                'home_cluster': home_cluster.value,
                'away_school': game.away_team.school.name,
                'away_cluster': away_cluster.value,
                'date': game.time_slot.date,
                'facility': game.time_slot.facility.name
            })
    
    total_with_clusters = len(same_cluster_games) + len(cross_cluster_games)
    cross_cluster_pct = (len(cross_cluster_games) / total_with_clusters * 100) if total_with_clusters > 0 else 0
    
    print(f"\n[INFO] Cross-cluster games: {len(cross_cluster_games)} / {total_with_clusters} ({cross_cluster_pct:.1f}%)")
    print(f"[INFO] Same-cluster games: {len(same_cluster_games)} ({100 - cross_cluster_pct:.1f}%)")
    print(f"[INFO] Missing cluster data: {len(missing_cluster_games)}")
    
    # Show specific cross-cluster examples
    print(f"\n[EXAMPLES] Cross-cluster games:")
    for cc_game in cross_cluster_games[:10]:
        print(f"  - {cc_game['home_school']} ({cc_game['home_cluster']}) vs "
              f"{cc_game['away_school']} ({cc_game['away_cluster']})")
        print(f"    Date: {cc_game['date']}, Facility: {cc_game['facility']}")
    
    # ========================================================================
    # ISSUE 4: Faith first night only 1 game
    # ========================================================================
    print("\n" + "=" * 80)
    print("ISSUE 4: FAITH FIRST NIGHT - NEED 3 GAMES")
    print("=" * 80)
    
    # Find Faith teams
    faith_teams = [t for t in teams if 'faith' in t.school.name.lower()]
    print(f"\n[INFO] Faith has {len(faith_teams)} teams:")
    for team in faith_teams:
        print(f"  - {team.id} ({team.division.value})")
    
    # Find Faith facility
    faith_facilities = [f for f in facilities if 'faith' in f.name.lower()]
    if faith_facilities:
        print(f"\n[INFO] Faith facilities:")
        for facility in faith_facilities:
            print(f"  - {facility.name}")
        
        # Find games at Faith facility
        faith_facility_games = defaultdict(list)
        for game in schedule.games:
            if 'faith' in game.time_slot.facility.name.lower():
                faith_facility_games[game.time_slot.date].append(game)
        
        if faith_facility_games:
            print(f"\n[INFO] Games at Faith facility by date:")
            for date in sorted(faith_facility_games.keys()):
                games = faith_facility_games[date]
                print(f"\n  {date}: {len(games)} games")
                
                # Check if Faith is playing
                faith_playing = [g for g in games if 
                                'faith' in g.home_team.school.name.lower() or 
                                'faith' in g.away_team.school.name.lower()]
                
                print(f"    Faith playing: {len(faith_playing)} games")
                
                for game in games[:5]:
                    faith_marker = ""
                    if 'faith' in game.home_team.school.name.lower() or 'faith' in game.away_team.school.name.lower():
                        faith_marker = " [FAITH]"
                    print(f"      {game.time_slot.start_time}: {game.home_team.school.name} vs "
                          f"{game.away_team.school.name}{faith_marker}")
            
            # Check first night
            first_night = min(faith_facility_games.keys())
            first_night_games = faith_facility_games[first_night]
            first_night_faith_games = [g for g in first_night_games if 
                                       'faith' in g.home_team.school.name.lower() or 
                                       'faith' in g.away_team.school.name.lower()]
            
            print(f"\n[CRITICAL] First night at Faith ({first_night}):")
            print(f"  Total games: {len(first_night_games)}")
            print(f"  Faith playing: {len(first_night_faith_games)}")
            print(f"  Expected: 3 Faith games (all Faith teams)")
            
            if len(first_night_faith_games) < 3:
                print(f"\n  [ISSUE] Only {len(first_night_faith_games)} Faith games on first night!")
                print(f"  Need: 3 games (Faith has {len(faith_teams)} teams)")
    else:
        print("\n[WARNING] No Faith facility found!")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nIssue 2 (Teams spread out):")
    print(f"  - Schools on multiple days: {len(schools_multiple_days)} / {len(school_games_by_date)}")
    print(f"  - This is EXPECTED for 8-game season")
    
    print(f"\nIssue 3 (Playing across town):")
    print(f"  - Cross-cluster games: {len(cross_cluster_games)} ({cross_cluster_pct:.1f}%)")
    print(f"  - Target: <30% cross-cluster")
    print(f"  - Status: {'GOOD' if cross_cluster_pct < 30 else 'NEEDS IMPROVEMENT'}")
    
    print(f"\nIssue 4 (Faith first night):")
    if faith_facilities and faith_facility_games:
        first_night = min(faith_facility_games.keys())
        first_night_faith_games = [g for g in faith_facility_games[first_night] if 
                                   'faith' in g.home_team.school.name.lower() or 
                                   'faith' in g.away_team.school.name.lower()]
        print(f"  - First night Faith games: {len(first_night_faith_games)} / 3 expected")
        print(f"  - Status: {'GOOD' if len(first_night_faith_games) >= 3 else 'ISSUE'}")
    else:
        print(f"  - Status: Cannot verify (no Faith facility data)")

if __name__ == "__main__":
    try:
        test_client_issues()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
