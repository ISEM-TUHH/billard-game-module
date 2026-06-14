import numpy as np

from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class Curling2(GameMode):

    """ The goal is to play the own team balls closest to the target for maximum points (similar to curling)
    """
    # Constants
    Table_Width = 2230
    Table_Height = 1115
    Line_Left_X = 300
    Line_Right_X = 1930
    Bullseye_Radius = 200
    
    
    def __init__(self, rounds=2, plays_per_round=2, mode="classic"):
        self.__file__ = __file__
        self.gamemode_name = "Curling2"
        self.state = "init"
        
        self.plays_per_round = plays_per_round
        self.rounds = rounds
        self.mode = mode
        
        self.current_round = 1
        self.current_play_in_round = 0
        self.score = { "player1": 0, "player2": 0}
        self.current_round_score = {
            "round_summary": "round_summary loading",
            "winner": None,
            "points": 0
        }
 
        self.current_player = None
        self.player1 = None
        self.player2 = None
        
        self.round_ball_distances = {"player1": [], "player2": []}
        
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
        
        
    def get_play_image_definition(self):
        base = [
            {
                "type": "text", 
                "text": f"Round {self.current_round}/{self.rounds} | play {self.current_play_in_round + 1}/{self.plays_per_round*2} | Turn: {self.current_player['name']}"
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
                    "c1": {"x": 300, "y": 0},
                    "c2": {"x": 300, "y": 1115},
                    "color": "white" if self.current_player == self.player1 else "black",
                    "width": 5
                })
            
            base.append(
                {
                    "type": "line",
                    "ref": "start_line_right",
                    "c1": {"x": 1930, "y": 0},
                    "c2": {"x": 1930, "y": 1115},
                    "color": "white" if self.current_player == self.player2 else "black",
                    "width": 5
                }
            )
        else:
            base.append({
                "type": "line",
                "ref": "start_line_right",
                "c1": {"x": 1930, "y": 0},
                "c2": {"x": 1930, "y": 1115},
                "color": "white",
                "width": 5
            })
        
        return base
    
    def get_bullseye_position(self):
        if self.mode == "center":
            return [self.Table_Width//2, self.Table_Height//2]
        return [self.Table_Width//4, self.Table_Height//2]
        
    def get_round_results(self, coords):
        _, _, solids, striped, _ = split_by_type(coords)
        
        bullseye_vec = np.array(self.bullseye_center)
        
        p1_distances = []
        for ball in solids:
            ball_vec = coord_to_vec(ball)
            dist = np.linalg.norm(ball_vec - bullseye_vec)
            p1_distances.append(dist)
            
        p2_distances = []
        for ball in striped:
            ball_vec = coord_to_vec(ball)
            dist = np.linalg.norm(ball_vec - bullseye_vec)
            p2_distances.append(dist)
            
        p1_distances.sort()
        p2_distances.sort()
        
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
            self.score['player1'] += points_won
            summary_parts.append(f"{self.player1['name']} wins round {self.current_round}/{self.rounds} with {points_won} points")
        elif p2_best < p1_best:
            round_winner = "player2"
            for d in p2_distances:
                if d < p1_best: points_won += 1
                else: break
            self.score['player2'] += points_won
            summary_parts.append(f"{self.player2['name']} wins round {self.current_round}/{self.rounds} with {points_won} points")
        else:
            round_winner = "draw"
            summary_parts.append(f"Round {self.current_round}/{self.rounds} ends in a draw")
            
        p1_penalty, p2_penalty = 0, 0
        if self.negative_points:
            p1_penalty = max(0, self.plays_per_round - len(solids))
            p2_penalty = max(0, self.plays_per_round - len(striped))
            self.score['player1'] -= p1_penalty
            self.score['player2'] -= p2_penalty
            summary_parts.append(f"\nPenalty points: {self.player1['name']}: {p1_penalty} - {self.player2['name']}: {p2_penalty}")
            
        return {
            "winner": round_winner,
            "points": points_won,
            "round_summary": " ".join(summary_parts)
        }
        
    def get_standings(self):
        return f"{self.player1['name']}: {self.score['player1']}, {self.player2['name']}: {self.score['player2']}"
        
    
    def setup_game(self, inp):
        print("INP CURLING GAME:", inp)
        
        self.mode = inp["game_mode"]
        self.bullseye_center = self.get_bullseye_position()
        self.negative_points = inp['negative_points']
        self.plays_per_round = int(inp['plays_per_round'])
        self.rounds = int(inp['rounds'])
        p1_name = inp['player1']
        p2_name = inp['player2']
                
        self.player1 = {
            "name": p1_name if p1_name else "Player 1"
        }
        self.player2 = {
            "name": p2_name if p2_name else "Player 2"
        }
        
        self.current_round = 1
        self.current_play_in_round = 0
        self.current_player = self.player1
        self.score = {"player1": 0, "player2": 0}
        self.round_ball_distances = {"player1": [], "player2": []}
        
        return "start", {}, {"message": f"Game startet! {self.current_player['name']}'s turn. (full)"}

 
    def play_turn(self, inp):
        coords = inp.get("coordinates", {})
        
        # if not coords and not self.negative_points: return "next_turn", {}, {"message": "No ball detected. Shoot again!"}         
    
        self.current_play_in_round += 1
            
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        if self.current_play_in_round >= self.plays_per_round*2:
            self.current_round_score = self.get_round_results(coords)
            return "finish_round", {}, {"message": f"Round {self.current_round} finished!"}
        else:
            return "next_turn", {}, {"message": f"{self.current_player['name']}'s turn. ({"full" if self.current_player == self.player1 else "striped"})"}
    
    
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
            return "end_game", {}, {"message": msg, "notification": "Match Finished"}
        else:
            return "next_round", {}, {"message": msg}
        
    def finish_game(self, inp):
        return "init", {}, {"message": f"Game over"}
    
    def index_args(self):
        return {
            "title": "Curling2",
            "description": "Play Curling2!",
            "js_vars": {}
        }