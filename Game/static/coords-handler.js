/*

    This file implements common functions for interaction with the coodinates of the balls / livestream
    Pull coords from the camera (via game module), display them, provide them to the entire JS of the site, provide corrections and send them to the game module

*/

// CHANGE THE TABLE MEASUREMENTS HERE
longsideTable = 2230; //mm
shortsideTable = 1115; //mm 
//1171, 2150

var manipulatedFlag = false; // tracks wether the coordinates have been manipulated. If true, they will not be replaced by camera calculated coordinates
var coordinates = {} /* storing manually placed balls with the structure: 
  ball-1: {
    name: ball-1,
    x: 450,
    y: 376
  }, 
  ball-2: ...
*/
var altCoordinates = {}; // storage for other objects placed on the image than balls. Same structure.
var currentRound = {};

// --------------------- Functions for getting the coordinates

// Get coordinates from the camera-module
async function getCameraCoordinates() {
  var data = [];
  if (!manipulatedFlag) { //only if we want new coordinates
    const response = await fetch("/camera/coords");
    var data = await response.json();
    coordinates = {}; // reset coordinates
    // remove all old positions
    for (let b of balls) {
      b.style.display = "none";
    }
  } 
  //for (let b of data) {
  //  coordinates["ball-" + b.name] = b; // -> doing this in placing ball
    // place all balls on the image
  var keys = Object.keys(data);
  for (let i of keys) {
    b = data[i]
    console.log(b);
    var x = b.x; // these are in real dimensions (mm)
    var y = b.y;
    var id = "ball-" + b.name;
    if (!manipulatedFlag) {
      placePointFromRealDim(x,y,id);
    }
  }

  return;// data; // Gibt die Koordinaten zurück
}

// --------------------- Functions for placing/deleting balls ----------------------------

// Function to place the point at specific pixel coordinates
function placePoint(x, y, id, realBall = true) {
  // if realBall is false, this is another type of object placed on the image.
  const point = document.getElementById(id);
  point.style.display = "inline";
  //console.log(x, y)
  point.style.left = `${x}px`; // Set the left position
  point.style.top = `${y}px`; // Set the top position
  if (realBall) {
    coordinates[id] = {name: id, x: x, y: y};
  } else {
    altCoordinates[id] = {name: id, x: x, y: y};
  }
  console.log(x,y)
}

function placePointFromRealDim(xr, yr, id) {
  //var rect = e.target.getBoundingClientRect();
  var image = document.getElementById("livestream");
  var rect = image.getBoundingClientRect();
  var x = xr/longsideTable*rect.width;
  var y = yr/shortsideTable*rect.height;
  placePoint(x, y, id);
  
}

function pxToReal(x) {
  var image = document.getElementById("livestream");
  var rect = image.getBoundingClientRect();

  // check the right scaling -> these two should be nearly equal
  // console.log(longsideTable/rect.width, shortsideTable/rect.height);
  return x/rect.width*longsideTable;
}

// Remove a ball when clicking on it
var balls = document.getElementsByClassName("ball");
for (let element of balls) {
  element.addEventListener("click", function(e) {
    element.style.display = "none";
    delete coordinates[element.id];
    if (element.id != "marker-start") {
      setManipulatedFlag(true); // deleting the marker-start (for distance) does not count as manipulating the real coordinates 
    }

    sendCorrectedCoords();
  })
}; 

// Listen to click event on the livestream and place the point accordingly
var current_ball = "ball-1";
document.getElementById("livestream").addEventListener("click", function(e) {
  //console.log(e);
  
  var rect = e.target.getBoundingClientRect();
  var image = document.getElementById("livestream");

  var isBall = (current_ball != "marker-start");
  placePoint(e.x - rect.left, e.y - rect.top, current_ball, realBall = isBall);
  
  // convert to image coordinates
  //imX = (e.x - rect.left)/rect.width * image.naturalWidth;
  //imY = (e.y - rect.top)/rect.height * image.naturalHeight;
  //console.log(imX, imY, rect.height, rect.width);
  if (isBall) { // like when deleting the marker-start, placing it should not be counted as manipulation
    setManipulatedFlag(true);
  }

  sendCorrectedCoords();

}, false)

// --------------------- Functions for handling manipulation ----------------

function sendCorrectedCoords() {
    //console.log(coordinates);
    var sendCoords = {}; 
    for (let c of Object.keys(coordinates)) {
        //console.log(c)
        var newName = c.replace("ball-","");
        var coord = coordinates[c];
        sendCoords[newName] = {"name": newName, "x": pxToReal(coord.x), "y": pxToReal(coord.y)};
        //console.log(newName, coord);
    }
    //console.log(sendCoords)
    sender("/general/correctedcoords", sendCoords);
}

document.getElementById("manipulation-flag").addEventListener("change", () => {
  var flag = document.getElementById("manipulation-flag");
  manipulatedFlag = flag.checked
})
function setManipulatedFlag(state) {
  var flag = document.getElementById("manipulation-flag");
  flag.checked = state;
  manipulatedFlag = state;
}

// update the selected ball based on radio buttons
function update_cur_ball() {
  var val = document.querySelector('input[name="current_ball"]:checked').value;
  console.log(val);
  current_ball = val; // id of the now selected ball (or other object)
}
document.getElementById("ball-selector").addEventListener("click", function (e) {
  update_cur_ball();
})


// take an image if something didnt work out with the camera AI, so the AI can be trained on it
saveImageButton = document.getElementById("ai-training-button");
saveImageButton.addEventListener("click", () => {
    fetch("/general/takeimage")
        .then((res) => res.json())
        .then((res) => {
            saveImageButton.value = "Click to save image. " + res["answer"];
        })
})

// Keep the camera alive
setInterval(() => {fetch("http://134.28.20.53:5000/website/liveline");}, 55000) 