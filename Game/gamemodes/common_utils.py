import numpy as np
import pandas as pd
import json
import glob

""" This file supplies common operations used by the gamemodes. Mainly coordinate operations """

def ball_distance(coords, b1, b2):
    """ From a coords dict, calculates the distance between two given balls """

def metric_distance(c1, c2):
    """ Metric distance between two coordinates each containing {"x": 0, "y": 0} """
    return np.linalg.norm(coord_to_vec(c1) - coord_to_vec(c2))
    #return np.sqrt((float(c1["x"]) - float(c2["x"])**2 + (float(c1["y"] - float(c2["y"]))**2)))

def metric_distance_closest(coords, c2):
    """ Calculates the distance between one point and all points in the coords. Returns the closest coord and distance. """
    for k, v in coords.items():
        coords[k]["distance"] = metric_distance(v, c2)
    min_element = min(coords.values(), key=lambda x: x["distance"])
    return min_element, min_element["distance"]


def classify_region(coord, region_img, translator):
    """ Based on a loaded region image (bw image of the size of the playing field with a color for each region), classifies the region of the coords given. Needs a translator dictionary (mapping color to region name) """
    # TODO: design region_img/translator (storage/loading) system
    color = region_img.astype(int)[int(coord["x"]), int(coord["y"])]
    region = translator[str(color)]
    return region

def project_line(coord, corner1, corner2):
    """ Draws a mathematical line segment between the two corners (each in coords dict format) and finds the closest point to the passed coord on the line. If the projection would be outside the line segment, it returns the closest corner. """
    c1, c2, c = coord_to_vec(corner1), coord_to_vec(corner2), coord_to_vec(coord)
    v = c2 - c1
    u = c - c1

    alpha = np.dot(v/np.linalg.norm(v), u/np.linalg.norm(v))
    print("OUT of common_utils.project_line:", alpha, v, u, c1, c2, c)
    if alpha < 0:
        return corner1
    if alpha > 1:
        return corner2
    else:
        return vec_to_coord(c1 + alpha*v)

def get_border_intercept(coordStart, coordPass, size=(2230, 1115)):
    """ Determines a point somewhere outside the playing field on a line drawn from a starting point through a passing point. Used for drawing. """
    cs, cp = coord_to_vec(coordStart), coord_to_vec(coordPass)
    max_length = np.linalg.norm(size) # worst case needed length
    
    v = cp - cs
    ce = max_length/np.linalg.norm(v) * v + cs
    return vec_to_coord(ce)

def coord_to_vec(coord):
    """ Transforms a {"x": 0, "y": 0} dict to a np.ndarray [x, y] """
    return np.array([coord["x"], coord["y"]]) 

def vec_to_coord(vec):
    """ Transforms a np.ndarry [x,y] into a dict {"x": 0, "y": 0} """
    return {"x": vec[0], "y": vec[1]}

ALL_BALLS = ["1", "2", "3", "4", "5", "6", "7", "eight", "9", "10", "11", "12", "13", "14", "15", "white"]

def coords_report(coordsNew, coordsOld):
    """ Find the differences between new and old coordinates and report on sunken balls. """
    ballsOld = set(coordsOld.keys())
    ballsNew = set(coordsNew.keys())

    sunkenBalls = ballsOld - ballsNew
    appearedBalls = ballsNew - ballsOld
    keptBalls = ballsNew & ballsOld

    legalSunkenBalls = sunkenBalls.copy() - {"white", "eight"}
    report = {
        "eight_sunk": "eight" in sunkenBalls,
        "white_sunk": "white" in sunkenBalls,
        "n_sunk": len(sunkenBalls),
        "n_sunk_legal": len(legalSunkenBalls), # only considering legal balls to sink
        "n_sunk_half": len([k for k in legalSunkenBalls if int(k) > 8 and int(k) < 16]), 
        "n_sunk_full": len([k for k in legalSunkenBalls if int(k) < 8])
    }

    return report

def is_close_enough(c1, c2, tolerance=50):
    """ Are the two coordinates close enough too each other? tolerance is given in mm (as are coordinates) """
    u1 = coord_to_vec(c1)
    u2 = coord_to_vec(c2)
    return np.linalg.norm(u1 - u2) < tolerance

