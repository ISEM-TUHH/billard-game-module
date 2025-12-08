import numpy as np
from .gamemodes import common_utils as utils
from .GameImage import BilliardBall

class GameEngine:
    """ This class implements basic physics based calculations for determining good hits.

    The holes get evenly spaced out along the edges of the defined size
    """

    group_map = {
        "half": ["half", "striped"],
        "striped": ["half", "striped"],
        "full": ["full", "solid"],
        "solid": ["full", "solid"],
        "eight": ["eight", "black"],
        "black": ["eight", "black"]
    }

    def __init__(self, size=(2230,1115), ballDiameter=57):
        self.w, self.h = tuple(size)
        w, h = tuple(size)
        
        self.diam = ballDiameter
        d = ballDiameter//2

        holes = [
            (d,d),
            (w//2, 0),
            (w-d, d),
            (d, h-d),
            (w//2, h),
            (w-d, h-d)
        ]
        self.holes = []
        for h in holes:
            self.holes.append(np.array([h[0], h[1]]))

    def getShots(self, data, group="open"):
        """ Calculate all possible first-level (simple) shots. Returns for each ball in the specified group (except white) the coordinate of the white ball and where it should travel to, the coordinate of the ball it will hit and hole this ball will go to. This requires the white ball to exist, else it will return empty.

        Calcs based on https://www.real-world-physics-problems.com/physics-of-billiards.html

        Args:
            data (dict): coordinates of the balls in the typical coordinate format
            group (optional str): only consider hits for balls in the group. Can be "open" (all balls), "half"/"striped", "full"/"solid", "eight"/"black"
        """
        if "white" not in data:
            print(f"The white ball was not found in the data provided to the getShots method of GameEngine.")
            return {}

        print("GAMEENGINE trying with group", group)

        white = data["white"]
        wx, wy = white["x"], white["y"]
        wvec = np.array([wx,wy])

        shots = {}
        for b, coords in data.items(): # loop over every ball to find each best (simple) shot.
            if b == "white":
                continue # dont calculate shots for the white ball...

            if group is not None and BilliardBall.getGroup(b) not in self.group_map[group]:
                print("GAMEENGINE trying with group", group, BilliardBall.getGroup(b), b)

                continue

            x, y = coords["x"], coords["y"]
            bvec = np.array([x,y])

            u = bvec - wvec # defines the directional vector of a mathematical line

            # find the minimum distance hole, that is behind the ball looking from white
            distances = []
            lam = [] # cant use the word lambda, but this is lambda
            for h in self.holes: # get the distances from every holes to the projected line between white and the ball
                l = ( np.dot( (h-bvec), u) ) / (np.linalg.norm(u, ord=2) **2)
                lam.append(l)
                distances.append( np.linalg.norm( h - bvec - l*u ) )
            
            index = None
            while min(distances) < 1e9:
                # loop over the distances to find the smallest one that is behind the ball (lambda > 0)
                d = min(distances)
                i = distances.index(d)
                l = lam[i]
                if l > 0:
                    index = i
                    break
                else:
                    distances[i] = 1e9 # disable this option and find the next closes hole
            
            if index == None:
                print(f"No valid hit found for {b}, exiting GameEngine.getShots empty.")
                continue
            
            # find the vector from the hole to the ball in the form "g: base + lambda*uh"
            hole = self.holes[index]

            uh = bvec - hole
            base = hole

            # the position the white ball should go to
            len_uh = np.linalg.norm(uh)
            endWhite = base + uh * (len_uh + self.diam)/len_uh

            # check, if there is a possible direct shot from the white to the end position of the white ball (near the ball we want to hit)
            skip_this_ball_flag = False
            for otherBall, otherCoords in data.items(): # check for all balls...
                if otherBall in [b, "white"]: # if they are not the balls for which we draw the segment...
                    continue
                isInRegion, distance = utils.project_on_segment(utils.coord_to_vec(otherCoords), wvec, endWhite)
                if not isInRegion: # if they cant be projected onto the line segment, we directly go to the next ball
                    continue
                if distance <= self.diam: # if they can be projected onto the line and are at less than one ball diameter distance, the shot is impossible and we break this loop as well as the entire ball
                    skip_this_ball_flag = True
                    break
            if skip_this_ball_flag:
                continue

            # check, if there is a possible direct shot from the ball to the hole
            for otherBall, otherCoords in data.items(): # check for all balls...
                if otherBall in [b, "white"]: # if they are not the balls for which we draw the segment...
                    continue
                isInRegion, distance = utils.project_on_segment(utils.coord_to_vec(otherCoords), hole, bvec)
                if not isInRegion: # if they cant be projected onto the line segment, we directly go to the next ball
                    continue
                if distance <= self.diam: # if they can be projected onto the line and are at less than one ball diameter distance, the shot is impossible and we break this loop as well as the entire ball
                    skip_this_ball_flag = True
                    break
            if skip_this_ball_flag:
                continue

            shot = {
                "hole": {
                    "x": hole[0],
                    "y": hole[1]
                },
                "ball": coords,
                "end-white": {
                    "x": endWhite[0],
                    "y": endWhite[1]
                },
                "white": white
            }
            shots[b] = shot
        
        return shots
