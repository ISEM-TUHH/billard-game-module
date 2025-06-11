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

// select the mode -> make all other mode-sections invisible
document.getElementById("mode-selector-radios").addEventListener("click", function(e) {
  var val = document.querySelector('input[name="mode"]:checked').value;

  // update the backend -> beamer
  fetch("/kp2/selectmode", {
    method: "POST",
    headers: {
			"Accept": "application/json",
			"Content-Type": "application/json"
		},
    body: JSON.stringify({"mode": val})
  })

  for (let i of ["precision", "distance", "break","trickshot"]) {
    var vis = "none";
    if (i === val) {
      vis = "inline";
    }
    document.getElementById(i).style.display = vis;
  }

  if (val != "distance") {
    // when leaving distance mode, deselect the flag icon
    current_ball = "white"
  } else {
    current_ball = "marker-start"
  }

});


// select all radios and sort into names -> add event listener for each
const radios = document.querySelectorAll('input[type="radio"]');
console.log(radios);
radios.forEach(radio => {
    radio.addEventListener('change', () => {
        // Alle Labels zurücksetzen
        var name = radio.name;
        radios.forEach(r => {
            if (r.name === name) {
                const label = r.parentElement; // Das übergeordnete Label des Radio-Buttons
                label.style.backgroundColor = "#f1f1f1";
                label.style.border = "0px solid #00C1D4";
                label.classList.remove('active');
            }
        });
        // Aktives Label hinzufügen
        const activeLabel = radio.parentElement; // Das übergeordnete Label des ausgewählten Radio-Buttons
        activeLabel.style.backgroundColor = "#e0f7fa";
        activeLabel.style.border = "2px solid #00C1D4";
        activeLabel.classList.add('active');
    });
});

// Function to reset the manipulationFlag -> enable the loading of new coordinates from the camera module
document.getElementById("manipulation-flag").addEventListener("change", () => {
  var flag = document.getElementById("manipulation-flag");
  manipulatedFlag = flag.checked
})
function setManipulatedFlag(state) {
  var flag = document.getElementById("manipulation-flag");
  flag.checked = state;
  manipulatedFlag = state;
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
}, false)

// update the selected ball based on radio buttons
function update_cur_ball() {
  var val = document.querySelector('input[name="current_ball"]:checked').value;
  console.log(val);
  current_ball = val; // id of the now selected ball (or other object)
}
document.getElementById("ball-selector").addEventListener("click", function (e) {
  update_cur_ball();
})


