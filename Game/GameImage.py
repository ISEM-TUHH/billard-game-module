import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json # for testing
import os
import cv2

class GameImage:
	"""Class to generate an image from different game modes and other information

	Each image starts with a black background, as this is "neutral" on a beamer.
	:param size: width x height of the image in pixels
	:type size: tuple<int>
	:param phys: how many meters are 1000 pixels? (equivalent to how many mm are 1 pixel)
	:type phys: float
	"""
	ballDiameter = 52.5 # diameter of a billiard ball (snooker) in mm

	def __init__(self, size=(1920, 1080), phys=1):
		self.img = Image.new(mode="RGB", size=size, color="#000000")
		#self.img = Image.new(mode="RGB", size=size, color="#50b12c")
		self.draw = ImageDraw.Draw(self.img)
		self.phys = phys
		self.w, self.h = size

	def getImageCV2(self):
		return np.array(self.img)[:,:,[2,1,0]] # shift from rgb to bgr

	def placeBall(self, pos, n, d=None):
		"""Place a ball on the canvas self.img based on its number

		:param pos: (x,y) center of the ball in mm from the top left
		:type pos: tuple<int>
		:param n: number of the ball
		:type n: int
		:param d: diameter of the ball in pixels, automatically determined to be accurate according to self.phys and 
		:type d: optional int
		"""
		if d == None:
			d = int(self.ballDiameter/self.phys)
		
		b = BilliardBall(n)
		bImg = b.getImg(d)
		x,y = tuple([int(i/self.phys - d//2) for i in pos])
		self.img.paste(bImg, (x,y), bImg) # second call for mask, so the corners dont get overwritten

	def placeAllBalls(self, data):
		"""Place all balls mentioned in the data dict on the canvas self.img

		:param data: dictionary matching the number of a ball (key) to its position (tuple x,y) from the upper left in mm. Can also just be the output of Camera.get_coords (.../v1/getcoords)
		:type data: dict<tuple<float>> or list<dict>
		"""
		for b in data:			
			if type(data) == list:
				rawN = b["name"]
				number = 8 if rawN=="eight" else (16 if rawN=="white" else int(rawN))
				x,y = b["x"],b["y"]
				self.placeBall((x,y),number)
				continue
			self.placeBall(data[b], int(b))

	def instructionText(self, text):
		"""Place text on top and flipped on the bottom of the image. Font size is chosen automatically.

		:param text: Text to be placed
		:type text: str
		"""
		fs = int(self.h/15)# if self.w/len(text) < # TODO: make it more dynamic 
		font = ImageFont.truetype("Roboto-Black.ttf", fs)

		img = Image.new(mode="RGBA", size=(self.w, int(1.5*fs)), color="#00000000")
		draw = ImageDraw.Draw(img)

		_,_, w, h = draw.textbbox((0,0), text, font = font)
		draw.text(((self.w-w)//2, 0), text, font=font, fill="white", background="#00000000")
		self.img.paste(img, (0,0), img)
		timg = img.transpose(Image.ROTATE_180)
		self.img.paste(timg, (0,int(self.h-1.5*fs)), timg)

	def drawArrow(self, start, end, color="white"):
		"""Draws an arrow from the start to the end (in mm)

		:param start, end: coordinates in mm (x,y)
		:type start, end: tuple<float>
		"""
		startP = tuple([int(i/self.phys) for i in start])
		endP = tuple([int(i/self.phys) for i in end])
		self.draw.line([startP,endP], fill=color, width=0)

	def addGameMode(self, supermode, game):
		""" Add an overlay to the image depending on the current game supermode.

		:param supermode: supermode of the game
		:type supermode: str
		:param game: Game Object calling this function
		:type game: Game Object 
		"""

		match supermode:
			case "kp2":
				kp2mode = game.kp2mode
				match kp2mode:
					case "precision":
						self.instructionText("Challenge: Precision")
						# draw a bullseye
						bullX, bullY = self.h//2, self.h//2
						r = 30 # radius of each ring
						print(bullX, bullY)
						for i in [4,2,0]:
							#topWhite = bullX - 2*(i+1)*r
							#bottomWhite = bullX + 2*(i+1)*r
							#topBlack = bullX - 2*i*r
							#bottomBlack = bullX + 2*i*r
							white = 2*(i+1)*r
							black = 2*i*r
							print(white, black)
							self.draw.ellipse((bullX-white, bullY-white, bullX+white, bullY+white), fill="#FFFFFF")
							self.draw.ellipse((bullX-black, bullY-black, bullX+black, bullY+black), fill="#000000")
						return
					case "results":
						# show results screen -> podium
						return
					case "base":
						self.instructionText("Select a challenge on the screen.")
						return
					case "trickshot":
						# Loading a trickshot already creates an image
						return
					case "break":
						self.instructionText("Challenge: Break")
					case "distance":
						self.instructionText("Challenge: Distance")


				


class BilliardBall:
	"""Class to store each Billiard Balls graphical attributes

	Each ball is initiated with its number with number 16 being the white ball. Number 1-7 are full, 8 is black, 9-15 are half.
	"""
	colors = ["#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#20201e","#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#d5d1c5","#fb48c4"] # the last entry is a dummy ball color (neon pink)

	def __init__(self, n):
		current_dir = os.path.dirname(__file__) # finding the Roboto-Black.ttf/navigating the dirs
		self.fontpath = current_dir + "/../Roboto-Black.ttf"

		if n == "white":
			n = 16
		elif n == "eight":
			n = 8
		n = int(n)
		self.indexNumber = n
		self.n = n if n != 16 and n != 17 else "" # empty string for the white and dummy ball
		self.type = "half" if (n>8 and n<16) else "full"
		if n == 8:
			self.type = "eight"
		elif n == 16:
			self.type = "white"

		self.color = self.colors[n-1]
		self.white = self.colors[-2]


	def getImg(self, d):
		"""Get the image of the ball with its number, half or full and color.
		
		:param d: Diameter of the returned image (side of square) in px
		:type d: int
		:return: PIL.Image object
		"""
		self.font = ImageFont.truetype(self.fontpath, d//3)
		
		img = Image.new(mode="RGBA", size=(d, d))
		draw = ImageDraw.Draw(img)

		draw.ellipse((0,0,d,d), fill=self.color, outline=self.color) # main color 
		if self.type == "half":
			draw.rectangle((0,0,d,d//5), fill=self.white, outline=self.white)
			draw.rectangle((0,4*d//5,d,d), fill=self.white, outline=self.white)
			draw.ellipse((-d//2,-d//2,3*d//2,3*d//2), outline="#00000000", width=d//2)

		if self.indexNumber != 17: # do not draw a white inner circle for dummy balls
			draw.ellipse((d//4,d//4, 3*d//4, 3*d//4), fill=self.white, outline=self.white) # inner white circle
		_,_, w, h = draw.textbbox((0,d//20), str(self.n), font = self.font)
		draw.text(((d-w)//2, (d-h)//2), str(self.n), font=self.font, fill="black")

		return img

class Trickshot: 
	"""Class to draw a trickshot with all its belongings onto the gameimage based on the json/dict defining the trickshot (see subfolder trickshots)

	:param definition: dict describing the trickshot, most likely loaded from a trickshots/*.json
	:type definition: dict
	:param size: the size of the image in mm = pixel. Sample down later.
	:type size: optional tuple (width, height)
	"""

	def __init__(self, definition, size=(2150, 1171)):
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
		self.placeBalls()
		self.drawCue()
		return np.array(self.img)[:,:,[2,1,0]] # transform to cv2

	def getHitHints(self, d=100):
		height = int(1.05*d)

		img = Image.new(mode="RGBA", size=(d,height))
		draw = ImageDraw.Draw(img)

		# basic form
		draw.rectangle((0,d, d,height), fill="white")
		draw.ellipse((0,0, d,d), fill="white")

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

	def placeBalls(self, anonymize = False, diameter=52):
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

	def drawCue(self, linewidth = 20):
		allCue = self.d["cue"]
		start = tuple([allCue["start"]["x"], allCue["start"]["y"]])
		end = tuple([allCue["end"]["x"], allCue["end"]["y"]])
		self.draw.line([start, end], width=linewidth, fill="grey") # brown is literally invisible on the blue table cloth

		

if __name__ == "__main__":
	#data = {"1": (400,300), "2": (654,76), "16": (1200,900), "14": (1800,400), "8": (700,300), "5": (588,833)}
	#g = GameImage(phys=0.5, size=(3840,2160))
	#g.instructionText("Platziere die Kugeln auf den Projektionen")
	#g.placeAllBalls(data)
	#g.drawArrow((100,100),(300,600))

	#g.img.show()
	trick = json.load(open("trickshots/number_one.json", "r"))

	t = Trickshot(trick)
	#t.getCueHints()
	#t.drawPolygons()
	#t.placeBalls(anonymize=False)
	#t.placeHitHints()
	#t.drawCue()
	#t.img.show()
	img = t.getTrickshotImage()
	cv2.imshow("Trickshot", img)
	cv2.waitKey(0)
	#cv2.destroyAllWindows()