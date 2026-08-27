/*

    Provides functions to submit the kp2 round. This includes a reset of the scoreboard.

*/

document.getElementById("submit-button").addEventListener("click", (e) => {
    // First of all, check if the configuration boxes session-info and user-info have all set inputs
    var userinfo = getAllInputValues(document.getElementById("user-info"));
    var sessioninfo = getAllInputValues(document.getElementById("session-info"));

    if (!checkAllSet(userinfo)) {
        // not all user info are set
        tempAlert("Set user information to continue", 5000);
        return;
    }
    if (!checkAllSet(sessioninfo)) {
        // not all user info are set
        tempAlert("Set session information to continue", 5000);
        return;
    }

    send_setting(document.getElementById("user-info"), print=false, meta=true);

    send_setting(document.getElementById("session-info"), print=false, meta=true);

    kp2Controller({"kp2_activity": "hand_in", "action": "game"}, set_activity=false)
        .then((res) => {
            var ev = new CustomEvent("update_scoreboard", {detail: res.history});
            //console.log("HISTORY EVENT", ev, ev.detail);
            window.dispatchEvent(ev);

            // also build up a small table with the overview
            var table = res.overview;
            var text_head = "<table><thead><tr>";
            var text_body = "</tr></thead><tbody><tr>";
            for (var k in table) {
                text_head += "<th>" + k + "</th>";
                text_body += "<td>" + table[k] + "</td>";
            }
            document.getElementById("result-overview").innerHTML = text_head + text_body + "</tr></tbody></table>"
            + "<a href='/gamemode_report/kp2/" + res.history.timestamp + "'>Download report</a>";
        })
})