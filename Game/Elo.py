import math

class Elo():
    """Simple implementation of the elo rating system originally developed by Arpad Elo.
    
    :param K: constant multiplier/penalty
    :type K: int
    """

    def __init__(self, K=30):
        self.K = K

    def match(self, players, winner=0):
        """Players are two dict-objects with the key "elo". Updates their elo value based on the outcome

        :param players: list of the two player dictionaries
        :type player: list<dict>
        :param winner: winner's index in the player list. 0.5 if draw.
        """
        if len(players) != 2 or type(player[0]) != dict:
            print(f"Error in players argument: {players}")
        
        elo1, elo2 = players[0]["elo"], players[1]["elo"]
        odd1 = self.propability(elo1, elo2)
        odd2 = self.propability(elo2, elo1)
        
        outcome = winner # directly use winner's index as indication of outcome -> 0 if p1 has won, 1 if p2.

        nelo1 = elo1 + self.K*((1-outcome)-odd1)
        nelo2 = elo2 + self.K*(outcome-odd2)

    def propability(self, elo1, elo2): 
        """Returns the propability of player with elo1 of winning agains player with elo2
        """
        return 1/(1 + math.pow(10, (elo2 - elo1)/400))