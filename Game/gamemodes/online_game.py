from .common_utils import *
from .api_utils import *
from .GameMode import GameMode
from ..GameImage import GameImage

class OnlineGame(GameMode):
    """ Play a game of billiards online against another table in the network! 



    Args:
        env (dict): loaded and parsed .env file with configuration and authentication for the global API interface
    """

    def __init__(self, env=None, settings=None):
        self.__file__ = __file__
        self.gamemode_name = "Online Game"
        self.name = ""
        self.state = "init"
        self.score = 0
        #self.history_file
        self.game_state = "unknown" #: this tracks the state of the current game, kept up to date with the API

        if not env is None:
            self.SETTINGS = {"env": env}
        if not settings is None:
            self.SETTINGS = settings
            env = settings["env"]

        self.API = API(env)

        self.gameimage = GameImage()

        self.TREE = {
            "init": [
                self.request_game,
                {"wait": "wait", "play": "play", "reset": "init", "init": "init"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Start an Online Game"
                    },
                    {
                        "type": "central_image",
                        "img": "isem-logo-big"
                    }
                ],
                ["Request Game", {
                    "type": "text",
                    "name": "player",
                    "placeholder": "Player Name"
                }, {
                    "type": "text",
                    "name": "team",
                    "placeholder": "Team"
                }, {
                    "type": "selector",
                    "name": "opponent_table",
                    "options": ""
                }
                ]
            ],
            "wait": [ # 
                self.handle_long_poll,
                {"continue": "play", "wait": "wait", "finished": "finished"},
                lambda: self.gameimage.definition,
                [None] # this is hardcoded on the template online_game.html

            ],
            "play": [
                self.evaluate_play,
                {"finished": "finished", "continue": "play", "wait": "wait"},
                lambda: self.gameimage.definition,
                [None] # this is hardcoded on the template online_game.html
            ]
        }
        GameMode.__init__(self)

    def request_game(self, inp):
        """ Send a request to the API to open the game or (if selected) look for open games """
        print("REQUEST GAME:", inp)
        # pipe to global server
        res = self.API.start_game(inp["name"], inp["team"], inp["password"], inp["tooltips"], inp["opponent_table"])
        self.game_state = res["state"]
        match res["state"]:
            case "error": # defined in api_utils.py
                message = "Could not authenticate player"
                return "init", {"gameimage-updates": [{"type": "text", "text": message}]}, {"message": message}
            case "shootout": 
                # if this results in a found game (state = shootout), instantly play the shootout
                self.gameimage.definition = res["imgd"]
                return "play", {}, {"message": res["message"]}
            case "invite":
                self.gameimage.definition = res["imgd"]
                return "wait", {}, {"message": res["message"], "notification": "Waiting for the other player...", "emit": {"start_long_poll": {}}}
        
        return "init", {}, {} # FORWARD THE lpt TO THE CLIENT: otherwise, long polls wont succeed

    def handle_long_poll(self, inp):
        """This method gets called by run_long_poll from long_poll_online.js. Check if there is a new state available on the server. If that is the case and its this players turn, return to play mode. Alternatively, display the new gameimage and messages.

        Args:
            inp (_type_): _description_
        """
        print("HANDLE LONG POLL:", inp)
        if "clicked_on" in inp.keys() and inp["clicked_on"] == "Cancel":

            status = self.API.abort_game()["http"]
            print("GAME HAS BEEN ABORTED BY THIS CLIENT WITH STATUS CODE", status)
            self.message = "Game aborted"
            return "finished", {}, {"message": self.message, "emit": {"stop_long_poll": {}}}

        is_new, res = self.API.check_state()
        if not is_new:
            return "wait", {}, {"resume": False}
        else:
            if len(res.keys()) == 0:
                # when the game is missing in the cache
                return "finished", {}, {"message": "The game was aborted.", "resume": True}
            self.gameimage.definition = res["imgd"]
            self.game_state = res["state"]
            if res["state"] == "finished":
                self.message = "You won!" if res["play"] else "You lost :(" # the winner is set as the active player at the end
                return "finished", {}, {"message": res["message"], "resume": True}

            if not res["play"] and res["state"] not in ["shootout", "finished"]:
                return "wait", {}, {"message": res["message"], "resume": False}
            else:
                return "continue", {}, {"message": res["message"], "resume": True}

    def evaluate_play(self, inp):
        """ Sends the coordinates to the game and handles the decision """
        print("NOW evaluating play. game_state=", self.game_state)
        if "shootout" in self.game_state:
            res = self.API.evaluate_break(inp["coordinates"])
        else:
            res = self.API.evaluate_play(inp["coordinates"])
        print(f"RESPONSE FROM evaluate_play (with state={self.game_state})", res)
        
        # handle results
        self.gameimage.definition = res["imgd"]
        self.game_state = res["state"]
        if "play" in res["state"] or "break" in res["state"]:
            if res["play"]:
                return "continue", {}, {"message": res["message"]}
            else:
                return "wait", {}, {"message": res["message"], "emit": {"start_long_poll": {}}}
        if "shootout" in res["state"]:
            return "wait", {}, {"message": "Waiting for the opponent to play", "emit": {"start_long_poll": {}}}
        if "finished" == res["state"]:
            self.message = "You won!" if res["play"] else "You lost :(" # the winner is set as the active player at the end
            return "finished", {}, {"message": res["message"]}
        raise ValueError(f"Some error appeared in the API, inp & response dump: {inp} \n\n {res}")


    def index_args(self):
        # check if available first (this feature should exist on main branch?)
        try:
            tables = self.API.get_all_tables() # a pd.DataFrame with id, name, location
            table_list = tables[["id", "name", "location"]].values.tolist() # pass in dict as table_list

            teams = self.API.get_all_teams()
            print("TEAMS", teams)
            team_list = teams.values.tolist()
        except Exception as e:
            #print("EXCEPTION ENCOUNTERED IN OnlineGame.index_args:")
            #raise e
            return {"error": "Can't get data from the API. Has this server internet access and is the API running? 503 Service Unavailable", "error_status": 503}

        return {
            "table_list": table_list,
            "team_list": team_list,
            "title": "Online Billard@ISEM"
        }

    def apply_gi(res):
        self.gameimage.definition = res["imgd"]

    def history(self, add=None):
        # overwriting GameMode.history
        # just show the website
        leaderboard = self.API.get_leaderboard()
        teams = leaderboard[["Team", "Elo"]].groupby("Team").mean()
        teams["Team"] = teams.index

        out = {
            "single_table": leaderboard.values.tolist(),
            "single_columns": ["Name", "Elo", "Team", "Home"],
            "team_table": teams.values.tolist()
        }
        return out

    def reset(self, keep_settings=True, inplace=False, **kwargs):
        if inplace:
            self.__init__(settings=self.SETTINGS, **kwargs)
            print("Reset this object. New state:", self.state)
            return "reset", {}, {"click": "#init button.collapsible"}
            
        return self.__init__(settings=self.SETTINGS, **kwargs)
