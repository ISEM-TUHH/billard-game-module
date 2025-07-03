players = {}
currentPlayer = "";
groups = [] // gets populated by 
start_precision = {}

startGameButton = document.getElementById("game-start-button");
startGameButton.addEventListener("click", () => {
    var p1name = document.getElementById("person-name-1").value;
    var p1team = document.getElementById("team-name-1").value;
    var p2name = document.getElementById("person-name-2").value;
    var p2team = document.getElementById("team-name-2").value;

    players = {
        player1: p1name,
        player2: p2name
    }

    sender("/game/startgame", {
        "p1": p1name,
        "t1": p1team,
        "p2": p2name,
        "t2": p2team
    })
    
    document.querySelector("label[for=prec1-button]").innerHTML = p1name + " try";
    document.querySelector("label[for=prec2-button]").innerHTML = p2name + " try";

    startGameButton.value = "Restart game"
})

precCheckboxes = document.getElementsByClassName("prec-checkbox")
for (let c of precCheckboxes) {
    c.addEventListener("change", ()=>{
        // get the label to update status
        var label = document.querySelector("label[for=" + c.id + "]");
        //var oldText = label.innerText;
        label.innerText = "Finding ball...";
        getCameraCoordinates()
            .then((r) => {

            // check how many balls have been placed
            var keys = Object.keys(coordinates)
            var length = keys.length;
            console.log(r);
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
                /*start_precision[c.value] = coordinates
                console.log(coordinates)
                p1 = start_precision.player1;
                p2 = start_precision.player2;*/
                p1 = coordinates[keys[0]]
                p1.x = p1.xr;
                p1.y = p1.yr;
                player = c.value
                json = {}
                json[player] = p1
                //p2.x = p2.xr;
                //p2.y = p2.yr;
                fetch("/game/determinestart", {
                    method: "POST",
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(json)
                }).then((r) => r.json())
                    .then((r) => {
                        label.innerText = players[player] + ": " + r.distance + " mm";
                    })

            }
        })
    })
};


inspectButton = document.getElementById("inspect-button")
inspectButton.addEventListener("click", () => {
    getCameraCoordinates()
})

submitButton = document.getElementById("submit-button")
submitButton.addEventListener("click", () => {
    fetch("/game/enterround")
        .then((res) => res.json())
        .then((res) => {
            currentPlayer = res["current-player"];
            remaining = res["remaining-balls"];
            groups = res["groups"];

        })
})