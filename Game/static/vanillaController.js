/*

    This file provides the vanilla controller, which just adds the gamemode and sends the data directly to the gamemodecontroller endpoint of the game module

*/

function vanillaController(jsonData, set_activity=false) {
    // set_activity argument is only for compatability reasons, not used
    jsonData["gmode"] = current_gamemode

    fetch("/gamemodecontroller", {
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

var controller = vanillaController;