def check_positions(real, goal, tolerance=50):
    """ Check if each ball of two sets of balls are close enough to each other (tolerance in mm). 
    If the balls are in the format {"white": {...}, "1": {...}}, it checks if each ball is on the corresponding goal ball with the same name.
    If the balls are just grouped (half, full, white, eight in the "group" field), check if they are within tolerance of a goal ball with the same group.
    If there are no identifications, just check if every ball is on any goal ball position.

    :returns: bool (if matches), str (message why it failed), dict (coords of real balls with "incorrect"/"correct" name to display. dict just for compatability, dict keys are unimportant)    
    """
    output = True
    message = "Correct positions"
    signal_coords = [] # red dummy balls are not placed correctly, green are placed correctly

    # ensure inputs are a lists
    real_clean = real if type(real) is list else list(real.values())
    df_real = pd.DataFrame(real_clean)
    goal_clean = goal if type(goal) is list else list(goal.values())
    df_goal = pd.DataFrame(goal_clean)

    if len(real) != len(goal):
        output = False
        message = "The number of balls is not matching."

    #print(goal.values())
    elif (type(goal) is dict and np.all(["name" in x.keys() for x in goal.values()]) ) or (type(goal) is list and "name" in goal[0].keys()):
        # if the balls are named, they should be perfect matches (within tolerance) of the goal balls with the same name
        for k,v in real.items():
            coord = v.copy()
            if k not in goal.keys():
                # a wrong ball is on the field?
                output = False
                coord["name"] = "incorrect"
            elif not is_close_enough(v, goal[k]):
                output = False
                coord["name"] = "incorrect"
            else: 
                coord["name"] = "correct"
            signal_coords.append(coord)
        output = True

    else:
        if "group" not in goal_clean[0].keys():
            # if no identifications are given, just look if all real balls are on any goal balls
            df_goal["group"] = "common"
            df_real["group"] = "common"
        
        # if the balls are only known as part of a group, they should be within tolerance of goal balls of their group
        for k, df in df_real.groupby("group"):
            goals = df_goal[df_goal["group"] == k]
            if goals.shape[0] != df.shape[0]:
                # if there are not the same numbers of balls in each group, they cant possibly match
                output = False
                message = f"The number of {k.lower()} balls is not matching."

            x_goal, y_goal = goals["x"].to_numpy().reshape((-1, 1)), goals["y"].to_numpy().reshape((-1, 1))
            x_real, y_real = df["x"].to_numpy(), df["y"].to_numpy()

            distances_squared = (x_real - x_goal)**2 + (y_real - y_goal)**2
            in_range = distances_squared <= tolerance**2

            all_correct = in_range.any(axis=0).all() and in_range.any(axis=1).all() # check if there is at least one in_range==True in every row and col
            if not all_correct:
                output = False
                logic = in_range.any(axis=0)
                incorrect = np.array(np.where(~logic)).flatten()
                correct = np.array(np.where(logic)).flatten()
                print("Rough equal: not all correct", incorrect)
                message = "Correct ball positions"
                for index in incorrect:
                    signal_coords.append({"name": "incorrect", "x": x_real[index], "y": y_real[index]})
                for index in correct:
                    signal_coords.append({"name": "correct", "x": x_real[index], "y": y_real[index]})

    signal_coords_dict = {}
    for i,s in enumerate(signal_coords):
        signal_coords_dict[str(100+i)] = s

    print(signal_coords_dict)
    return output, message, signal_coords_dict




#%% Coordinate file handling

def load_coordinate_file(path):
    """ load a coordinate file (like longest break challenges) from a file. See coordinate file reference for details on file formatting. """
    data = {}
    with open(path, "r") as f:
        data = json.load(f)

    for k in data["coordinates"]:
        data["coordinates"][k]["name"] = k # this field is needed in some iterators

    return data
    
def load_challenge_files(glob_path, sort_difficulty=False):
    """ looks for all files matching the glob pattern passed (see Python's glob module) and loads them with load_coordinate_file. Use this to load challenge files. 

    :param bool sort_diffulty: decide if the returned list should be sorted by the difficulty field (easiest come first). Otherwise, sorts alphabetically by name to achieve consistency.
    """
    files = glob.glob(glob_path)
    #print(glob_path, ":", files)

    challenges = []
    for file in files:
        challenges.append(load_coordinate_file(file))

    if sort_difficulty:
        challenges.sort(key=lambda x: x["difficulty"])
    else:
        challenges.sort(key=lambda x: x["name"])

    #print("challenges", len(challenges))
    return challenges

