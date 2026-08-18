from collections import Counter
from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class Curling(GameMode):
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

    DEFAULT_SETTINGS = {
        "plays_per_round": 3,
        "rounds": 1,
        "game_mode": "classic",
        "negative_points": True,
        "submit_only_last_turn": True,
        "player1_name": "",
        "player1_team": "",
        "player2_name": "",
        "player2_team": "",
    }


    def __init__(self, settings=None):
        self.__file__ = __file__
        self.gamemode_name = "Curling"
        self.state = "init"

        self.SETTINGS = dict(self.DEFAULT_SETTINGS)
        self.apply_settings(settings or {})

        self.current_round = 1
        self.current_play_in_round = 0
        self.player_scores = { "player1": 0, "player2": 0}
        self.current_round_score = {
            "round_summary": "round_summary loading",
            "winner": None,
            "points": 0
        }
        
        self.last_round_coords = {}
        self.last_scoring_balls = []

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
                lambda: self.get_play_image_definition((self.current_round_score['round_summary'] + "\nStandings: " + self.get_standings())),
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


    @staticmethod
    def safe_int(value, default, lo=None, hi=None):
        try:
            result = int(value)
        except (TypeError, ValueError):
            result = default
        if lo is not None:
            result = max(lo, result)
        if hi is not None:
            result = min(hi, result)
        return result


    @staticmethod
    def safe_bool(value, default):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() == "true"


    def settings_snapshot(self, values):
        values = values or {}
        return {
            "game_mode": values.get("game_mode") or self.SETTINGS.get("game_mode"),
            "rounds": self.safe_int(values.get("rounds"), self.SETTINGS.get("rounds"), 1, 10),
            "plays_per_round": self.safe_int(values.get("plays_per_round"), self.SETTINGS.get("plays_per_round"), 1, 7),
            "negative_points": self.safe_bool(values.get("negative_points"), self.SETTINGS.get("negative_points")),
            "submit_only_last_turn": self.safe_bool(values.get("submit_only_last_turn"), self.SETTINGS.get("submit_only_last_turn")),
            "player1_name": (values.get("player1") or "").strip(),
            "player1_team": (values.get("team1") or "").strip(),
            "player2_name": (values.get("player2") or "").strip(),
            "player2_team": (values.get("team2") or "").strip(),
        }


    def setup_game(self, inp):
        print("INP CURLING GAME:", inp)
        self.apply_settings(inp)

        self.bullseye_center = self.get_bullseye_position()

        p1_name = self.SETTINGS["player1_name"]
        p2_name = self.SETTINGS["player2_name"]
        p1_team = self.SETTINGS["player1_team"]
        p2_team = self.SETTINGS["player2_team"]

        self.player1 = {
            "name": p1_name if p1_name else "Player 1",
            "team": p1_team
        }
        self.player2 = {
            "name": p2_name if p2_name else "Player 2",
            "team": p2_team
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
        self.last_round_coords = {}
        self.last_scoring_balls = []

        return "start", {}, {"message": f"Game started! \n{self.current_player['name']}'s turn. (full)"}


    def play_turn(self, inp):
        coords = inp["coordinates"]

        if self.submit_only_last_turn: 
            self.current_round_score = self.get_round_results(coords)
            self.message = "Hello World :)"
            self.update_history()

            return "finish_round", {}, {"message": f"{self.current_round_score['round_summary']}\n{self.current_round_score['ball_summary']}"}

        self.current_play_in_round += 1

        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        if self.current_play_in_round >= self.plays_per_round*2:
            self.current_round_score = self.get_round_results(coords)
            self.update_history()
            return "finish_round", {}, {"message": f"{self.current_round_score['round_summary']}\n{self.current_round_score['ball_summary']}"}
        else:
            return "next_turn", {}, {"message": f"{self.current_player['name']}'s turn. \n({'full' if self.current_player == self.player1 else 'striped'})"}


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

        if self.current_round > self.rounds or inp.get("clicked_on") == "End Game":
            return "end_game", {}, {"message": msg + " " + self.get_standings(), "notification": "Match Finished", "hist-package": self.HISTORY}
        else:
            return "next_round", {}, {"message": msg}


    def finish_game(self, inp):
        return "init", {}, {"message": f"Game over"}


    def get_play_image_definition(self, round_finish_text = None):

        if self.submit_only_last_turn:
            round_text = f"Round: {self.current_round}/{self.rounds} | Start: {self.current_player['name']} ({'full' if self.current_player == self.player1 else 'striped'})\nSubmit after each player had {self.plays_per_round} shots."
        else:
            round_text = f"Round: {self.current_round}/{self.rounds} | play: {self.current_play_in_round + 1}/{self.plays_per_round*2}\nTurn: {self.current_player['name']} ({'full' if self.current_player == self.player1 else 'striped'})"

        base = [
            {
                "type": "text", 
                "text": round_finish_text or round_text
            },
            {
                "type": "bullseye", 
                "center": self.bullseye_center,
                "radius": 200
            },
            {
                "type": "balls",
                "coords": self.last_round_coords if round_finish_text else {},
                "ref": "starting_point"
            }
        ]

        if self.mode == "center" and round_finish_text == None:
            base.append(
                {
                    "type": "line",
                    "ref": "start_line_left",
                    "c1": {"x": self.LINE_LEFT_X, "y": 0 + 0.2 * self.TABLE_HEIGHT},
                    "c2": {"x": self.LINE_LEFT_X, "y": self.TABLE_HEIGHT * 0.8},
                    "color": "white" if self.current_player == self.player1 or self.submit_only_last_turn else "black",
                    "width": 5
            })

            base.append(
                {
                    "type": "line",
                    "ref": "start_line_right",
                    "c1": {"x": self.LINE_RIGHT_X, "y": 0 + 0.2 * self.TABLE_HEIGHT},
                    "c2": {"x": self.LINE_RIGHT_X, "y": self.TABLE_HEIGHT * 0.8},
                    "color": "white" if self.current_player == self.player2 or self.submit_only_last_turn else "black",
                    "width": 5
            })
        elif round_finish_text == None:
            base.append({
                "type": "line",
                "ref": "start_line_right",
                "c1": {"x": self.LINE_RIGHT_X, "y": 0 + 0.2 * self.TABLE_HEIGHT},
                "c2": {"x": self.LINE_RIGHT_X, "y": self.TABLE_HEIGHT * 0.8},
                "color": "white",
                "width": 5
            })
            
        for ball in self.last_scoring_balls:
            base.append(
                {
                    "type": "line",
                    "ref": f"scoring_ball_{ball}",
                    "c1": {"x": ball["x"], "y": ball["y"]},
                    "c2": {"x": self.bullseye_center[0], "y": self.bullseye_center[1]},
                    "color": "white",
                    "width": 3
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
        ball_distances = []
        for ball in balls:
            ball_vec = coord_to_vec(ball)
            dist = np.linalg.norm(ball_vec - bullseye_vec)
            ball_distances.append((ball, dist))
        ball_distances.sort(key=lambda item: item[1])
        return ball_distances
    
        
    def get_round_results(self, coords):
        _, _, solids, striped, _ = split_by_type(coords)

        bullseye_vec = np.array(self.bullseye_center)

        p1_distances = self.calc_distances(solids, bullseye_vec)
        p2_distances = self.calc_distances(striped, bullseye_vec)

        p1_best = p1_distances[0][1] if p1_distances else float('inf')
        p2_best = p2_distances[0][1] if p2_distances else float('inf')

        points_won = 0
        round_winner = None
        scoring_balls = []
        next_closest = None

        summary_parts = []
        ball_summary_parts = []
        
        if p1_best < p2_best:
            winner_key, winner_name, winner_dists, loser_best = "player1", self.player1["name"], p1_distances, p2_best
            next_closest = p2_distances[0] if p2_distances else None
            round_winner = "player1"
        elif p2_best < p1_best:
            winner_key, winner_name, winner_dists, loser_best = "player2", self.player2["name"], p2_distances, p1_best
            next_closest = p1_distances[0] if p1_distances else None
            round_winner = "player2"
        else:
            round_winner = "draw"
            summary_parts.append(f"Round {self.current_round}/{self.rounds}: draw")
            
        if round_winner != "draw":
            points_won = sum(1 for _, d in winner_dists if d < loser_best)
            scoring_balls = winner_dists[:points_won]
            
            self.player_scores[winner_key] += points_won
            #summary_parts.append(f"{winner_name} wins round {self.current_round}/{self.rounds} with {points_won} points")
            summary_parts.append(f"Round {self.current_round}/{self.rounds}: {winner_name} +{points_won} points")
        
        if scoring_balls:
            balls_text = "\n".join(
                f"ball {ball['name']} at {d:.0f} mm"
                for ball, d in scoring_balls
            )
            ball_summary_parts.append(f"Scoring balls:\n{balls_text}")
            
        if next_closest:
            ball, d = next_closest
            ball_summary_parts.append(f"\nThe next closest ball is {ball['name']} at {d:.0f}mm")
        
        p1_penalty, p2_penalty = 0, 0
        if self.negative_points:
            p1_penalty = max(0, self.plays_per_round - len(solids))
            p2_penalty = max(0, self.plays_per_round - len(striped))
            self.player_scores['player1'] -= p1_penalty
            self.player_scores['player2'] -= p2_penalty
            penalties = []
            if p1_penalty:
                penalties.append(f"{self.player1['name']} -{p1_penalty}")
            if p2_penalty:
                penalties.append(f"{self.player2['name']} -{p2_penalty}")
            if penalties:
                summary_parts.append(f" | Penalty: {', '.join(penalties)}")
            #summary_parts.append(f" | Penalty points: {self.player1['name']}: {p1_penalty}, {self.player2['name']}: {p2_penalty}")

        self.last_round_coords = coords
        self.last_scoring_balls = [ball for ball, d in scoring_balls]
        
        return {
            "winner": round_winner,
            "points": points_won,
            "round_summary": " ".join(summary_parts),
            "ball_summary": " ".join(ball_summary_parts)
        }


    def get_standings(self):
        return f"{self.player1['name']}: {self.player_scores['player1']} <> {self.player2['name']}: {self.player_scores['player2']}"


    def index_args(self):
        return {
            "title": "Curling",
            "description": "Play Curling!",
            "player_names": self.player_names,
            "team_names": self.team_names,
            "js_vars": {
                "rounds": self.rounds,
                "plays_per_round": self.plays_per_round
            },
            "current_settings": {
                "game_mode": self.mode,
                "rounds": self.rounds,
                "plays_per_round": self.plays_per_round,
                "negative_points": bool(self.negative_points),
                "submit_only_last_turn": bool(self.submit_only_last_turn),
                "player1": self.SETTINGS.get("player1_name", ""),
                "team1": self.SETTINGS.get("player1_team", ""),
                "player2": self.SETTINGS.get("player2_name", ""),
                "team2": self.SETTINGS.get("player2_team", ""),
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


    def settings(self, inp):
        self.apply_settings(inp.get("settings") or {})
        return {}, {"message": "Settings saved."}


    def apply_settings(self, settings_dict):
        self.SETTINGS = {**self.SETTINGS, **self.settings_snapshot(settings_dict)}
        
        self.mode = self.SETTINGS["game_mode"]
        self.rounds = self.SETTINGS["rounds"]
        self.plays_per_round = self.SETTINGS["plays_per_round"]
        self.negative_points = self.SETTINGS["negative_points"]
        self.submit_only_last_turn = self.SETTINGS["submit_only_last_turn"]