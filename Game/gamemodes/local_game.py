from .GameMode import GameMode
from .GameModel import Game
from .api_utils import API
from .common_utils import *
from ..GameImage import GameImage

class LocalGame(GameMode):
    """ A local game that essentially simulates both sides of a online game """

    def __init__(self, env=None, settings=None):
        self.__file__ = __file__
        self.gamemode_name = "Local Game"

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

        self.player1 = {
            "name": inp["player1"],
            "team": inp["team1"]
        }
        self.player2 = {
            "name": inp["player2"],
            "team": inp["team2"]
        }

        self.game = Game(self.player1, self.player2)
        self.game.generate_shootout() # game.break_points will be displayed in the shootout stage

        return "start_shootout", {}, {"message": "Game started"}

    def shootout(self, inp):
        """ This gets called to two times (once per player): decides who will start """
        self.break_distances.append(inp["coordinates"]) # distances get calculated by the game object
        if len(self.break_distances) == 2:
            rdict = self.game.evaluate_break(self.break_distances[0], self.break_distances[1])
            return "break", {}, {"message": rdict["winner"]["name"] + " won the shootout"}
        else:
            return "again", {"gameimage-updates": [{"type": "text", "text": self.player2["name"] + " turn for shootout"}]}, {}

    def play(self, inp):
        """ After the break is decided, enter the play loop """

        token = self.game.active_player["token"]
        message, img_definition, _ = self.game.evaluate_play(token, inp["coordinates"])

        print(message)
        if "[END]" in message:
            # the game is over
            return "end", {"gameimage-updates": img_definition}, {"message": self.game.active_player["name"] + " won the game", "notification": message}

        return "continue", {"gameimage-updates": img_definition}, {"message": self.game.active_player["name"] + " can play"}


    def index_args(self):
        out = {
            "title": "Local Billiard@ISEM",
            "teams": ["ISEM", "ITPE"]
        }
        return out