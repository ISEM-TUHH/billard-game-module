import requests
import dotenv

class GlobalAPI:
    """ Interface class with the API provided by the main global server """

    def __init__(self, configpath):
        self.config = dotenv.dotenv_values(configpath)

        self.address = self.config["ADDRESS"]

        # merge this into every request to authenticate with the API
        self.table_auth = {"TID": self.config["TABLEID"], "TAUTH": self.config["TAUTH"]}

        self.server_is_online = self.is_server_online()

    def endpoint(self, endpoint):
        """ Returns full address from endpoint passed as '/a/b' or 'a/b' """
        if endpoint[0] != "/":
            endpoint = "/" + endpoint
        return self.address + endpoint

    def is_server_online(self):
        try:
            requests.get(self.endpoint("/ping")) # just test if the website is reachable
        except:
            return False
        return True

    def post(self, endpoint, json):
        if not self.server_is_online: # in a debugging session
            return {"game_id": -1}

        data = json | self.table_auth
        response = requests.post(self.endpoint(endpoint), json=data, headers={"content-type": "application/json"})

        return response.json()

    def get(self, endpoint):
        """ Only send information relevant for auth """
        return self.post(endpoint, json={})