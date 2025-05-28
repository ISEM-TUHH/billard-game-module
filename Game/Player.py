import numpy as np

class Player:
    """ Implementing a the player class and storing all relevant values
    
    CURRENTLY NOT IN USE

    :param json_data: parsed version of the player entry in players.json
    :type json_data: dict
    """

    def __init__(self, json_data):
        self.name = json_data["name"]
        self.team = json_data["team"]
        self.elo = json_data["elo"]
        self.id = json_data["id"]

    def make_id(self):
        """ Concats name and team and stores it as id
        """
        self.id = self.name + "AND" + self.team

    def to_dict(self):
        dic = {
            "name": self.name,
            "team": self.team,
            "elo": self.elo,
            "id": self.id
        }
        return dic