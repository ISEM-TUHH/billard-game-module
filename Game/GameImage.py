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

	The image gets build using a `definition` (list). It consists of `parts` (dicts) which each can look like

	.. code:: python3

		{
			"type": "text",
			"text": "This is a text element, that will show up at the top and bottom of the image."
		}

	The available types and specific fields are listed in the documentation of each `part`. Each `part` gets assigned (if not defined) a reference (field `ref`), under which it can be changed using self.update_definition. 
	Some `part` types are static and will get reassigned instead of added with a different reference if they are input to GameImage.update_definition, unless a specific reference has been assigned.


	Attributes:
		definition: list of `parts`. The first element in the list will get drawn first, with later parts getting drawn above of it (rudimentary layering)
	
	Args:
		definition (list): `definition` list as specified in the GameImage class documentation
		size (tuple<int, int>): width, height of the goal image in pixels
		phys (float): how many meters are 1000 pixels? (equivalent to how many mm are 1 pixel). Not really in use.
		img_chache (dict): Images that can be used by using in their key as reference, e.g., in a part like `{"type": "text", "text": "Cached Image", "subimg": "key-from-img_cache"}` the `subimg` would be loaded from the file, url (QR-code) or PIL.Image object mapped to the key. Files get loaded upon init and the loaded cache gets copied when the object gets copied (GameImage.copy), minimizing file operations.

	Todo:
		- Move the GameImage system to its entirely own module/project as an abstraction layer on top of PIL itself.
		- Add GIF/video features. Maybe this would need the GameImage to be generated on the Beamer module itself.
		- Add GameImage slots to mimize compute needs
	"""

	def __init__(self, definition=[], size=(2230, 1115), phys=1, img_cache={
		"isem-logo": "static/images/ISEM-only.png", # small logo without text for subimg display
		"isem-logo-big": "static/images/isem_logo_big.png", # big logo with text for central display
		"feedback-form-qr": "https://www.youtube.com/watch?v=XfELJU1mRMg" # link to the feedback form
	}):
		self.img = Image.new(mode="RGBA", size=size, color="#000000ff")
		self.ballDiameter = 57 # diameter of a billiard ball (snooker) in mm
		#self.img = Image.new(mode="RGB", size=size, color="#50b12c")
		self.draw = ImageDraw.Draw(self.img)
		self.phys = phys
		self.w, self.h = size
		self.current_dir = os.path.dirname(__file__)

		self.FLAG_MODIFIED = False # track if the image has been updated since the last redraw

		self.fontpath = os.path.join(self.current_dir, "../fonts/Minecraft-Regular.otf") 

		# list of graphical parts that can only exist max once.
		self.static = ["balls", "text", "team", "break", "central_image"] #: These `part` types are static and will get reassigned instead of added with a different reference if they are input to GameImage.update_definition, unless a specific reference has been assigned.

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
		"""Generate a copy of the image.

		:return: copy of this object
		:rtype: GameImage
		"""
		return GameImage(definition=self.definition.copy(), img_cache=self.img_cache)

	def draw_from_dict(self, definition, draw=True):
		"""Draw the image (GameImage.img) from a list<dictionary> specifying the subparts. Execution flow is from top to bottom, so lower (later) parts are on a higher image layer.

		Args:
			definition (list): `definition` list as specified in the class documentation. If an element of the list is `None`, all `parts` in the passed `definition` list will be treated using GameImage.update_definition.
			draw (bool, optional): Choose if the image should directly be rendered ore only the definition updated. The improvement over just reassigning GameImage.definition is the creation of references.

		Returns:
			list: `definition` list with assigned references (field `ref`, only for `parts` that had none before)

		Todo:
			- Change match-case statement to dict mapping type to methods
		"""
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
		"""Draw the GameImage.img again using the definition already available as GameImage.definition
		"""
		self.draw_from_dict(self.definition)

	def update_definition(self, val, ref=None, subfield=None, new_instance=False, layer=-1, remove=False):
		"""Adds a new part to the image definition or update an existing part.
		
		If ref is None or no current entry has the same ref, actually adds a new part. Otherwise it finds a part with the same reference (either passed as argument `ref` or in `val` as field `ref`). If subfield != None, looks for the key in a part with given ref and only updates that.

		Args:
			val (dict, any): If `subfield is None`, this gets treated as an entire `part`, otherwise it is the new value of the field `subfield` in the part with reference `ref`. If it has the field `"remove": True` and a set `ref` field, the part with that `ref` will be removed, calls GameImage.rm_definition.
			ref (str, optional): reference of a part to update. Defaults to None.
			subfield (str, optional): Key of the field in an existing part to update. Defaults to None.
			new_instance (bool, optional): Unused. Defaults to False.
			layer (int, optional): At what layer should this be inserted? Defaults to -1 for the last element (highest layer)
			remove (bool, optional): Remove the element that has the given `ref`, calls GameImage.rm_definition. Defaults to False.
		"""
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
		"""Specific wrapper for GameImage.update_definition to only update the text part"""
		self.update_definition(text, ref="text", subfield="text")

	def getImageCV2(self):
		"""Exports the GameImage.img (PIL.Image) as a RGB cv2 compatible np.ndarray

		Returns:
			np.ndarray: RGB image
		"""
		if self.FLAG_MODIFIED:
			self.redraw()
		return np.array(self.img)[:,:,[2,1,0]] # shift from rgb to bgr

	def line(self, c1, c2, color="white", width=3): # TODO: add different coordinate formats
		"""Draws a line between two points.

		Part description: `{"type": "line", "c1": [123, 123], "c2": {"x": 123, "y": 123}, "color": "#123456", "width": 5}`

		Args:
			c1 (dict, iterable): Coordinates of one end (e.g. as {"x": 12, "y": 34})
			c2 (dict, iterable): Coordinates of the other end
			color (str, optional): Color of the line, hexcode (#112233) or keyword. Defaults to "white".
			width (int, optional): Width of the line in px. Defaults to 3.
		"""
		if type(c1) is dict:
			c1 = (c1["x"], c1["y"])
			c2 = (c2["x"], c2["y"])
		self.draw.line([c1, c2], fill=color, width=width)

	def rectangle(self, c1, c2, outline="white", width=5, fill=None):
		"""Draws a rectangle between two points as opposite corners.

		Part description: `{"type": "rectangle", "c1": [123, 123], "c2": {"x": 123, "y": 123}, "outline": "#123456", "width": 5, "fill": None}`

		Args:
			c1 (iterable): Coordinates of one end (x, y)
			c2 (iterable): Coordinates of the other end
			outline (str, optional): Color of the line, hexcode (#112233) or keyword. Defaults to "white".
			width (int, optional): Width of the border in px. Defaults to 5.
			fill (str, optional): Color of the line, hexcode (#112233) or keyword. Defaults to None.
		"""
		self.draw.rectangle([c1, c2], outline=outline, width=width, fill=fill)

	def bullseye(self, center=None, r=30):
		"""Draws a bullseye around the center with 3 rings, with each ring having a width of r

		Part description: `{"type": "bullseye", "center": [123, 123], "r": 30}`

		Args:
			center (list-like, optional): Center of the bullseye. Defaults to None.
			r (int, optional): Thickness of each of the three rings. Defaults to 30.
		
		Todo:
			- change r to be the total radius not this weird ring-thickness.
			- ideally also add a number of rings parameter
		"""

		if center is None:
			bullX, bullY = self.w//4, self.h//2
		else:
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
		"""Draws and arrow by specifying the bottom point. bottom as np.array([x, y]), orientation in degrees relative to +x-axis in mathemtical positive direction

		Part description: `{"type": "arrow_bottom", "bottom": [123, 123], "orientation": 3.14159, "length": 50, "head_width": 50, "line_width": 10, "color": "#123456"}`

		Args:
			bottom (list-like): Starting point of the arrow (not the head)
			orientation (float): Orientation in radians from the +x axis (pi/2 would be vertical, 0 to the right)
			length (float): Length of the arrow
			head_width (int, optional): Width of the arrow head. Defaults to 50.
			line_width (int, optional): Thickness of the line. Defaults to 10.
			color (str, optional): Color as keyword or hex. Defaults to "white".
		"""

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
		self.draw.line(arrow, width=line_width, fill=color, joint="curve")
		#self.draw.circle(arrow[1], radius=line_width//2, fill=color, width=0)

	def arrow(self, start, end, offset=0, **kwargs):
		"""Arrow pointing from start to end

		Part description: `{"type": "arrow", "start": [123, 123], "end": {"x": 123, "y": 123}, "offset": 35}` + optional fields of GameImage.arrow_bottom

		Args:
			start (list-like): Starting point (bottom)
			end (list-like): End point (head)
			offset (int, optional): Distance from the bottom and head to where the arrow actually start. Useful for pointing arrows between billard balls. Defaults to 0.
		"""
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
		bImg = b.getImg(d, square=True)
		x,y = tuple([int(float(i)/self.phys - d//2) for i in pos])
		self.img.paste(bImg, (x,y), bImg) # second call for mask, so the corners dont get overwritten

	def placeAllBalls(self, coords):
		"""Place all balls mentioned in the data dict on the canvas self.img

		Part description: `{"type": "line", "coords": [coords dict]}`

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

		data = coords
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

	def drawBallConnections(self, shots, offset=35, line_width=6, head_width=12, **kwargs):
		""" Takes the output of GameEngine.getShots and draws arrows accordingly. Each shot path gets the color of the ball it is supposed to sink (except for the black ball, which would not be visible)

		Part description: `{"type": "possible_shots", "shots": [shots dict]}` + optional fields from GameImage.arrow and GameImage.arrow_bottom

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

		Part description: `{"type": "text", "text": "Hello World", "subimg": "isem-logo"}`
		
		Images can be passed as PIL image, path or GameImage.img_cache key. Text can be emphasized by encapsulating in **...**

		Todo:
			- Finalize emphasised formatting (color blind friendly). Maybe generalize text rendering?

		:param text: Text to be placed
		:type text: str
		:param subimg: Image to be placed directly under the text
		:type subimg: optional PIL Image or relative path to image 
		"""		
		fs = int(self.h/15)# if self.w/len(text) < # TODO: make it more dynamic 
		font = ImageFont.truetype(self.fontpath, fs)

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

		Part description: `{"type": "team", "name": "Jon Doe", "team": "ISEM"}

		Args:
			name (str): Player name
			team (str): Team name
		"""
		fs = int(self.h//25)
		font = ImageFont.truetype(self.fontpath, fs)
		img = Image.new(mode="RGBA", size=(self.h, int(1.5*fs)), color="#00000000")
		draw = ImageDraw.Draw(img)

		_,_, wn,hn = draw.textbbox((0,0), name, font=font)
		_,_, wt,ht = draw.textbbox((0,0), team, font=font)
		draw.text((self.h//4 - wn//2, 0), name, font=font, fill="white", background="#00000000")
		draw.text((3*self.h//4 - wt//2, 0), team, font=font, fill="white", background="#00000000")

		timg = img.transpose(Image.ROTATE_90)
		self.img.paste(timg, (self.w - int(1.5*fs),0), timg)

	def drawBreak(self, ball=True):
		""" Draw the basic triangle for a break and optionally the white ball for break

		Part description: `{"type": "break", "ball": True}
		
		Args:
			ball (bool): Should the starting point of the break be drawn?

		Todo:
			- verify the position of the starting point and break triangle

		"""
		center = self.h//2
		offTop = 160
		offFront = 290
		self.draw.polygon([(center, center-offTop),(center+offFront, center), (center, center+offTop)], fill=(255,255,0))
		if ball:
			self.placeBall((4*self.w//5, center), "white")

	def centralImage(self, img):
		"""Draw an (PIL) image in the center of the image. Currently the image gets inserted at its original size, so resizing must be done before.

		Part description: `{"type": "central-image", "img": "isem-logo-big"}

		Args:
			img (path, PIL.Image, GameImage.img_cache key): Image the gets placed in the center

		Todo:
			- add sizing options
		"""
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


				


class BilliardBall:
	"""Class to store each Billiard Balls graphical attributes

	Each ball is initiated with its number with number 16 being the white ball. Number 1-7 are full/solid, 8 is black/eight, 9-15 are half/striped.

	Special balls are dummy (17), correct (18) and incorrect (19).

	Attributes:
		colors (list): list of all colors (hexcodes strings) ordered 


	Args:
		n (int, str): name of the ball
	"""
	white = "#d5d1c5"
	colors = ["#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#20201e","#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517", white, "#058aff", "#69f902", "#f9021f"]#"#fb48c4"] # the last entry is a dummy ball color (neon pink)
	unique_map = {
		"eight": 8,
		"black": 8,
		"white": 16,
		"dummy": 17,
		"correct": 18,
		"incorrect": 19
	}

	def __init__(self, n):


		current_dir = os.path.dirname(__file__) # finding the Roboto-Black.ttf/navigating the dirs
		#self.fontpath = current_dir + "/../Roboto-Black.ttf"
		self.fontpath = current_dir + "/../fonts/Minecraft-Regular.otf"

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
		""" Get the hexcode of the color of the ball based on the n value (number or str keys) 
		
		Args:
			n (int, str): number or name of the ball
		"""
		n = int(n) if n not in cls.unique_map.keys() else cls.unique_map[n]
		return cls.colors[n-1]

	@classmethod
	def getGroup(cls, n):
		""" Get the group of the color of the ball based on the n value (number or str keys). Everything over 16 is dummy.
		
		Args:
			n (int, str): number or name of the ball
		"""
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

	def getImg(self, d, square=False):
		"""Get the image of the ball with its number, half or full and color.
		
		:param d: Diameter of the returned image (side of square) in px
		:type d: int
		:param square: should the ball image be generated as a square? This is useful when you are simultaneously displaying ball positions on the beamer and infering ball positions using the camera module. Displayed square balls are less likely to get picket up as balls compared to circular balls.
		:type square: optional, bool
		:return: PIL.Image object
		"""
		self.font = ImageFont.truetype(self.fontpath, d//3)
		
		img = Image.new(mode="RGBA", size=(d+1, d+1))
		draw = ImageDraw.Draw(img)

		if square:
			form = lambda points, fill=None, outline=0, width=None: draw.rectangle(points, fill=fill, outline=outline)
		else:
			form = lambda points, fill=None, outline=0, width=0: draw.ellipse(points, fill=fill, outline=outline, width=width)

		#draw.ellipse((0,0,d,d), fill=self.color, outline=self.color) # main color 
		form((0,0,d,d), fill=self.color, outline=self.color)
		if self.type == "half":
			draw.rectangle((0,0,d,d//5), fill=self.white, outline=self.white)
			draw.rectangle((0,4*d//5,d,d), fill=self.white, outline=self.white)
			form((-d//2,-d//2,3*d//2,3*d//2), outline="#00000000", width=d//2)
			#draw.ellipse((-d//2,-d//2,3*d//2,3*d//2), outline="#00000000", width=d//2)

		if self.indexNumber < 17: # do not draw a white inner circle for dummy/special balls
			#draw.ellipse((d//4,d//4, 3*d//4, 3*d//4), fill=self.white, outline=self.white) # inner white circle
			form((d//4,d//4, 3*d//4, 3*d//4), fill=self.white, outline=self.white)
			_,_, w, h = draw.textbbox((0,d//20), str(self.n), font = self.font)
			draw.text(((d-w)//2, (d-h)//2), str(self.n), font=self.font, fill="black")
		#draw.ellipse((0,0,d,d), outline=self.white) # draw a white circle around it (good for balls with weak colors)
		form((0,0,d,d), outline=self.white)

		return img

class Trickshot: 
	"""Deprecated.

	The trickshot challenge this belongs to has been superseeded by the Longst Break challenge, since that can be played more reliably.
	
	Class to draw a trickshot with all its belongings onto the gameimage based on the json/dict defining the trickshot (see subfolder trickshots).

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
		"""Hit hints are hints on where to hit the ball (shown from the back) to get a desired trajectory like backspin.

		Information on the hit hint gets pulled from Trickshot.d["hit"]["x" and "y"] (d = definition from init).

		Args:
			d (int, optional): Diameter of the ball that should be displayed. Defaults to 100.

		Returns:
			_type_: _description_
		"""
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

		The hit hint (generated by Trickshot.getHitHints) gets placed four times, on each edge once.
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
			bImg = b.getImg(diameter, square=True) # currently hardcoded ball diameter
			
			xCorner, yCorner = int(ball["x"])-offset, int(ball["y"])-offset
			self.img.paste(bImg, (xCorner, yCorner), bImg)

	def drawCue(self, linewidth = 20, indicatorDistance = 180, indicatorLength = 200):
		"""Draws the suggested position for the cueue including an indicator of the power level of the hit.

		Args:
			linewidth (int, optional): Width of the cue and indicator. Defaults to 20.
			indicatorDistance (int, optional): Distance from the indicator to the cueue. Defaults to 180.
			indicatorLength (int, optional): Length of the indicator. Defaults to 200.
		"""
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

