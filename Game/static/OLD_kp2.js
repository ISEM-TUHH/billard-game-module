// The camera interface and some calibrations get set in coords-handler.js, which must be loaded on the page before this script.
currentRound = {"trickshot": 0, "break": 0};
oldMode = "none"; // track the current mode  
// select the mode -> make all other mode-sections invisible
//document.getElementById("mode-selector-radios").addEventListener("click", function(e) {
function updateKP2mode(e) {
  var val = e.value;//document.querySelector('input[name="mode"]:checked').value;
  if (val === oldMode) {
    return;
  }
  oldMode = val;
  // update the backend -> beamer
  /*fetch("/kp2/selectmode", {
    method: "POST",
    headers: {
			"Accept": "application/json",
			"Content-Type": "application/json"
		},
    body: JSON.stringify({"mode": val})
  });*/
  console.log(val)
  sender("/kp2/selectmode", {"mode": val})

  // make all the other invisible
  for (let i of ["precision", "distance", "break","trickshot"]) {
    var vis = "none";
    if (i === val) {
      vis = "inline";
    }
    document.getElementById(i).style.display = vis;
  }

  // delete all balls from the image
  for (let ball of balls) {
    ball.style.display = "none";
    delete coordinates[ball.id]; // deleting a key from an object in which it doesn't exist works :)
    delete altCoordinates[ball.id];
  }

  if (val != "distance") {
    // when leaving distance mode, deselect the flag icon
    current_ball = "white"
  } else {
    current_ball = "marker-start"
  }

}


// select all radios and sort into names -> add event listener for each
/*const radios = document.querySelectorAll('input[type="radio"]');
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
});*/

// ----------------------------------- Precision logic -------------
// -> Kalibrierung: einfach eine Kugel auf das (projizierte) Bild legen und messen.
var refPoint = {x: 565, y: 557}; //reference point towards the distance is calculated


var debugObject = 0;
/*
var precDifficultyRange = document.getElementById("prec-difficulty");
var precDifficulty = 1
precDifficultyRange.addEventListener("change", ()=>{
  var val = precDifficultyRange.value;
  sender("/kp2/cosmetics/precdif", {"difficulty": val});
  
  var label = document.querySelector("label[for=prec-difficulty]");
  var difName = ["Hard", "Regular", "Easy"][val];
  label.innerText = difName + ": x" + 5*(1+2*val);

  precDifficulty = val;
})
*/

/*
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
        label.innerText = Math.round(distance) + " mm (-" + 5*(1+2*precDifficulty)*Math.round(distance) + " points)";

        soundJudge(distance, [30, 120, 240, 360])
        sender("/kp2/cosmetics/value", {"mm": Math.round(distance)})
        setTimeout(() => {
          sender("/general/settext", {"text": ""})
        }, 10000);

        currentRound[c.id] = distance;
      }
    })
  });
}
*/


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

          label.innerText = Math.round(distance) + " mm (" + Math.round(distance) + " points)";
          currentRound[d.id] = distance;
          sender("/kp2/cosmetics/value", {"mm": Math.round(distance)})
          setTimeout(() => {
            sender("/general/settext", {"text": ""})
          }, 10000);
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
        label.innerText = sunken + " balls were sunk (" + 500*sunken + " points)";
        currentRound["break"] = sunken;

        soundJudge(nBalls, [13,14,15,15])
        sender("/kp2/cosmetics/value", {"n": Math.round(sunken)})
        setTimeout(() => {
          sender("/general/settext", {"text": ""})
        }, 10000);
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
    var oldText = label.innerText;currentRound
    label.innerText = "Counting balls...";

    getCameraCoordinates()
      .then((r) => {
        var nBalls = Object.keys(coordinates).length;
        var sunken = 3 - nBalls;
        label.innerText = sunken + " balls were sunk (" + 500*sunken + " points)";
        currentRound["trickshot"] = sunken;

        soundJudge(nBalls, [0,1,2,3,3])
        sender("/kp2/cosmetics/value", {"n": Math.round(sunken)})
        setTimeout(() => {
          sender("/general/settext", {"text": ""})
        }, 10000);
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

    })
    .then(() => {
      setTimeout(() => {
        sender("/general/settext", {"text": "Welcome to the final challenge!"});
      }, 15000)
    })
});

// reset the form
document.getElementById("roundForm").addEventListener("reset", () => {
    // the timeout of 100ms is a hack, as the firing order of events (form reset) is wrong otherwise
    setTimeout(() => {
    ogs = document.querySelectorAll("[data-og]");
    for (let inp of ogs) {
      inp.innerText = inp.dataset.og;
    }
    for (let c of col_counters) {
      c.dispatchEvent(new Event("input"))
    }
    currentRound = {"trickshot": 0, "break": 0};
    }, 100)
})


// Events happening onload
function loadScores(e) {
  //console.log(e);
  document.getElementById("submit-button").value = "Last score: " + e.score;

  document.getElementById("table-team").innerHTML = e["team-board"];
  document.getElementById("table-single").innerHTML = e["single-board"];
  
  updatePodium("team", e);
  updatePodium("single", e);
}

function updatePodium(prefix, res) {
  //console.log(res, prefix)
	json = JSON.parse(res[prefix + "-podium"]);
	for (let i = 1; i < 4; i++) {
		el = document.getElementById(prefix + "-" + i)
		el.getElementsByTagName("p")[0].innerText = json["top"][i-1];
		el.getElementsByClassName("podium-rank")[0].innerHTML = json["mid"][i-1] + "<br/>(" + json["bot"][i-1] + ")";
	}
}

// on load load all scores and podiums
/*fetch("/kp2/enterround", {
  method: "POST",
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({"get": "true"})
}).then((e) => e.json())
  .then((res) => {
    loadScores(res);
  })*/
  

// every 55 seconds ping the server to say "hey there, I am still connected, please keep rendering frame :)"
// if there where no pings in 60s, frame generation stops.
setInterval(() => {fetch("http://134.28.20.53:5000/website/liveline");}, 55000) 