// Get coordinates from the camera-module
async function getCameraCoordinates() {
  var data = [];
  if (!manipulatedFlag) { //only if we want new coordinates
    const response = await fetch("/camera/coords");
    var data = await response.json();
    coordinates = []; // reset coordinates
    // remove all old positions
    for (let b of balls) {
      b.style.display = "none";
    }
  } 
  //for (let b of data) {
  //  coordinates["ball-" + b.name] = b; // -> doing this in placing ball
    // place all balls on the image
  for (let b of data) {
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

// put an input with a given value into a storage div to have the form track it. CURRENTLY NOT USED -> just put the data directly into currentRound json, which gets send in the end.
function storeInput(storageID, fieldID, value) {
  storageDiv = document.getElementById(storageID);

}

// ----------------------------------- Precision logic -------------
// -> Kalibrierung: einfach eine Kugel auf das (projizierte) Bild legen und messen.
var refPoint = {x: 565, y: 557}; //reference point towards the distance is calculated


var debugObject = 0;

var precCheckboxes = document.getElementsByClassName("prec-checkbox");
for (let c of precCheckboxes) {
  c.addEventListener("change", () => {  
    if (!c.checked) {
      return; // if this is an uncheck event -> only measure data when checking the element
    }
    // get the label to update status
    var label = document.querySelector("label[for=" + c.id + "]");
    //var oldText = label.innerText;
    label.innerText = "Finding ball...";

    getCameraCoordinates()
      .then((r) => {

      // check how many balls have been placed
      var keys = Object.keys(coordinates)
      var length = keys.length;
      if (length === 0) {
        // no ball found, error
        alert("No ball found. Please retry or manually place a ball on the screen.");
        label.innerText = label.dataset.og;
        c.checked = false;
      } else if (length > 1) {
        // There must be only one ball found, otherwise manually delete
        alert("More than one ball found, please delete the other balls on the screen or remove them from the field and try again");
        label.innerText = label.dataset.og;
        c.checked = false;
      } else {
        // if there is only one ball, all is good
        console.log(keys, keys[0]);
        var ball = coordinates[keys[0]];
        
        // pythagoras and transform to real length (px to mm)
        var xr = pxToReal(ball.x);
        var yr = pxToReal(ball.y);
        var distance = Math.sqrt((xr - refPoint.x)**2 + (yr - refPoint.y)**2);
        label.innerText = Math.round(distance) + " mm";

        //soundJudge(distance, [15, 150, 450])

        currentRound[c.id] = distance;
      }
    })
  });
}



// ----------------------------------- Distance logic ----------------

// disable measurement of the distance when there where no collisions entered
var col_counters = document.getElementsByClassName("collision-counter");
for (let c of col_counters) {
  c.addEventListener("input", () => {
    // the box has to be directly next to it (element wise)
    c.nextElementSibling.disabled = !c.value;
  })
}

var distCheckboxes = document.getElementsByClassName("dist-checkbox");
for (let d of distCheckboxes) {
  d.addEventListener("change", ()=>{
    if (!d.checked) {
      return; // if this is an uncheck event -> only measure data when checking the element
    }
    var label = document.querySelector("label[for=" + d.id + "]");
    var nCol = document.getElementById(d.id + "c").value;

    var start = document.getElementById("marker-start");

    // determine the position of the starting point to be either on the left or the right half of the field.
    var leftDistanceStart = parseInt(start.style.left);
    var image = document.getElementById("livestream");
    var rect = image.getBoundingClientRect();
    var width = rect.width;

    //var oldText = label.innerText;
    label.innerText = "Finding ball...";

    getCameraCoordinates()
      .then((r) => {

        // place all balls on the image
        /*for (let b of r) {
          console.log(b);
          var x = b.x; // these are in real dimensions (mm)
          var y = b.y;
          var id = "ball-" + b.name;
          if (!manipulatedFlag) {
            placePointFromRealDim(x,y,id);
          }
        }*/

        // check how many balls have been placed
        var keys = Object.keys(coordinates)
        var length = keys.length;
        if (length === 0) {
          // no ball found, error
          alert("No ball found. Please retry or manually place a ball on the screen.");
          label.innerText = oldText;
          d.checked = false;
        } else if (length > 1) {
          // There must be only one ball found, otherwise manually delete
          alert("More than one ball found, please delete the other balls on the screen or remove them from the field and try again");
          label.innerText = label.dataset.og;
          d.checked = false;
        } else {
          var ball = coordinates[keys[0]];
          var finDist = 0;
          var offset = 0;
          if (leftDistanceStart < width/2) {
            // we are starting on the left side
            offset = leftDistanceStart;
            if (nCol%2 === 0) {
              finDist = ball.x;
            } else {
              finDist = width - ball.x
            }
          } else {
            // we are starting on the right side
            offset = width - leftDistanceStart;
            if (nCol%2 === 0) {
              finDist = width - ball.x;
            } else {
              finDist = ball.x;
            }
          }
          
          var distance = pxToReal(nCol*width - offset + finDist);

          label.innerText = Math.round(distance) + " mm";
          currentRound[d.id] = distance;
        }
      })


    
  })
}


// ----------------------- Logic for Break ----------------------
document.getElementById("break-button").addEventListener("change", ()=>{
  var self = document.getElementById("break-button")
  if (!self.checked) {
      return; // if this is an uncheck event -> only measure data when checking the element
    }
    var label = document.querySelector("label[for=" + self.id + "]");
    var oldText = label.innerText;
    label.innerText = "Counting balls...";

    getCameraCoordinates()
      .then((r) => {
        var nBalls = Object.keys(coordinates).length;
        var sunken = 16- nBalls;
        label.innerText = sunken + " balls were sunk";
        currentRound["break"] = sunken;
      })
})

// ------------------------- Logic for Trickshots -----------------
/*document.getElementById("trickshot-load").addEventListener("click", ()=> {
  fetch("/trickshots/load", {
          method: "post",
          headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({"id": "0"})
      }); // there is no answer to be processed :)
})*/

document.getElementById("trickshot-button").addEventListener("change", ()=>{
  var self = document.getElementById("trickshot-button")
  if (!self.checked) {
      return; // if this is an uncheck event -> only measure data when checking the element
    }
    var label = document.querySelector("label[for=" + self.id + "]");
    var oldText = label.innerText;
    label.innerText = "Counting balls...";

    getCameraCoordinates()
      .then((r) => {
        var nBalls = Object.keys(coordinates).length;
        var sunken = 3 - nBalls;
        label.innerText = sunken + " balls were sunk";
        currentRound["trickshot"] = sunken;
      })
})

// ------------------------- Logic for submission and reset -------
submitButton = document.getElementById("submit-button")
submitButton.addEventListener("click", ()=>{
  personName = document.getElementById("person-name").value;
  teamName =  document.getElementById("team-name").value;
  if ((teamName === "") || (personName === "")) {
    alert("No name/team has been entered!");
    return;
  }
  currentRound["team-name"] = teamName;
  currentRound["person-name"] = personName;
  console.log(currentRound); // for debugging
  if (Object.keys(currentRound).length != 10) {
    alert("Not every test was done!");
    return;
  }
  fetch("/kp2/enterround", {
    method: "POST",
    headers: {
			"Accept": "application/json",
			"Content-Type": "application/json"
		},
    body: JSON.stringify(currentRound)
  }).then((res) => res.json())
    .then((e) => {
      loadScores(e);

      document.getElementById("roundForm").reset();
      ogs = document.querySelectorAll("[data-og]")
      for (let inp of ogs) {
        inp.innerText = inp.dataset.og;
      }
      currentRound = {}
    })

});

//
function loadScores(e) {
  console.log(e);
  document.getElementById("submit-button").value = "Last score: " + e.score;

  document.getElementById("table-team").innerHTML = e["team-board"];
  document.getElementById("table-single").innerHTML = e["single-board"];
  
  updatePodium("team", e);
  updatePodium("single", e);
}

function updatePodium(prefix, res) {
  console.log(res, prefix)
	json = JSON.parse(res[prefix + "-podium"]);
	for (let i = 1; i < 4; i++) {
		el = document.getElementById(prefix + "-" + i)
		el.getElementsByTagName("p")[0].innerText = json["top"][i-1];
		el.getElementsByClassName("podium-rank")[0].innerHTML = json["mid"][i-1] + "<br/>(" + json["bot"][i-1] + ")";
	}
}

// on load load all scores and podiums
fetch("/kp2/enterround", {
  method: "POST",
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({"get": "true"})
}).then((e) => e.json())
  .then((res) => {
    loadScores(res);
  })
  

// every 55 seconds ping the server to say "hey there, I am still connected, please keep rendering frame :)"
// if there where no pings in 60s, frame generation stops.
setInterval(() => {fetch("http://134.28.20.53:5000/website/liveline");}, 55000) 