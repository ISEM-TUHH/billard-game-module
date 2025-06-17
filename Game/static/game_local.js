player1 = "";
player2 = "";
currentPlayer = "";
groups = [] // gets populated by 


startGameButton = document.getElementById("game-start-button");
startGameButton.addEventListener("click", () => {
    var p1name = document.getElementById("person-name-1").value;
    var p1team = document.getElementById("team-name-1").value;
    var p2name = document.getElementById("person-name-2").value;
    var p2team = document.getElementById("team-name-2").value;

    player1 = p1name;
    player2 = p2name;

    sender("/game/startgame", {
        "p1": p1name,
        "t1": p1team,
        "p2": p2name,
        "t2": p2team
    })

    startGameButton.value = "Restart game"
})

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