from .GameMode import GameMode
from .GameModel import Game
from .api_utils import API
from .common_utils import *
from ..GameImage import GameImage
from ..Elo import Elo

class LocalGame(GameMode):
    """ A local game that essentially simulates both sides of a online game """

    def __init__(self, env=None, settings=None):
        self.__file__ = __file__
        self.gamemode_name = "Local Game"
        self.HISTORY_FORMAT = ".json" # default would be .csv, but here .json is more reasonable

        self.player1 = None
        self.player2 = None
        self.break_distances = []

        # this is important for GameMode.reset()
        if not env is None:
            self.SETTINGS = {"env": env}
        if not settings is None:
            self.SETTINGS = settings

        self.api = API(self.SETTINGS["env"])
        self.gameimage = GameImage()

        self.TREE = {
            "init": [
                self.setup_shootout,
                {"start_shootout": "shootout"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Enter your names and teams"
                    },
                    {"type": "central_image", "img": "isem-logo-big"}
                ],
                ["Send"] # inputs are defined manually on the page
            ],
            "shootout": [
                self.shootout,
                {"again": "shootout", "break": "play"},
                lambda: [
                    {
                        "type": "text", "text": f"{self.player1['name']} turn for shootout"
                    },{
                        "type": "balls", "coords": self.game.break_points
                    }
                ],
                ["Hand in"]
            ],
            "play": [
                self.play,
                {"continue": "play", "end": "finished"},
                lambda: [{
                    "type": "break",
                    "draw_ball": True
                },{
                    "type": "text", "text": self.game.active_player['name'] + " may break"
                }],
                ["Hand in"]
            ]
        }

        GameMode.__init__(self)


    def setup_shootout(self, inp):
        """ Upon sending the player and team names, save the game config and lookup the player """
        print("INP LOCAL GAME:", inp)

        self.player1 = {
            "name": inp["player1"],
            "team": inp["team1"],
            "tooltips": inp["tooltips1"]
        }
        self.player2 = {
            "name": inp["player2"],
            "team": inp["team2"],
            "tooltips": inp["tooltips2"]
        }

        self.game = Game(self.player1, self.player2)
        self.game.generate_shootout() # game.break_points will be displayed in the shootout stage

        return "start_shootout", {}, {"message": "Game started", "disable": [".single-player-details"]}

    def shootout(self, inp):
        """ This gets called to two times (once per player): decides who will start """
        self.break_distances.append(inp["coordinates"]) # distances get calculated by the game object
        if len(self.break_distances) == 2:
            rdict = self.game.evaluate_break(self.break_distances[0], self.break_distances[1])
            return "break", {}, {"message": rdict["winner"]["name"] + f" won the shootout: {int(rdict['distance1'])} mm vs. {int(rdict['distance2'])} mm", "log_to": ".results"} # log the message to the .results container
        else:
            return "again", {"gameimage-updates": [{"type": "text", "text": self.player2["name"] + " turn for shootout"}]}, {"message": "Other players turn", "log_to": ".results"}

    def play(self, inp):
        """ After the break is decided, enter the play loop """

        token = self.game.active_player["token"] # the token was designed to allow the game model to determine which player submits a round (useful for integrity in online games)
        message, img_definition, _ = self.game.evaluate_play(token, inp["coordinates"])

        #print(message)
        if "[END]" in message:
            # the game is over
            self.message = self.game.short_message # this gets read by GameMode.TREE["finished"]
            history = self.game.history
            self.save_json_history(history)
            
            self.HISTORY = None # history is handled differently -> not always a new row is added
            self.update_elo() # this also adds previously unregistered players

            return "end", {"gameimage-updates": img_definition, "reset-gameimage": True}, {"message": self.game.active_player["name"] + " won the game", "notification": message}

        return "continue", {"gameimage-updates": img_definition, "reset-gameimage": True}, {"message": self.game.active_player["name"] + " can play"}


    def index_args(self):
        out = {
            "title": "Local Billard@ISEM",
            "teams": ["ISEM", "ITPE"]
        }
        return out


    def update_elo(self):
        """ Loads the history file, looks for the players (based on name/team) or adds them with elo=1000, and then updates them based on the outcome (assumes that the active player won.) """
        all_players = self.get_history()
        winner = self.game.active_player
        loser = self.game.inactive_player

        # check if the winner exists:
        if not ((all_players["player"] == winner["name"]) & (all_players["team"] == winner["team"])).any():
            #print("Winner did not exist previously")
            all_players = pd.concat((all_players, pd.DataFrame([{"player": winner["name"], "team": winner["team"], "score": 1000}])), ignore_index=True)
        # check if the loser exists:
        if not ((all_players["player"] == loser["name"]) & (all_players["team"] == loser["team"])).any():
            #print("Loser did not exist previously")
            all_players = pd.concat((all_players, pd.DataFrame([{"player": loser["name"], "team": loser["team"], "score": 1000}])), ignore_index=True)

        p1index = all_players.index[(all_players["player"] == winner["name"]) & (all_players["team"] == winner["team"])][0]
        p2index = all_players.index[(all_players["player"] == loser["name"]) & (all_players["team"] == loser["team"])][0]

        #print("UPDATE ELO")
        #print(all_players)
        #print(p1index, all_players.loc[p1index, "score"], all_players.index[(all_players["player"] == winner["name"]) & (all_players["team"] == winner["team"])])
        #print(p2index, all_players.loc[p2index, "score"], all_players.index[(all_players["player"] == loser["name"]) & (all_players["team"] == loser["team"])])

        player = [{"elo": all_players.loc[p1index, "score"]}, {"elo": all_players.loc[p2index, "score"]}]
        elo = Elo()
        elo.match(player, winner=0) # per definition, the winner is always the first in the list

        all_players.loc[p1index, "score"] = player[0]["elo"]
        all_players.loc[p2index, "score"] = player[1]["elo"]

        self.save_history(all_players)