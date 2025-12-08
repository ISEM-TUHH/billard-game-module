/*

    This file provides functions for updating the scoreboard (history) based on the hist field in the returned json data upon finishing a game.

These methods are included in the base.html

*/

function update_scoreboard(histdata) {
    // updating the single table
    var singles = document.getElementById("table-single");
    var sd = histdata["single_table"];
    var text = "" //"Individual<table><thead><tr><th></th><th>Player</th><th>Team</th><th>Score</th></tr></thead><tbody></tbody>";
    var coloring = "";
    for (var i = 0; i < sd.length; i++) {

        // if a new row has been added: highlight the row in ISEM red (accent 6)
        // remove the highlight after 7s
        if (histdata.hasOwnProperty("single_new_index") && histdata["single_new_index"] === i) {
            coloring = ' class="new-history-entry" style="background-color: #ff4f4f"'; // id="new-single-result"'
            setTimeout(() => {
                //document.getElementById("new-single-result").style = "";
                //document.getElementById("new-single-result").id = "";
                //console.log("Removing class from", singles.querySelector(".new-history-entry"));
                singles.querySelector(".new-history-entry").style["background-color"] = "";
                singles.querySelector(".new-history-entry").classList.remove("new-history-entry");
            }, 7000)
        } else {
            coloring = "";
        }
        text += "<tr" + coloring + ">";
        for (let j = 0; j < sd[i].length; j++) {
            text += "<td>" + sd[i][j] + "</td>";
        }
        text += "</tr>";

        //text += "<tr" + coloring + "><td>" + sd[i][0] + "</td><td>" + sd[i][1] + "</td><td>" + sd[i][2] + "</td><td>" + sd[i][3] + "</td><td>" + sd[i][4] + "</td></tr>";
    }
    //console.log("HISTORY:", histdata, "text:", text)
    singles.getElementsByTagName("tbody")[0].innerHTML = text

    // updating the teams table
    var teams = document.getElementById("table-team");
    var td = histdata["team_table"];
    var text = "Teams<table><thead><tr><th></th><th>Team</th><th>Score</th></tr></thead><tbody></tbody>";
    for (var i = 0; i < td.length; i++) {
        text += "<tr><td>" + td[i][1] + "</td><td>" + td[i][0] + "</td></tr>";
    }
    text += "</tbody></table>";
    teams.innerHTML = text
}

window.addEventListener("update_scoreboard", (e) => {
    //console.log(e);
    update_scoreboard(e.detail);
})