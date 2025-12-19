from dataclasses import dataclass, asdict
import requests
import json
import os

@dataclass
class ApiAuth:
    """ Provides a common data interface for transfering authentication data """
    TID: str
    TAUTH: str
    ADDRESS: str # only because of **kwargs
    PORT: str # only because of **kwargs
    PID: str = ""
    PAUTH: str = ""
    GID: str = ""

    def json(self):
        """ Return all set fields (= not default value) as a dict """
        j = asdict(self)
        out = j.copy()
        defaults = asdict(ApiAuth)
        for k, v in j.items():
            if v == defaults[k]:
                del out[k]
        out["TID1"] = out["TID"]
        del out["TID"]
        return out

class API:
    """ Provides a common interface for communicating with the global API """

    def __init__(self, env):
        self.AUTH = ApiAuth(**env)
        self.address = env["ADDRESS"]
        self.port = env["PORT"]

    def post(self, endpoint, data):
        send_data = data | self.AUTH.json()
        url = os.path.join(f"https://{self.address}:{self.port}", endpoint)
        try:
            res = requests.post(url, json=send_data)
        except:
            print(f"Cant establish connection or refused. Tried posting to {url}")
            raise ConnectionError(f"Cant establish connection or refused. Tried posting to {url}")



        return res.json()

    def get_all_tables(self):
        """ Load all table names/locations/ID as a list from the API """
        try:
            tables = self.post("get_tables", {})
        except Exception as e:
            tables = [{
                "name": "Billard@ISEM",
                "location": "ISEM, TUHH, Hamburg",
                "id": 123454321
            }]

    def get_players_from_team(self, table_id):
        """ Load all players that are on a certain table """

    def add_player(self, name, team):
        """ Add a player of a certain team. Automatically adds id, origin_table """


    #%% Game methods

    def start_game(self, player, team, opponent_table=None):
        """ Posts the player and team as well as the opponent table (if existing). If it is not set, just look """


    def evaluate_break(self, coordinates):
        """ Send the coordinates to the server and return the decision ("won" / "lost") """

    def evaluate_play(self, coordinates):
        """ Send the coordinates to the server and return the decision ("go_on" / "change" / "lost" / "won") """