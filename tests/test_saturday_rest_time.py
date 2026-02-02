"""
Test that non-rec divisions have at least 1 hour rest between games on Saturdays.

Client requirement: "When we do a doubleheader we want an hour in between games 
in all non-rec divisions. This should only happen on Saturday's."
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler
from app.models.models import Division
from collections import defaultdict
from datetime import datetime, timedelta

def test_saturday_rest_time():
    print("\n" + "=" * 80)
    print("TESTING SATURDAY REST TIME CONSTRAINT")
    print("=" * 80)
    
    reader = SheetsReader()
    teams, facilities, rules = reader.load_all_data()
    
    print(f"\n[INFO] Loaded {len(teams)} teams")
    
    # Generate schedule
    print("\n[INFO] Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    if not schedule or not schedule.games:
        print("[ERROR] No schedule generated!")
        return False
    
    print(f"[INFO] Generated {len(schedule.games)} games")
    
    # Check Saturday rest time
    print("\n" + "=" * 80)
    print("CHECKING SATURDAY REST TIME")
    print("=" * 80)
    
    # Group games by team and date
    team_games_by_date = defaultdict(lambda: defaultdict(list))
    for game in schedule.games:
        game_date = game.time_slot.date
        
        # Add to home team's schedule
        team_games_by_date[game.home_team.id][game_date].append({
            'game': game,
            'time': game.time_slot.start_time,
            'division': game.home_team.division,
            'opponent': game.away_team.id
        })
        
        # Add to away team's schedule
        team_games_by_date[game.away_team.id][game_date].append({
            'game': game,
            'time': game.time_slot.start_time,
            'division': game.away_team.division,
            'opponent': game.home_team.id
        })
    
    # Find Saturday doubleheaders with insufficient rest
    violations = []
    saturday_doubleheaders = []
    
    for team_id, dates in team_games_by_date.items():
        for game_date, games in dates.items():
            # Check if Saturday (weekday 5)
            if game_date.weekday() == 5 and len(games) > 1:
                team = next(t for t in teams if t.id == team_id)
                
                # Check if non-rec division
                is_rec = (team.division == Division.ES_K1_REC or team.division == Division.ES_23_REC)
                
                saturday_doubleheaders.append({
                    'team_id': team_id,
                    'school': team.school.name,
                    'division': team.division.value,
                    'is_rec': is_rec,
                    'date': game_date,
                    'num_games': len(games),
                    'games': games
                })
                
                if not is_rec:
                    # Non-rec division - check rest time
                    # Sort games by time
                    sorted_games = sorted(games, key=lambda g: g['time'])
                    
                    # Check time between consecutive games
                    for i in range(len(sorted_games) - 1):
                        game1_time = datetime.combine(game_date, sorted_games[i]['time'])
                        game2_time = datetime.combine(game_date, sorted_games[i + 1]['time'])
                        
                        time_diff_minutes = (game2_time - game1_time).total_seconds() / 60
                        
                        if time_diff_minutes < 60:
                            violations.append({
                                'team_id': team_id,
                                'school': team.school.name,
                                'division': team.division.value,
                                'date': game_date,
                                'game1_time': sorted_games[i]['time'],
                                'game2_time': sorted_games[i + 1]['time'],
                                'rest_minutes': int(time_diff_minutes)
                            })
    
    print(f"\n[INFO] Saturday doubleheaders: {len(saturday_doubleheaders)}")
    
    # Show distribution
    rec_doubleheaders = [d for d in saturday_doubleheaders if d['is_rec']]
    non_rec_doubleheaders = [d for d in saturday_doubleheaders if not d['is_rec']]
    
    print(f"  - Rec divisions (K-1, 2-3): {len(rec_doubleheaders)} (no rest requirement)")
    print(f"  - Non-rec divisions (Comp, JV): {len(non_rec_doubleheaders)} (need 1-hour rest)")
    
    if violations:
        print(f"\n[FAIL] Found {len(violations)} Saturday rest time violations:")
        
        for v in violations[:10]:  # Show first 10
            print(f"\n  {v['team_id']}")
            print(f"    School: {v['school']}")
            print(f"    Division: {v['division']}")
            print(f"    Date: {v['date']} (Saturday)")
            print(f"    Game 1: {v['game1_time']}")
            print(f"    Game 2: {v['game2_time']}")
            print(f"    Rest time: {v['rest_minutes']} minutes (need 60)")
        
        if len(violations) > 10:
            print(f"\n  ... and {len(violations) - 10} more violations")
        
        return False
    else:
        print("\n[PASS] All non-rec Saturday doubleheaders have at least 1-hour rest")
    
    # Show examples of correct scheduling
    if non_rec_doubleheaders:
        print(f"\n[INFO] Example non-rec Saturday doubleheaders:")
        for dh in non_rec_doubleheaders[:3]:
            print(f"\n  {dh['team_id']} ({dh['division']})")
            print(f"    Date: {dh['date']}")
            sorted_games = sorted(dh['games'], key=lambda g: g['time'])
            for i, game in enumerate(sorted_games, 1):
                print(f"    Game {i}: {game['time']}")
            
            if len(sorted_games) > 1:
                time1 = datetime.combine(dh['date'], sorted_games[0]['time'])
                time2 = datetime.combine(dh['date'], sorted_games[1]['time'])
                rest_minutes = int((time2 - time1).total_seconds() / 60)
                print(f"    Rest time: {rest_minutes} minutes")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total teams: {len(teams)}")
    print(f"Saturday doubleheaders: {len(saturday_doubleheaders)}")
    print(f"  - Rec divisions: {len(rec_doubleheaders)}")
    print(f"  - Non-rec divisions: {len(non_rec_doubleheaders)}")
    print(f"Rest time violations: {len(violations)}")
    
    if violations:
        print(f"\n[FAIL] {len(violations)} non-rec teams have insufficient rest on Saturdays")
        return False
    else:
        print("\n[PASS] All non-rec Saturday doubleheaders have proper rest time")
        return True

if __name__ == "__main__":
    try:
        success = test_saturday_rest_time()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
