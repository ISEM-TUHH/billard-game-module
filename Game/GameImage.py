import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json # for testing
import os
import cv2
from random import randint
import copy
import qrcode

#from .GameEngine import GameEngine

def ie(dic, key, default):
	""" If key in dic returns value in dic else default """
	return dic[key] if key in dic else default

class GameImage:
	"""Class to generate an image from different game modes and other information

	Each image starts with a black background, as this is "neutral" on a beamer.
	:param size: width x height of the image in pixels
	:type size: tuple<int>
	:param phys: how many meters are 1000 pixels? (equivalent to how many mm are 1 pixel)
	:type phys: float
	"""
	ballDiameter = 57 # diameter of a billiard ball (snooker) in mm

	def __init__(self, definition=[], size=(2230, 1115), phys=1, img_cache={
		"isem-logo": "static/images/ISEM-only.png", # small logo without text for subimg display
		"isem-logo-big": "static/images/isem_logo_big.png", # big logo with text for central display
		"feedback-form-qr": "https://www.youtube.com/watch?v=XfELJU1mRMg" # link to the feedback form
	}):
		self.img = Image.new(mode="RGBA", size=size, color="#000000ff")
		#self.img = Image.new(mode="RGB", size=size, color="#50b12c")
		self.draw = ImageDraw.Draw(self.img)
		self.phys = phys
		self.w, self.h = size
		self.current_dir = os.path.dirname(__file__)

		self.FLAG_MODIFIED = False # track if the image has been updated since the last redraw


		# list of graphical parts that can only exist max once.
		self.static = ["balls", "text", "team", "break", "central_image"]

		# loading of common referenced images (ISEM logo etc), provide directly
		self.img_cache = {}
		for k,v in img_cache.items():
			if type(v) is str:
				if v.startswith("http"):
					self.img_cache[k] = qrcode.make(v).convert("RGBA") # generate a qrcode and change mode from "1" to "RGBA" so it can be pasted
				else:
					self.img_cache[k] = Image.open(os.path.join(self.current_dir, v))
			else:
				self.img_cache[k] = v

		self.definition = definition
		if len(definition) != 0:
			self.draw_from_dict(definition)

	def copy(self):
		""" Creates a new object with the same definition list. Also copies the loaded img_cache to minimize storage operations. """

		return GameImage(definition=self.definition.copy(), img_cache=self.img_cache)

	def draw_from_dict(self, definition, draw=True):
		""" Draw the gameimage from a list<dictionary> specifying the subparts. Execution flow is from top to bottom, so lower parts are on a higher image layer. """
		self.img = Image.new(mode="RGBA", size=(self.w, self.h), color="#000000ff")
		#self.img = Image.new(mode="RGB", size=size, color="#50b12c")
		self.draw = ImageDraw.Draw(self.img)

		if None in definition:
			for part in definition:
				if part is None: continue
				self.update_definition(part)
			return self.definition

		self.definition = definition
		for part in self.definition:
			#part["ref"] = ie(part, "ref", randint(0, int(1e6))) if part["type"] not in self.static else part["type"] # random reference id
			part["ref"] = ie(part, "ref", randint(0, int(1e6)) if part["type"] not in self.static else part["type"])

			if not draw: continue

			match part["type"]:
				case "balls":
					self.placeAllBalls(part["coords"])
					if "draw_lines" in part.keys():
						self.drawBallConnectionsOld(part["coords"])
				case "text":
					self.instructionText(part["text"], subimg=(part["subimg"] if "subimg" in part.keys() else None))
				case "team":
					self.nameTeamText(parts["player_name"], parts["player_team"])
				case "break":
					self.drawBreak(ball=part["draw_ball"])
				case "central_image":
					self.centralImage(part["img"])
				case "line":
					self.line(part["c1"], part["c2"], color=ie(part, "color", "white"), width=ie(part, "width", 3))
				case "rectangle":
					self.rectangle(part["c1"], part["c2"], outline=ie(part, "outline", "white"), width=ie(part, "width", 3), fill=ie(part, "fill", None))
				case "bullseye":
					self.bullseye(center=ie(part, "center", None), r=ie(part, "radius", 30))
				case "polygon":
					self.draw.polygon(part["points"], fill=ie(part, "fill", None), outline=ie(part, "outline", "white"), width=ie(part, "width", 3))
				case "arrow_bottom":
					self.arrow_bottom(**part) # bottom, orientation, length, head_with|line_width|color
				case "arrow":
					self.arrow(**part) # needs coords start, end. Otherwise takes same optional arguments as arrow_bottom
				case "possible_shots":
					self.drawBallConnections(**part)

		return self.definition

	def redraw(self):
		self.draw_from_dict(self.definition)

	def update_definition(self, val, ref=None, subfield=None, new_instance=False, layer=-1, remove=False):
		""" Adds a new part to the image definition if ref is None or no current entry has the same ref. If subfield != None, looks for the key in a part with given ref and only updates that. """
		self.FLAG_MODIFIED = True

		if type(val) is dict and "type" in val.keys() and val["type"] in self.static: # handle static parts
			ref = val["type"]
		if type(val) is dict and "ref" in val.keys():
			ref = val["ref"]

		# if the passed dict has remove==True, remove it. 
		if type(val) is dict and "remove" in val.keys() and val["remove"]:
			remove = True

		if remove:
			self.rm_definition(ref)
			return
		# debug
		#print("available ref:", [p["ref"] for p in self.definition])
		#print("this ref:", ref)

		if ref is not None and (ref in [p["ref"] for p in self.definition] or ref in self.static):
			index = next((index for (index, d) in enumerate(self.definition) if d["ref"] == ref), None)

			if ref in self.static and index is None:
				val["ref"] = ref
				self.definition.append(val)

			elif not subfield is None:
				assert subfield in self.definition[index].keys(), f"The given subfield {subfield} does not exist in the part {self.definition[index]['type']} with keys {self.definition[index].keys()}."

				self.definition[index][subfield] = val

			else:
				#print("GI update:", val, "ref:", ref, "index:", index)
				self.definition[index] = val | {"ref": ref}
				#print("Success? GI at index:", self.definition[index])

		else: # add a new part at the specified layer (-1 for last, other negative indices are supported too, but always +1)
			if ref is None:
				val["ref"] = randint(0, int(1e6)) if ref != None else ref
			if layer == -1:
				self.definition.append(val)
			else:
				if layer < 0:
					layer += 1
				self.definition.insert(layer, val)

	def rm_definition(self, ref):
		""" Remove an element from the definition by ref """
		index = next((index for (index, d) in enumerate(self.definition) if d["ref"] == ref), None)
		if index is not None:
			self.definition.pop(index)

	def update_text(self, text):
		self.update_definition(text, ref="text", subfield="text")

	def getImageCV2(self):
		if self.FLAG_MODIFIED:
			self.redraw()
		return np.array(self.img)[:,:,[2,1,0]] # shift from rgb to bgr

	def line(self, c1, c2, color="white", width=3): # TODO: add different coordinate formats
		if type(c1) is dict:
			c1 = (c1["x"], c1["y"])
			c2 = (c2["x"], c2["y"])
		self.draw.line([c1, c2], fill=color, width=width)

	def rectangle(self, c1, c2, outline="white", width=5, fill=None):
		self.draw.rectangle([c1, c2], outline=outline, width=width, fill=fill)

	def bullseye(self, center=None, r=30):
		if center is None:
			bullX, bullY = self.w//4, self.h//2
		bullX, bullY = center[0], center[1]
		r = 30 # radius of each ring
		#print(bullX, bullY)
		for i in [4,2,0]:
			white = 2*(i+1)*r
			black = 2*i*r
			
			self.draw.ellipse((bullX-white, bullY-white, bullX+white, bullY+white), fill="#FFFFFF")
			self.draw.ellipse((bullX-black, bullY-black, bullX+black, bullY+black), fill="#000000")
		# inner circle:
		self.draw.ellipse((bullX-r, bullY-r, bullX+r, bullY+r), fill="#000000")

	def arrow_bottom(self, bottom, orientation, length, head_width=50, line_width=10, color="white", **kwargs):
		""" Draws and arrow by specifying the bottom point. bottom as np.array([x, y]), orientation in degrees relative to +x-axis in mathemtical positive direction"""

		# TODO: add feature to put text on the arrow?
		bot = np.array([bottom["x"], bottom["y"]])

		start_head = length - head_width
		polygon = np.array([
			[0, 0], # bottom
			#[start_head, 0], # start of head
			[length, 0], # head
			[start_head, -head_width/2],
			[length, 0],
			[start_head, +head_width/2],
		]).T

		rad = np.pi*orientation/180
		cs = np.cos(rad)
		sn = np.sin(rad)
		rot = np.array([[cs, sn], [-sn, cs]])

		arrow = [(int(c[0]), int(c[1])) for c in ((rot @ polygon).T + bot)]

		#print(arrow)
		self.draw.line(arrow, width=line_width, fill=color)
		self.draw.circle(arrow[1], radius=line_width//2, fill=color, width=0)
		#self.draw.polygon(arrow[2:], outline=color, width=line_width, fill=color)

	def arrow(self, start, end, offset=0, **kwargs):
		""" Arrow pointing from start to end """
		top = np.array([end["x"], end["y"]])
		bot = np.array([start["x"], start["y"]])

		u = top - bot
		length = np.linalg.norm(u)
		orientation = np.angle(u[0] - 1j*u[1], deg=True) # gets the complex angle: -u[1] due to orientation of the coordinate system in PIL vs normal maths :)
		if 2*offset >= length:
			#offset =
			pass 
		elif offset != 0: 
			bot = bot + offset/length * u
			length = length - 2*offset
		
		#print("ARROW", length, orientation)
		self.arrow_bottom({"x": bot[0], "y": bot[1]}, orientation, length, **kwargs)

	def placeBall(self, pos, n, d=None):
		"""Place a ball on the canvas self.img based on its number

		:param pos: (x,y) center of the ball in mm from the top left
		:type pos: tuple<int>
		:param n: number of the ball
		:type n: int or str
		:param d: diameter of the ball in pixels, automatically determined to be accurate according to self.phys and 
		:type d: optional int
		"""
		if d == None:
			d = int(self.ballDiameter/self.phys)
		
		b = BilliardBall(n)
		bImg = b.getImg(d)
		x,y = tuple([int(float(i)/self.phys - d//2) for i in pos])
		self.img.paste(bImg, (x,y), bImg) # second call for mask, so the corners dont get overwritten

	def placeAllBalls(self, data):
		"""Place all balls mentioned in the data dict on the canvas self.img

		:param data: dictionary matching the number of a ball (key) to its position (tuple x,y) from the upper left in mm. Can also just be the output of Camera.get_coords (.../v1/getcoords)
		:type data: dict<tuple<float>> or list<dict>
		"""
		unique_map = {
			"eight": 8,
			"white": 16,
			"dummy": 17,
			"correct": 18,
			"incorrect": 19
		}

		for b in data:			
			if type(data) == list:
				rawN = b["name"]
				#number = rawN if type(rawN) is int else unique_map[rawN]
				#number = 8 if rawN=="eight" else (16 if rawN=="white" else int(rawN))
				x,y = b["x"],b["y"]
				self.placeBall((x,y),number)
				continue
			elif "x" in data[b].keys():
				pos = (data[b]["x"], data[b]["y"])
				self.placeBall(pos, data[b]["name"])
			else:
				#print(b)
				self.placeBall(data[b], int(b))

	def drawBallConnectionsOld(self, data, drawBalls=True):
		""" Draw a line between the white ball an every other ball. If the white ball is not found on the image, exit.

		:param data: coordinates as passed from the camera
		:type data: list
		:param drawBalls: should this also draw the balls on the image
		:type drawBalls: optional bool
		"""
		localData = {}
		data2 = data if type(data) == list else [data[b] for b in data]
		for b in data2:
			#print(b)
			localData[b["name"]] = b
		
		if not "white" in localData:
			print(f"Trying to draw the connections from the white ball, but white not found.")
		else:
			xw, yw = localData["white"]["x"], localData["white"]["y"]
			ge = GameEngine() # use the GameEngine to get all available shots
			shots = ge.getShots(localData)

			for b in shots:
				if b == "white":
					continue

				x, y = localData[b]["x"], localData[b]["y"]
				
				shot = shots[b]
				hole = shot["hole"]
				end_white = shot["end-white"]
				xh, yh = hole["x"], hole["y"]
				xwe, ywe = end_white["x"], end_white["y"]

				kwargs = {"offset": 20, "color": "grey", "line_width": 5, "head_width": 10}
				self.arrow(end=hole, start=localData["white"], **kwargs) # ball to hole
				self.arrow(end=start_white, start=end_white, **kwargs) # white to ball
				#self.draw.line([(xw,yw),(xwe,ywe)], fill="grey", width=4)
				#self.draw.line([(x,y),(xh,yh)], fill="grey", width=4)

		if drawBalls:
			self.placeAllBalls(data2)

	def drawBallConnections(self, shots, offset=35, line_width=6, head_width=12, **kwargs):
		""" Takes the output of GameEngine.getShots and draws arrows accordingly. Each shot path gets the color of the ball it is supposed to sink (except for the black ball, which would not be visible)

		Args:
			shots (dict): output of GameEngine.getShots like {"1": {"hole": {"x": 123, "y": 123}, "ball": ..., "end-white": ..., "white": ...}, ...}
			kwargs (optional): arguments passed to GameImage.arrow()
		"""
		offset = 35 # 35mm offset to the start and end of the arrow from the passed coordinates
		for ballName, shot in shots.items():
			color = BilliardBall.getColor(ballName)
			if ballName == "eight":
				color = "#FFFFFF"
			print("drawBallConnections:", ballName, color)
			self.arrow(shot["white"], shot["end-white"], offset=offset, color=color, line_width=line_width, head_width=head_width, **kwargs)
			self.arrow(shot["ball"], shot["hole"], offset=offset, color=color, line_width=line_width, head_width=head_width, **kwargs)

	def instructionText(self, text, subimg=None):
		"""Place text on top and flipped on the bottom of the image. Font size is chosen automatically.

		:param text: Text to be placed
		:type text: str
		:param subimg: Image to be placed directly under the text
		:type subimg: optional PIL Image or relative path to image 
		"""		
		fs = int(self.h/15)# if self.w/len(text) < # TODO: make it more dynamic 
		font = ImageFont.truetype(self.current_dir + "/../Roboto-Black.ttf", fs)

		#img = Image.new(mode="RGBA", size=(self.w, int(1.5*fs)), color="#00000000")
		img = Image.new(mode="RGBA", size=(self.w, int(3*fs)), color="#00000000")
		draw = ImageDraw.Draw(img)

		if subimg != None: # draw subimg before text to control layering
			size = self.w, int(1.5*fs)
			if type(subimg) == str:
				if subimg in self.img_cache.keys():
					subimg = self.img_cache[subimg]
				else:
					# load from file
					subimg = Image.open(self.current_dir + "/" + subimg)
			subimg.thumbnail(size, Image.Resampling.LANCZOS)
			w,h = subimg.size
			img.paste(subimg, ((self.w-w)//2, int(1.5*fs)))

		_,_, w, h = draw.textbbox((0,0), text.replace("**", ""), font = font)
		center = (self.w - w)//2

		# quasi markdown format
		if "**" in text:
			offset_left = 0
			for i, textpart in enumerate(text.split("**")):
				_, _, w2, h2 = draw.textbbox((0, 0), textpart, font = font, stroke_width=3)
				if i%2 == 1:
					draw.text((center + offset_left, 0), textpart, font = font, stroke_width=3, stroke_fill="green", fill="white", background="#00000000")
				else:
					draw.text((center + offset_left, 0), textpart, font = font, fill="white", background="#00000000")
				offset_left += w2
		else:
			draw.text((center, 0), text, font=font, fill="white", background="#00000000")

		self.img.paste(img, (0,0), img)
		timg = img.transpose(Image.ROTATE_180)
		#self.img.paste(timg, (0,int(self.h-1.5*fs)), timg)
		self.img.paste(timg, (0,int(self.h-3*fs)), timg)

	def nameTeamText(self, name, team):
		"""Put the name and team on the right side of the image, oriented outwards.
		"""
		fs = int(self.h//25)
		font = ImageFont.truetype(self.current_dir + "/../Roboto-Black.ttf", fs)
		img = Image.new(mode="RGBA", size=(self.h, int(1.5*fs)), color="#00000000")
		draw = ImageDraw.Draw(img)

		_,_, wn,hn = draw.textbbox((0,0), name, font=font)
		_,_, wt,ht = draw.textbbox((0,0), team, font=font)
		draw.text((self.h//4 - wn//2, 0), name, font=font, fill="white", background="#00000000")
		draw.text((3*self.h//4 - wt//2, 0), team, font=font, fill="white", background="#00000000")

		timg = img.transpose(Image.ROTATE_90)
		self.img.paste(timg, (self.w - int(1.5*fs),0), timg)

	def drawBreak(self, ball=True):
		""" Draw the basic triangle for a break and optionally the white ball for break """
		center = self.h//2
		offTop = 160
		offFront = 290
		self.draw.polygon([(center, center-offTop),(center+offFront, center), (center, center+offTop)], fill=(255,255,0))
		if ball:
			self.placeBall((4*self.w//5, center), "white")

	def centralImage(self, img):
		""" Draw an (PIL) image in the center of the image. Scaling is currently done before using img.resize((w, h)) """
		# TODO: add sizing options
		if type(img) is str:
			if img in self.img_cache.keys():
				img = self.img_cache[img]
			else:
				img = Image.open(img, ) # TODO: is this the correct file path format?
		w, h = img.size
		#print("CENTRAL IMAGE", w, h)
		if img.mode == "1": # black and white qr codes
			#print(img.size)
			self.img.paste(img, ((self.w - w)//2, (self.h - h)//2))
		else:
			self.img.paste(img, ((self.w - w)//2, (self.h - h)//2), mask=img.split()[3])

	# OLD
	def addGameMode(self, supermode, game):
		""" Add an overlay to the image depending on the current game supermode.

		:param supermode: supermode of the game
		:type supermode: str
		:param game: Game Object calling this function
		:type game: Game Object 
		"""
		logo1 = Image.open(self.current_dir + "/static/isem_logo.png")
		logo = logo1.resize((700,350))

		match supermode:
			case "base":
				#self.instructionText("Welcome to Billard@ISEM!", subimg="static/images/ECIUxISEM-transparent.png")
				#self.instructionText("Select a Game Mode", subimg="static/images/ECIUxISEM-transparent.png")
				self.instructionText("Select a Game Mode", subimg="static/images/ISEM-only.png")
				#self.img.paste(logo, (self.w//2-350, self.h//2-350//2))
				self.centralImage(logo)
			case "trickshots":
				self.instructionText("Select a Trickshot")
			case "kp2":
				kp2mode = game.kp2mode
				#self.instructionText(" ", subimg="static/images/ECIUxISEM-transparent.png")
				self.instructionText(" ", subimg="static/images/ISEM-only.png")
				if kp2mode not in ["base", "trickshot", "precision"]:
					# draw the outline of the push unit
					# measurements are roughlty equivalent to the real physical object
					right, top = self.w, self.h//2
					self.draw.rectangle([(right-250, top-280//2),(right, top+280//2)], outline="yellow", width=10)
					self.draw.rectangle([(right-250-90, top-10),(right-250, top+10)], outline="yellow", width=10)

				match kp2mode:
					case "precision":
						dif = game.kp2_prec_difficulty

						text = "Challenge: Precision" if game.live_value == "" else game.live_value
						self.instructionText(text)
						# draw a bullseye
						bullX, bullY = self.w//4, self.h//2
						r = 30 # radius of each ring
						#print(bullX, bullY)
						for i in [4,2,0]:
							white = 2*(i+1)*r
							black = 2*i*r
							
							self.draw.ellipse((bullX-white, bullY-white, bullX+white, bullY+white), fill="#FFFFFF")
							self.draw.ellipse((bullX-black, bullY-black, bullX+black, bullY+black), fill="#000000")
						# inner circle:
						self.draw.ellipse((bullX-r, bullY-r, bullX+r, bullY+r), fill="#000000")

						# process difficulty
						right, top = self.w, self.h//2
						lines = [right-250, right-500, right-750]
						for i in range(3):
							width = 2 if i != dif else 5
							color = "grey" if i != dif else "white"
							self.draw.line([(lines[i], 100), (lines[i], self.h-100)], fill=color, width=width)

						offset = lines[dif]
						self.draw.rectangle([(offset, top-280//2),(offset+250, top+280//2)], outline="yellow", width=10)
						self.draw.rectangle([(offset-90, top-10),(offset, top+10)], outline="yellow", width=10)

						return
					case "results":
						# show results screen -> podium
						self.img.paste(logo, (self.w//2-350, self.h//2-350//2))
						self.instructionText(f"Score: {str(game.kp2_last_score)}")
						return
					case "base":
						self.img.paste(logo, (self.w//2-350, self.h//2-350//2))
						text = "Select a challenge on the screen" if game.live_value == "" else game.live_value
						self.instructionText(text)
						return
					case "trickshot":
						trickshot = Trickshot(game.trickshots[str(game.trickshot_current_id)])
						timg = trickshot.getTrickshotImage()
						#timg = Image.fromarray(timgNP.astype("uint8"), "RGB")
						self.img.paste(timg, (0,0))
						#self.img = timg
						#self.draw = ImageDraw.Draw(self.img)
						text = game.live_value
						self.instructionText(text)
						return
					case "break":
						text = "Challenge: Break" if game.live_value == "" else game.live_value
						self.instructionText(text)
						self.drawBreak(ball=False)
					case "distance":
						text = "Challenge: Distance" if game.live_value == "" else game.live_value
						self.instructionText(text)
			
			case "game-local":
				self.instructionText(game.game.message)
				match game.game.state:
					case "pre": # before entering names
						self.img.paste(logo, (self.w//2-350, self.h//2-350//2))
					case "determine": # when determining who should break
						self.placeAllBalls(game.game.display_coords)
						self.instructionText(f"", subimg="static/images/ISEM-only.png")
					case "break":
						self.drawBreak()
						self.instructionText(f"", subimg="static/images/ISEM-only.png")
					case "game":
						pass # nothing besides the message should be displayed
					case "winner":
						pass # nothing besides the message should be displayed -> one day






				


class BilliardBall:
	"""Class to store each Billiard Balls graphical attributes

	Each ball is initiated with its number with number 16 being the white ball. Number 1-7 are full, 8 is black, 9-15 are half.

	Special balls are dummy (17), correct (18) and incorrect (19)
	"""
	white = "#d5d1c5"
	colors = ["#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#20201e","#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517", white, "#058aff", "#69f902", "#f9021f"]#"#fb48c4"] # the last entry is a dummy ball color (neon pink)
	unique_map = {
		"eight": 8,
		"white": 16,
		"dummy": 17,
		"correct": 18,
		"incorrect": 19
	}

	def __init__(self, n):


		current_dir = os.path.dirname(__file__) # finding the Roboto-Black.ttf/navigating the dirs
		self.fontpath = current_dir + "/../Roboto-Black.ttf"

		n = int(n) if n not in self.unique_map.keys() else self.unique_map[n]
		self.indexNumber = n
		self.n = n if n != 16 and n != 17 else "" # empty string for the white and dummy ball
		self.type = "half" if (n>8 and n<16) else "full"
		if n == 8:
			self.type = "eight"
		elif n == 16:
			self.type = "white"

		self.color = self.colors[n-1]
		#self.white = self.colors[-2]

	@classmethod
	def getColor(cls, n):
		""" Get the hexcode of the color of the ball based on the n value (number or str keys) """
		n = int(n) if n not in cls.unique_map.keys() else cls.unique_map[n]
		return cls.colors[n-1]

	@classmethod
	def getGroup(cls, n):
		""" Get the group of the color of the ball based on the n value (number or str keys). Everything over 16 is dummy."""
		n = int(n) if n not in cls.unique_map.keys() else cls.unique_map[n]
		if n == 8:
			group = "eight"
		elif n == 16:
			group = "white"
		elif n > 16:
			group = "dummy"
		else:
			group = "half" if (n>8 and n<16) else "full"
		return group

	def getImg(self, d):
		"""Get the image of the ball with its number, half or full and color.
		
		:param d: Diameter of the returned image (side of square) in px
		:type d: int
		:return: PIL.Image object
		"""
		self.font = ImageFont.truetype(self.fontpath, d//3)
		
		img = Image.new(mode="RGBA", size=(d+1, d+1))
		draw = ImageDraw.Draw(img)

		draw.ellipse((0,0,d,d), fill=self.color, outline=self.color) # main color 
		if self.type == "half":
			draw.rectangle((0,0,d,d//5), fill=self.white, outline=self.white)
			draw.rectangle((0,4*d//5,d,d), fill=self.white, outline=self.white)
			draw.ellipse((-d//2,-d//2,3*d//2,3*d//2), outline="#00000000", width=d//2)

		if self.indexNumber < 17: # do not draw a white inner circle for dummy/special balls
			draw.ellipse((d//4,d//4, 3*d//4, 3*d//4), fill=self.white, outline=self.white) # inner white circle
			_,_, w, h = draw.textbbox((0,d//20), str(self.n), font = self.font)
			draw.text(((d-w)//2, (d-h)//2), str(self.n), font=self.font, fill="black")
		draw.ellipse((0,0,d,d), outline=self.white) # draw a white circle around it (good for balls with weak colors)

		return img

class Trickshot: 
	"""Class to draw a trickshot with all its belongings onto the gameimage based on the json/dict defining the trickshot (see subfolder trickshots)

	:param definition: dict describing the trickshot, most likely loaded from a trickshots/*.json
	:type definition: dict
	:param size: the size of the image in mm = pixel. Sample down later.
	:type size: optional tuple (width, height)
	"""

	def __init__(self, definition, size=(2230, 1115)):
		self.d = definition
		self.width = size[0]
		self.height = size[1]
		self.img = Image.new(mode="RGBA", size=size)
		self.draw = ImageDraw.Draw(self.img)

	def getTrickshotImage(self):
		""" Draws everything from the definition and returns a cv2 image. 
		
		The background gets set to black, but this is not a problem as thisis "off" on a beamer.
		"""
		# actually draw everything
		self.placeHitHints()
		self.drawPolygons()
		self.placeBalls(anonymize=False)
		self.drawCue()
		return self.img # transform to cv2

	def getTrickshotImageCV2(self):
		return np.array(self.getTrickshotImage(self))[:,:,[2,1,0]]

	def getHitHints(self, d=100):
		height = int(1.05*d)

		img = Image.new(mode="RGBA", size=(d,height))
		draw = ImageDraw.Draw(img)

		# basic form
		draw.rectangle((0,d, d,height), fill="blue")
		draw.ellipse((0,0, d,d), fill="blue")

		# draw the actual hints (in the json: d.hit.x and .y)
		pos_x = self.d["hit"]["x"]*d
		pos_y = self.d["hit"]["y"]*d
		offset = int(d/20) # 2*offset = diameter of the marker
		draw.ellipse((pos_x-offset, pos_y-offset, pos_x+offset, pos_y+offset), fill="red")

		return img

	def placeHitHints(self):
		""" Generate and place the cue hints on the main image
		"""
		imgbot = self.getHitHints()
		w, h = imgbot.size
		self.img.paste(imgbot, (self.width//2-w//2,self.height-h), imgbot)

		imgtop = imgbot.transpose(Image.ROTATE_180)
		imgleft = imgbot.transpose(Image.ROTATE_270)
		imgright = imgbot.transpose(Image.ROTATE_90)
		self.img.paste(imgtop, (self.width//2-w//2,0), imgtop)
		self.img.paste(imgleft, (0,self.height//2-w//2), imgleft)
		self.img.paste(imgright, (self.width-h,self.height//2-w//2), imgright)


	def drawPolygons(self, linewidth=10):
		""" Directy draws all polygons from definition on the objects image
		"""
		rawAllPoly = self.d["polygons"]
		for color in rawAllPoly:
			# iterate over every polygon
			# key is the color
			#print(color)
			poly = rawAllPoly[color]
			coords = []
			for points in poly:
				coords.append((points["x"], points["y"]))
			#print(coords)
			self.draw.line(coords, width=linewidth, fill=color, joint="curve")

	def placeBalls(self, anonymize = False, diameter=57):
		""" Place all the ball from the definition onto the canvas

		:param anonymize: if true, every ball that is not white will be replaced by the same color, as their number is rarely important for trickshot
		:type anonymize: optional bool
		"""
		allBalls = self.d["balls"]
		for number in allBalls:
			# key is the number
			ball = allBalls[number]
			if anonymize and not number == "white":
				number = 17 # a dummy ball that does not really exist
			b = BilliardBall(number)

			offset = diameter // 2
			bImg = b.getImg(diameter) # currently hardcoded ball diameter
			
			xCorner, yCorner = int(ball["x"])-offset, int(ball["y"])-offset
			self.img.paste(bImg, (xCorner, yCorner), bImg)

	def drawCue(self, linewidth = 20, indicatorDistance = 180, indicatorLength = 200):
		allCue = self.d["cue"]
		start = tuple([allCue["start"]["x"], allCue["start"]["y"]])
		end = tuple([allCue["end"]["x"], allCue["end"]["y"]])
		self.draw.line([start, end], width=linewidth, fill="grey") # brown is literally invisible on the blue table cloth

		x, y = tuple([i-j for i,j in zip(start, end)])
		#a = indicatorDistance / np.sqrt(1-(x/y)**2) if y != 0 else 0
		a = indicatorDistance*y / np.sqrt(abs(y**2 - x**2))*np.sign(y-x) if x != y else indicatorDistance/np.sqrt(2)
		#b = indicatorDistance / np.sqrt(1-(y/x)**2) if x != 0 else 0
		b = indicatorDistance*x / np.sqrt(abs(x**2 - y**2))*np.sign(x-y) if x != y else -indicatorDistance/np.sqrt(2)
		end2 = (end[0]+a, end[1]+b)
		i = indicatorDistance*y / np.sqrt(y**2 + x**2)
		j = indicatorDistance*x / np.sqrt(y**2 + x**2)
		#j = indicatorLength / np.sqrt(1+(y/x)**2) if x != 0 else 0
		#print(a,b,j,i, x**2-y**2)
		start2 = (end2[0]+j, end2[1]+i)
		self.draw.line([start2, end2], width=linewidth, fill="grey")
		power = allCue["power"]
		indStart = (end2[0]+power*j, end2[1]+power*i)
		self.draw.line([indStart, end2], width=linewidth, fill="blue")

		

if __name__ == "__main__":
	#data = {"1": (400,300), "2": (654,76), "16": (1200,900), "14": (1800,400), "8": (700,300), "5": (588,833)}
	g = GameImage(phys=0.5, size=(2230,1115))
	g.instructionText("Platziere die **Kugeln** auf den Projektionen")
	g.nameTeamText("Mathis", "ISEM")
	#g.placeAllBalls(data)
	#g.drawArrow((100,100),(300,600))
	img = g.getImageCV2()
	#g.img.show()
	#trick = json.load(open("trickshots/number_one.json", "r"))

	#t = Trickshot(trick)
	#t.getCueHints()
	#t.drawPolygons()
	#t.placeBalls(anonymize=False)
	#t.placeHitHints()
	#t.drawCue()
	#t.img.show()
	#img = t.getTrickshotImage()
	cv2.imshow("Trickshot", img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()