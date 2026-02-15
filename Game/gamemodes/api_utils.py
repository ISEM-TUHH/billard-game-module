from dataclasses import dataclass, asdict
import requests
import json
import os
import pandas as pd

@dataclass
class ApiAuth:
    """ Provides a common data interface for transfering authentication data """
    TID: str
    TAUTH: str
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

    def auth(self):
        #print((self.TID, self.TAUTH))
        return (self.TID, self.TAUTH)

class API:
    """ Provides a common interface for communicating with the global API """

    def __init__(self, env):
        self.AUTH = ApiAuth(TID=env["TID"], TAUTH=env["TAUTH"])
        self.address = env["ADDRESS"]
        self.port = env["PORT"]

    def post(self, endpoint, data):
        """Post json data to a certain authenticated endpoint

        Authenticated by the information stored in API.ApiAuth 

        Args:
            endpoint (str): Endpoint of the api like "api/test" or "/api/test"
            data (dict): Data to send to the server. Must be serializable.

        Raises:
            ConnectionError: If the endpoint is not available, raise this error

        Returns:
            dict: Returned json data including ("http": http status code) pair.
        """
        url = f"{self.address}:{self.port}" + os.path.join("", endpoint)
        try:
            res = requests.post(url, json=data, auth=self.AUTH.auth())
        except:
            #print(e)
            print(f"Cant establish connection or refused. Tried posting to {url}")
            raise ConnectionError(f"Cant establish connection or refused. Tried posting to {url}")

        #print("API UTILS POST RESPONSE:", res)
        data = {}
        if res.headers.get('content-type') == 'application/json':
            data = res.json()
        return data | {"http": res.status_code}

    def get(self, endpoint):
        """Get json data from a certain authenticated endpoint

        Authenticated by the information stored in API.ApiAuth 

        Args:
            endpoint (str): Endpoint of the api like "api/test" or "/api/test"

        Raises:
            ConnectionError: If the endpoint is not available, raise this error

        Returns:
            dict: Returned json data including ("http": http status code) pair.
        """
        url = f"{self.address}:{self.port}" + os.path.join("", endpoint)
        try:
            #print("API UTILS GET", url, self.address, self.port)
            res = requests.get(url, auth=self.AUTH.auth())
        except Exception as e:
            print(e)
            print(f"Cant establish connection or refused. Tried posting to {url}")
            raise ConnectionError(f"Cant establish connection or refused. Tried posting to {url}")

        data = {}
        if res.headers.get('content-type') == 'application/json':
            data = res.json()
        return data | {"http": res.status_code}

    def get_all_tables(self):
        """ Load all table names/locations/ID as a list from the API """
        #try:
        tables_res = self.get("/info/get_tables")
        tables = pd.DataFrame(tables_res["tables"])
        #except Exception as e:
        #    tables = [{
        #        "name": "Billard@ISEM",
        #        "location": "TUHH",
        #        "id": 123454321
        #    }]
        return tables

    def get_all_teams(self):
        #try:
        teams_res = self.get("/info/get_teams")
        teams = pd.DataFrame(teams_res["teams"])
        #except Exception as e:
        #    print(e)
        #    teams = [{
        #        "name": "ISEM",
        #        "id": 123454321
        #    }]
        return teams


    def get_players_from_team(self, table_id):
        """ Load all players that are on a certain table """

    def get_leaderboard(self):
        """ Get the leaderboard in a format matching GameMode.history's single_table """
        table = self.get("/info/get_leaderboard")
        print(table)
        del table["http"]
        df = pd.DataFrame(table)[["Name", "Elo", "Team", "Home"]]
        return df#.values.tolist()

    def add_player(self, name, team):
        """ Add a player of a certain team. Automatically adds id, origin_table """


    #%% Game methods

    def check_state(self):
        url = f"{self.address}:{self.port}/api/long_poll"
        data = {"GID": self.gid, "LS": self.last_state}
        res = requests.post(url, json=data, auth=(self.gid, self.lpt))
        if res.status_code == 200:
            res = res.json()
            self.last_state = res["state"]
            res["play"] = (self.pid == res["apid"])
            return True, res
        if res.status_code == 410: # not existing in cache
            return True, {}
        return False, None

    def abort_game(self):
        res = self.post("/api/abort_game", {
            "GID": self.gid,
            "PID": self.pid,
            "TOKEN": self.player["token"]
        })
        return res



    def start_game(self, player, team, password, tooltips, opponent_table):
        """ Posts the player and team as well as the opponent table (if existing). If it is not set, just look """
        self.player = {
            "name": player,
            "team": team,
            "tooltips": tooltips # bool
        }
        res = self.post("/api/start_game", {
            "PNAME": player,
            "PTEAM": team,
            "PAUTH": password,
            "SHOW_TT": tooltips,
            "TID_OPP": opponent_table
        })
        del password
        match res["http"]:
            case 401:
                # player not authenticated or existing
                return {"state": "error"}
            case 200:
                # everything is fine, continue normal control flow
                self.player["id"] = res["pid"]
                self.pid = res["pid"]
                self.player["token"] = res["token"] # session token
                self.gid = res["gid"]
                self.lpt = res["lpt"]
                self.last_state = res["state"]
                del res["http"]
                del res["token"]
                return res

    def evaluate_break(self, coordinates):
        """ Send the coordinates to the server and return the decision ("won" / "lost") """
        res = self.post("/api/evaluate_break", {
            "GID": self.gid,
            "PID": self.player["id"],
            "TOKEN": self.player["token"],
            "coordinates": coordinates
        })
        if res["http"] in [200, 202]:
            del res["http"]
            self.last_state = res["state"]
            res["play"] = (self.pid == res["apid"])
            return res
        return {"state": "error"}


    def evaluate_play(self, coordinates):
        """ Send the coordinates to the server and return the decision ("go_on" / "change" / "lost" / "won") """
        res = self.post("/api/play_game", {
            "GID": self.gid,
            "PID": self.player["id"],
            "TOKEN": self.player["token"],
            "coordinates": coordinates
        })
        if res["http"] == 200:
            del res["http"]
            self.last_state = res["state"]
            res["play"] = (self.pid == res["apid"])
            return res
        return {"state": "error"}