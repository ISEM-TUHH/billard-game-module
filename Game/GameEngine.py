import numpy as np

class GameEngine:
    """ This class implements basic physics based calculations for determining good hits.

    The holes get evenly spaced out along the edges of the defined size
    """

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

    def getShots(self, data):
        """ Calculate all possible first-level (simple) shots. Returns for each ball (except white) the coordinate the white ball should travel to, and the coordinate of the hole this ball will go to. This requires the white ball to exist, else it will return empty.

        Calcs based on https://www.real-world-physics-problems.com/physics-of-billiards.html

        :param data: coords of the balls from the camera module
        :type data: dict
        """
        if "white" not in data:
            print(f"The white ball was not found in the data provided to the getShots method of GameEngine.")
            return {}

        white = data["white"]
        wx, wy = white["x"], white["y"]
        wvec = np.array([wx,wy])

        shots = {}
        for b in data: # loop over every ball to find each best (simple) shot.
            if b == "white":
                continue # dont calculate shots for the white ball...

            coords = data[b]
            x, y = coords["x"], coords["y"]
            bvec = np.array([x,y])

            u = bvec - wvec # defines the directional vector of a mathematic line

            # find the minimum distance hole, that is behind the ball looking from white
            distances = []
            lam = [] # cant use lambda, but this is lambda
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

            shot = {
                "hole": {
                    "x": hole[0],
                    "y": hole[1]
                },
                "end-white": {
                    "x": endWhite[0],
                    "y": endWhite[1]
                }
            }
            shots[b] = shot
        
        return shots
