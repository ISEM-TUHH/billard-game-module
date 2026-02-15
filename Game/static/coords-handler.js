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

// Reload the livestream with a cache buster, in case the camera needed to be rebooted
original_livestream_source = document.getElementById("livestream").src // store the original value to add the cache buster to
function reloadStream() {
  document.getElementById("livestream").src = original_livestream_source + "?t=" + Date.now(); // this forces the browser to reload the 
}
document.getElementById("reload-livestream").addEventListener("click", reloadStream)


// --------------------- Functions for getting the coordinates

// Get coordinates from the camera-module
/*async function getCameraCoordinates() {
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
    //console.log(b);
    var x = b.x; // these are in real dimensions (mm)
    var y = b.y;
    var id = "ball-" + b.name;
    if (!manipulatedFlag) {
      placePointFromRealDim(x,y,id);
    }
  }

  return;// data; // Gibt die Koordinaten zurück
}*/

// returns coordinates as promise -> handle using .then((res) => {...})
function getCameraCoordinatesAsync() {
  //var data = [];
  if (!manipulatedFlag) { //only if we want new coordinates
    return fetch("/camera/coords").then((res) => res.json())
      .then((res) => {
        placeAllBalls(res);
        return res;
      });
  } else {
    return Promise.resolve();
  }
  //for (let b of data) {
  //  coordinates["ball-" + b.name] = b; // -> doing this in placing ball
    // place all balls on the image

}

// --------------------- Functions for placing/deleting balls ----------------------------
// place all balls from a backend provided json object (typical backend format)
// when manually calling this, it will not updated the beamer. This is done either before (in the Game Module side) or when manually adding single balls (see click event listener on livestream below).
function placeAllBalls(coords) {
  coordinates = {}; // reset global coordinate storage
  
  // remove all highlights from previously existing ball selector button labels
  document.querySelectorAll("#ball-selector .ball-exists").forEach((e) => {
    e.classList.remove("ball-exists")
  })

  // remove all old positions
  for (let b of balls) {
    b.style.display = "none";
  }

  // add new balls
  var keys = Object.keys(coords);
  for (let i of keys) {
    b = coords[i]
    //console.log(b);
    var x = b.x; // these are in real dimensions (mm)
    var y = b.y;
    var id = "ball-" + b.name;
    if (!manipulatedFlag) {
      placePointFromRealDim(x,y,id);
    }
  }
}

// Function to place the point at specific pixel coordinates
function placePoint(x, y, id, realBall = true) {
  // if realBall is false, this is another type of object placed on the image.
  const point = document.getElementById(id);
  point.style.display = "inline";
  //console.log(x, y)
  point.style.left = `${x}px`; // Set the left position
  point.style.top = `${y}px`; // Set the top position
  if (realBall) {
    coordinates[id] = {name: id, x: x, y: y, xr: pxToReal(x), yr: pxToReal(y)};
  } else {
    altCoordinates[id] = {name: id, x: x, y: y, xr: pxToReal(x), yr: pxToReal(y)};
  }
  //console.log(x,y)

  // highlight the corresponding label/input
  document.querySelector("#ball-selector input[value=" + id + "]").classList.add("ball-exists")
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

    document.querySelector("#ball-selector input[value=" + element.id + "]").classList.remove("ball-exists")
    console.log()
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
    /*var sendCoords = {}; 
    for (let c of Object.keys(coordinates)) {
        //console.log(c)
        var newName = c.replace("ball-","");
        var coord = coordinates[c];
        sendCoords[newName] = {"name": newName, "x": pxToReal(coord.x), "y": pxToReal(coord.y)};
        //console.log(newName, coord);
    }*/
    //console.log(sendCoords)
    var sendCoords = coordinatesBackend()
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


// take an image if something didnt work out with the camera AI, so the AI can be trained on it
/*saveImageButton = document.getElementById("ai-training-button");
saveImageButton.addEventListener("click", () => {
    fetch("/general/takeimage")
        .then((res) => res.json())
        .then((res) => {
            saveImageButton.value = "Click to save image. " + res["answer"];
        })
})*/

// Keep the camera alive
// setInterval(() => {fetch("http://134.28.20.53:5000/website/liveline");}, 55000) 

// select all radios and sort into names -> add event listener for each
const radios = document.querySelectorAll('#ball-selector input[type="radio"]');
radios.forEach(radio => {
    //console.log(radio.value)
    radio.addEventListener('click', () => {
        if (!radio.checked) {
          return // dont do something on inactive elements
        }
        // Alle Labels zurücksetzen
        //console.log(radio.parentElement)
        var name = radio.name;
        radios.forEach(r => {
            if (r.name === name) {
                const label = r.parentElement; // Das übergeordnete Label des Radio-Buttons
                label.classList.remove('active');
            }
        });
        // Aktives Label hinzufügen
        const activeLabel = radio.parentElement; // Das übergeordnete Label des ausgewählten Radio-Buttons
        activeLabel.classList.add('active');

        current_ball = radio.value;

    });
});

// Provide the coords in a format usable for the backend
function coordinatesBackend() {
  var sendCoords = {}; 
  for (let c of Object.keys(coordinates)) {
      //console.log(c)
      var newName = c.replace("ball-","");
      var coord = coordinates[c];
      sendCoords[newName] = {"name": newName, "x": pxToReal(coord.x), "y": pxToReal(coord.y)};
      //console.log(newName, coord);
  }
  return sendCoords
}

document.getElementById("toggle-inference").addEventListener("click", (e) => {
  fetch(camera_address + "/v1/togglequick")
  elmnt = document.getElementById("toggle-inference");
  if (elmnt.value === "Activate live inference") {
    elmnt.value = "Deactivate live inference";
  } else {
    elmnt.value = "Activate live inference";
  }
})

document.getElementById("stop-livestream").addEventListener("click", (e) => {
  fetch(camera_address + "/v1/stopgeneration");
})