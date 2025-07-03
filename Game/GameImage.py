import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json # for testing
import os
import cv2

from .GameEngine import GameEngine

class GameImage:
	"""Class to generate an image from different game modes and other information

	Each image starts with a black background, as this is "neutral" on a beamer.
	:param size: width x height of the image in pixels
	:type size: tuple<int>
	:param phys: how many meters are 1000 pixels? (equivalent to how many mm are 1 pixel)
	:type phys: float
	"""
	ballDiameter = 57 # diameter of a billiard ball (snooker) in mm

	def __init__(self, size=(2230, 1115), phys=1):
		self.img = Image.new(mode="RGB", size=size, color="#000000")
		#self.img = Image.new(mode="RGB", size=size, color="#50b12c")
		self.draw = ImageDraw.Draw(self.img)
		self.phys = phys
		self.w, self.h = size
		self.current_dir = os.path.dirname(__file__)

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
		x,y = tuple([int(float(i)/self.phys - d//2) for i in pos])
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
			elif "x" in data[b].keys():
				pos = (data[b]["x"], data[b]["y"])
				self.placeBall(pos, b)
			else:
				#print(b)
				self.placeBall(data[b], int(b))

	def drawBallConnections(self, data, drawBalls=True):
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

				self.draw.line([(xw,yw),(xwe,ywe)], fill="grey", width=4)
				self.draw.line([(x,y),(xh,yh)], fill="grey", width=4)

		if drawBalls:
			self.placeAllBalls(data2)

	

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

		_,_, w, h = draw.textbbox((0,0), text, font = font)
		draw.text(((self.w-w)//2, 0), text, font=font, fill="white", background="#00000000")

		if subimg != None:
			size = self.w, int(1.5*fs)
			if type(subimg) == str:
				# load from file
				subimg = Image.open(self.current_dir + "/" + subimg)
			subimg.thumbnail(size, Image.Resampling.LANCZOS)
			w,h = subimg.size
			img.paste(subimg, ((self.w-w)//2, int(1.5*fs)))

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
		""" Draw the basic triangle and optionally the white ball for break """
		center = self.h//2
		offTop = 160
		offFront = 290
		self.draw.polygon([(center, center-offTop),(center+offFront, center), (center, center+offTop)], fill=(255,255,0))
		if ball:
			self.placeBall((4*self.w//5, center), "white")

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
				self.img.paste(logo, (self.w//2-350, self.h//2-350//2))
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
	"""
	colors = ["#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#20201e","#f7d339","#1f419f","#e44c23","#5d1c8f","#f89348","#17953b","#c71517","#d5d1c5","#2cff05"]#"#fb48c4"] # the last entry is a dummy ball color (neon pink)

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
		
		img = Image.new(mode="RGBA", size=(d+1, d+1))
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
	g.instructionText("Platziere die Kugeln auf den Projektionen")
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