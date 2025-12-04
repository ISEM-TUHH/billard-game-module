/*

    This file provides the kp2Controller function, which (compared to the vanillaController) manipulates the the gmode field (to kp2) and sets the current gamemode to the field "kp2_activity".

*/

function kp2Controller(jsonData, set_activity=true) {
    jsonData["gmode"] = "kp2";
    if (set_activity) {
        jsonData["kp2_activity"] = current_gamemode;
    }
    //console.log(jsonData)

    return fetch("/gamemodecontroller", {
            method: "POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        })
        .then((res) => res.json())
        .then((res) => {
            console.log("SEND:", jsonData, "RECEIVED:", res);

            if (res.hasOwnProperty("notification")) {
                tempAlert(res.notification, 6000);
            }
            if (res.hasOwnProperty("disable")) {
                for (var selector in res.disable) {
                    document.querySelectorAll(res.disable[selector]).forEach((e) => {
                        e.classList.add("deactivated")
                    })
                }
            }
            if (res.hasOwnProperty("enable")) {
                for (var selector in res.enable) {
                    document.querySelectorAll(res.enable[selector]).forEach((e) => {
                        e.classList.remove("deactivated")
                    })
                }
            }
            
            return res
        })
}

var controller = kp2Controller;

document.addEventListener("gamemode_updated", () => {
    //console.log("Initialising gamemode!")
    kp2Controller({"action": "show"})
})