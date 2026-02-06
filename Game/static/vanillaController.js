/*

    This file provides the vanilla controller, which just adds the gamemode and sends the data directly to the gamemodecontroller endpoint of the game module.
    This is not really useful if if the gamemode has subgamemodes (like KP2)

*/

function vanillaController(jsonData, set_activity=false) {
    // set_activity argument is only for compatability reasons, not used
    jsonData["gmode"] = global_gamemode; // CHANGED FROM local_gamemode, test downstream effects!

    console.log("SEND:", jsonData); 

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
            console.log("RECEIVED:", res);

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

            if (res.hasOwnProperty("emit")) {
                console.log("Events to emit:", res.emit)
                for (var event_name in res.emit) {
                    var ev = new CustomEvent(event_name, {detail: res.emit[event_name]});
                    window.dispatchEvent(ev);
                    //console.log("Dispatched event", ev)
                }                
            }

            if (res.hasOwnProperty("click")) {
                // emit a click event onto everything that matches
                for (var selector in res.click) {
                    document.querySelectorAll(res.click[selector]).forEach((e) => {
                        e.click();
                    })
                }
            }

            if (res.hasOwnProperty("log_to")) {
                document.querySelectorAll(res.log_to).forEach((e) => { // should be only one, but this prevents a not found error.
                    e.innerText = res.message;
                });
                delete res["message"]; // remove so it doesnt get in the way of gamemode_retro.js
            }

            
            return res
        })
}

var controller = vanillaController;