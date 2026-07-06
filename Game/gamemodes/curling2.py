from .GameMode import GameMode
from .common_utils import *

import random
import numpy as np

class Curling(GameMode):
    """Two players compete to have their final ball as close as possible to the white ball.

    """

    def __init__(self, settings=None):
        self.__file__ = __file__
        self.gamemode_name = "Curling"
        self.state = "init"
        self.score = 0

        # details on the game itself
        # 5 v 5 shots
        self.remaining_shots = 10
        self.order = ["solid", "striped"]
        self.last_white = {
            "name": "white",
            "y": 1115//2, 
            "x": 2230//4
        } # left center

        self.HISTORY = {
            "player1_team": "",
            "player1_name": "",
            "player2_team": "",
            "player2_name": "",
            "winner": 0,
            "distance1": 10000,
            "distance2": 10000
        }


        self.TREE = {
            "init": [
                self.start_game,
                {"start_game": "play_rounds", "reset": "init"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Curling: Enter your names!"
                    },
                    {
                        "type": "central_image",
                        "img": "isem-logo-big"
                    },
                    {
                        "type": "balls",
                        "coords": {"white": self.last_white}
                    }
                ],
                [None]
            ],
            "play_rounds": [
                self.display_positions,
                {"again": "play_rounds", "finished": "finished"},
                lambda: self.img_definition + [{
                        "type": "balls",
                        "coords": {"dummy": {            
                            "y": 1115//2,
                            "x": 5*2230//6,
                            "name": "dummy"
                        }},
                        "ref": "starting_point"
                }],
                [None]
            ],
            "finished": [
                lambda x: self.reset(inplace=True),
                {"False": "init"}, # not really important -> reset does that anyway. self.reset MUST NOT return True, as this would immediately skip the init step, which "proceeds" to the next step if the return is True (evaluation of return after reset...)
                lambda: [
                    {
                        "type": "text",
                        "text": f"{self.gamemode_name}: {self.message}"
                    },
                ] + self.img_definition,
                [None, {
                    "type": "button",
                    "name": "next_try",
                    "id": "next_try",
                    "placeholder": "Next Try",
                    "value": "Next Try",
                    "class": "submit-step"
                }]
            ]

        }
        GameMode.__init__(self)


    def start_game(self, inp):
        # have the player enter their names and teams.
        # randomly select who starts out.
        # player one always has the solid, p2 striped balls
        self.HISTORY |= {
            "player1_team": inp["p1team"],
            "player1_name": inp["p1name"],
            "player2_team": inp["p2team"],
            "player2_name": inp["p2name"],
        }

        self.id_name = [
            inp["p1name"] + " (" + inp["p1team"] + ")",
            inp["p2name"] + " (" + inp["p2team"] + ")"
        ]

        self.current_player = random.randint(0, 1)
        self.message = f"{self.id_name[self.current_player]} may play"

        self.img_definition = [
            {
                "type": "text",
                "text": self.message
            },
            {
                "type": "balls",
                "coords": [self.last_white]
            }
        ]

        return "start_game", {}, {"message": self.message}

    def display_positions(self, inp):
        # show which team currently leads
        coords = inp["coordinates"]
        white, _, solids, striped, _ = split_by_type(coords)

        if white is None:
            print("White ball not found, resetting")
            white = self.last_white
        else:
            self.last_white = white

        # calculate all distances
        solids_distances = [metric_distance(ball, white).astype(int) for ball in solids]
        striped_distances = [metric_distance(ball, white).astype(int) for ball in striped]

        min_solids = min(solids_distances) if len(solids_distances) > 0 else 3333
        min_striped = min(striped_distances) if len(striped_distances) > 0 else 3333

        if min_solids < min_striped:
            # solids is leading
            leading_player = self.id_name[0]
            
        else:
            # striped is leading
            leading_player = self.id_name[1]



        # always change the player
        self.current_player = (self.current_player + 1)%2
        
        # player name formatting: UPPER the current player
        players = self.id_name.copy()
        players[self.current_player] = players[self.current_player].upper() 
        self.message = f"{players[0]} {min_solids}mm : {min_striped}mm {players[1]}"

        # modify the gameimage
        # regroup the balls by anonymizing them
        balls = (
            [x | {"name": "correct"} for x in solids] +
            [x | {"name": "incorrect"} for x in striped]
            + [white]
        )
        self.img_definition = [
            {"type": "text", "text": self.message},
            {"type": "balls", "coords": balls}
        ]

        self.remaining_shots -= 1
        if self.remaining_shots == 0:
            self.HISTORY |= {
                "winner": leading_player,
                "distance1": min_solids,
                "distance2": min_striped
            }

            self.img_definition = [{"type": "balls", "coords": balls}]

            combined = [min_solids, min_striped]
            self.message = f"{leading_player} won with {min(combined)}mm vs {max(combined)}mm!"
            return "finished", {}, {"message": self.message, "hist-package": self.HISTORY}
        
        return "again", {}, {"message": self.message}

    def index_args(self):
        return {}

    def history(self, add=None):
        print("HISTORY", add)
        history = self.get_history()
        print("HISTORY", history)

        if add is not None:
            history = pd.concat((history, pd.DataFrame(add, index=[0])), ignore_index=True)
            print("HISTORY", history)
            self.save_history(history)

        winners = history["winner"].value_counts().to_dict().items()
        single_table = []
        for k, v in winners:
            split = k.split("(")
            name = split[0]
            team = split[1][:-1]

            single_table.append([
                name, v, team
            ])
        single_table_columns = ["Name", "Won Games", "Team"]
        df_team_table = pd.DataFrame(single_table, columns=single_table_columns)

        team_table = []
        for team, df in df_team_table.groupby("Team"):
            team_table.append([
                len(df), team
            ])

        return {
            "single_table": single_table,
            "single_columns": single_table_columns,
            "team_table": team_table
        }