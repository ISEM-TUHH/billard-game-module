from collections import Counter
from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class Curling2(GameMode):
    """ 
    A 1vs1 curling gamemode where players score points by placing their respective balls
    closest to the target bullseye.
    """
    # Constants
    TABLE_WIDTH = 2230
    TABLE_HEIGHT = 1115
    LINE_LEFT_X = 300
    LINE_RIGHT_X = 1930
    BULLSEYE_RADIUS = 200
    
    
    def __init__(self):
        self.__file__ = __file__
        self.gamemode_name = "Curling2"
        self.state = "init"
        
        self.plays_per_round = 3
        self.rounds = 3
        self.mode = "classic"
        
        self.current_round = 1
        self.current_play_in_round = 0
        self.player_scores = { "player1": 0, "player2": 0}
        self.current_round_score = {
            "round_summary": "round_summary loading",
            "winner": None,
            "points": 0
        }
        
        self.current_player = None
        self.player1 = None
        self.player2 = None
        
        self.gameimage = GameImage()
        
        self.TREE = {
            "init": [
                self.setup_game,
                {"start": "play", "reset": "init"},
                lambda: [
                    {"type": "text", "text": "Enter player names and set up the game"},
                    {"type": "central_image", "img": "isem-logo-big"}
                ],
                ["Start Game"]
            ],
            "play": [
                self.play_turn,
                {"next_turn": "play", "finish_round": "round_finished"},
                lambda: self.get_play_image_definition(),
                ["Submit Turn"]
            ],
            "round_finished": [
                self.finish_round,
                {"next_round": "play", "end_game": "finished"},
                lambda: [
                    {"type": "text", "text": self.current_round_score["round_summary"] + "\nStandings: " + self.get_standings()},
                    {"type": "central_image", "img": "isem-logo-big"}
                ],
                ["Next Round", "End Game"]
            ],
            "finished": [
                self.finish_game,
                {"init": "init"},
                lambda: [
                    {"type": "text", "text": "Final Score: " + self.get_standings()},
                    {"type": "central_image", "img": "isem-logo-big"}
                ],
                [None]
            ]
        }

        GameMode.__init__(self)
        
        self.saved_history = self.get_history()
        self.player_names = self.get_history_data("player1", "player2")
        self.team_names = self.get_history_data("team1", "team2")


    def setup_game(self, inp):
        print("INP CURLING GAME:", inp)
        
        self.mode = inp["game_mode"]
        self.bullseye_center = self.get_bullseye_position()
        self.negative_points = inp['negative_points']
        self.submit_only_last_turn = inp['submit_only_last_turn']
        self.plays_per_round = max(1, min(7, int(inp['plays_per_round'])))
        self.rounds = max(1, min(10, int(inp['rounds'])))
        p1_name = inp['player1']
        p2_name = inp['player2']
        p1_team = inp['team1']
        p2_team = inp['team2']

        self.player1 = {
            "name": p1_name if p1_name else "Player 1",
            "team": p1_team if p1_team else ""
        }
        self.player2 = {
            "name": p2_name if p2_name else "Player 2",
            "team": p2_team if p2_team else ""
        }
        
        self.HISTORY = {
            "player1": self.player1["name"],
            "player2": self.player2["name"],
            "team1": self.player1["team"],
            "team2": self.player2["team"],
            "score1": 0,
            "score2": 0,
            "winner": None,
        }
        
        self.current_round = 1
        self.current_play_in_round = 0
        self.current_player = self.player1
        self.player_scores = {"player1": 0, "player2": 0}
        
        return "start", {}, {"message": f"Game started! {self.current_player['name']}'s turn. (full)"}
    
    
    def play_turn(self, inp):
        coords = inp.get("coordinates", {})
        
        if self.submit_only_last_turn: 
            self.current_round_score = self.get_round_results(coords)
            self.message = "Hello World :)"
            self.update_history()
            
            return "finish_round", {}, {"message": f"Round {self.current_round} finished!"}       
    
        self.current_play_in_round += 1
            
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        if self.current_play_in_round >= self.plays_per_round*2:
            self.current_round_score = self.get_round_results(coords)
            self.message = "Hello World"
            self.update_history()
            return "finish_round", {}, {"message": f"Round {self.current_round} finished!"}
        else:
            return "next_turn", {}, {"message": f"{self.current_player['name']}'s turn. ({'full' if self.current_player == self.player1 else 'striped'})"}
    
    
    def finish_round(self, inp):
        round_results = self.current_round_score
        if round_results["winner"]:
            msg = round_results["round_summary"]
        else:
            msg = f"The round ends in a draw with no points given"
            
        self.current_round += 1
        self.current_play_in_round = 0

        if round_results["winner"]:
            self.current_player = self.player1 if round_results["winner"] == "player1" else self.player2
        
        if self.current_round > self.rounds or inp['clicked_on'] == "End Game":
            return "end_game", {}, {"message": msg + " " + self.get_standings(), "notification": "Match Finished", "hist-package": self.HISTORY}
        else:
            return "next_round", {}, {"message": msg}
     
        
    def finish_game(self, inp):
        return "init", {}, {"message": f"Game over"}
    
        
    def get_play_image_definition(self):
        
        if self.submit_only_last_turn:
            round_text = f"Round: {self.current_round}/{self.rounds} | Starting player: {self.current_player['name']} | Play all turns and hit 'Submit' to finish round"
        else:
            round_text = f"Round {self.current_round}/{self.rounds} | play {self.current_play_in_round + 1}/{self.plays_per_round*2} | Turn: {self.current_player['name']}"
        
        base = [
            {
                "type": "text", 
                "text": round_text
            },
            {
                "type": "bullseye", 
                "center": self.bullseye_center,
                "radius": 200
            }
        ]
        
        if self.mode == "center":
            base.append(
                {
                    "type": "line",
                    "ref": "start_line_left",
                    "c1": {"x": self.LINE_LEFT_X, "y": 0},
                    "c2": {"x": self.LINE_LEFT_X, "y": self.TABLE_HEIGHT},
                    "color": "white" if self.current_player == self.player1 or self.submit_only_last_turn else "black",
                    "width": 5
                })
            
            base.append(
                {
                    "type": "line",
                    "ref": "start_line_right",
                    "c1": {"x": self.LINE_RIGHT_X, "y": 0},
                    "c2": {"x": self.LINE_RIGHT_X, "y": self.TABLE_HEIGHT},
                    "color": "white" if self.current_player == self.player2 or self.submit_only_last_turn else "black",
                    "width": 5
                }
            )
        else:
            base.append({
                "type": "line",
                "ref": "start_line_right",
                "c1": {"x": self.LINE_RIGHT_X, "y": 0},
                "c2": {"x": self.LINE_RIGHT_X, "y": self.TABLE_HEIGHT},
                "color": "white",
                "width": 5
            })
        
        return base
    
    
    def update_history(self):
        self.HISTORY["score1"] = self.player_scores["player1"]
        self.HISTORY["score2"] = self.player_scores["player2"]
        
        if self.HISTORY["score1"] > self.HISTORY["score2"]:
            self.HISTORY["winner"] = self.player1["name"]
        elif self.HISTORY["score2"] > self.HISTORY["score1"]:
            self.HISTORY["winner"] = self.player2["name"]
        else:
            self.HISTORY["winner"] = "draw"
        
        
    def history(self, add=None):
        history_df = self.saved_history
        
        if add is not None:
            new_entry = pd.DataFrame([add])
            self.saved_history = pd.concat([history_df, new_entry], ignore_index=True)
            self.save_history(self.saved_history)
        history_df = self.saved_history
        
        if history_df.empty or "winner" not in history_df.columns:
            return {
                "single_table": [],
                "single_columns": ["Player", "Wins"],
                "team_table": []
            }
        
        wins = history_df["winner"].value_counts().to_dict()
        
        table = [
            [player, count]
            for player, count in wins.items()
            if player != "draw" and pd.notna(player)
        ]
        
        player1_winner = history_df["winner"] == history_df["player1"]
        player2_winner = history_df["winner"] == history_df["player2"]
        
        winning_teams = pd.concat([
            history_df.loc[player1_winner, "team1"],
            history_df.loc[player2_winner, "team2"]
        ])
        team_wins = winning_teams.value_counts().to_dict()
        team_table = [
            [count, team]
            for team, count in team_wins.items()
            if team != "draw" and pd.notna(team)
        ]
        
        return {
            "single_table": table,
            "single_columns": ["Player", "Wins"],
            "team_table": team_table
        }
    
    
    def get_bullseye_position(self):
        if self.mode == "center":
            return [self.TABLE_WIDTH//2, self.TABLE_HEIGHT//2]
        return [self.TABLE_WIDTH//4, self.TABLE_HEIGHT//2]
    
    
    def calc_distances(self, balls, bullseye_vec):
        distances = []
        for ball in balls:
            ball_vec = coord_to_vec(ball)
            dist = np.linalg.norm(ball_vec - bullseye_vec)
            distances.append(dist)
        distances.sort()
        return distances
     
        
    def get_round_results(self, coords):
        _, _, solids, striped, _ = split_by_type(coords)
        
        bullseye_vec = np.array(self.bullseye_center)
            
        p1_distances = self.calc_distances(solids, bullseye_vec)
        p2_distances = self.calc_distances(striped, bullseye_vec)
        
        p1_best = p1_distances[0] if p1_distances else float('inf')
        p2_best = p2_distances[0] if p2_distances else float('inf')
        
        points_won = 0
        round_winner = None

        summary_parts = []
        
        if p1_best < p2_best:
            round_winner = "player1"
            for d in p1_distances:
                if d < p2_best: points_won += 1
                else: break
            self.player_scores['player1'] += points_won
            summary_parts.append(f"{self.player1['name']} wins round {self.current_round}/{self.rounds} with {points_won} points")
        elif p2_best < p1_best:
            round_winner = "player2"
            for d in p2_distances:
                if d < p1_best: points_won += 1
                else: break
            self.player_scores['player2'] += points_won
            summary_parts.append(f"{self.player2['name']} wins round {self.current_round}/{self.rounds} with {points_won} points")
        else:
            round_winner = "draw"
            summary_parts.append(f"Round {self.current_round}/{self.rounds} ends in a draw")
            
        p1_penalty, p2_penalty = 0, 0
        if self.negative_points:
            p1_penalty = max(0, self.plays_per_round - len(solids))
            p2_penalty = max(0, self.plays_per_round - len(striped))
            self.player_scores['player1'] -= p1_penalty
            self.player_scores['player2'] -= p2_penalty
            summary_parts.append(f"\nPenalty points: {self.player1['name']}: {p1_penalty}, {self.player2['name']}: {p2_penalty}")
            
        return {
            "winner": round_winner,
            "points": points_won,
            "round_summary": " ".join(summary_parts)
        }
     
        
    def get_standings(self):
        return f"{self.player1['name']}: {self.player_scores['player1']}, {self.player2['name']}: {self.player_scores['player2']}"
        
    
    def index_args(self):
        return {
            "title": "Curling2",
            "description": "Play Curling2!",
            "player_names": self.player_names,
            "team_names": self.team_names,
            "js_vars": {
                "rounds": self.rounds,
                "plays_per_round": self.plays_per_round
            }
        }
    
        
    def get_history_data(self, *args, sort_result = True):
        df = self.saved_history
        if df is None or df.empty:
            return []
        
        all_data = []
        for column_name in args:
            if column_name in df.columns:
                values = (df[column_name].dropna().tolist())
                all_data.extend([str(v) for v in values if str(v).strip()])
        if not all_data:
            return []
        if sort_result:
            data_counts = Counter(all_data)
            return [data for data, count in data_counts.most_common()]
        
        return all_data
        