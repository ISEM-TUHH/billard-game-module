/*

    This file implements methods for the communication with the game module (MVC model).

Gamemodes can issue post requests to the game module's /gamemodecontroller endpoint. 

See vanillaController.js and kp2Controller.js for each implementation.

*/

function sender(apiEndpoint, jsonData) {
    fetch(apiEndpoint, {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
}

/* 
modus operandi: set this to a change event listener on checkboxes that signify actions
1. on the first check, this gets the coordinates from the camera and displays them. Sets the text of the checkboxes label to signal coordinate control
2. user controls (and corrects) the coordinates
3. on clicking (unchecking) the checkbox, this fires again. This time, take the current coordinate object and use it as the coordinates to send to the gamemode. On return, display the message in the label. Automatically check the box again, without firing this event again?
*/
//function getCoordsAndConfirm(event, jsonData, fun=kp2Controller, final=(l, r) => {l.innerText = r.message}) {
function getCoordsAndConfirm(event, jsonData, fun=controller, final=(l, r) => {l.innerText = (r.message !== undefined) ? r.message : l.dataset.og}) {
    //console.log(jsonData, event)
    target = event.target;
    label = target.labels[0];
    if (target.checked && !manipulatedFlag && !target.hasOwnProperty("step_coordinate_processing")) {
        // this is the first step 
        target.step_coordinate_processing = "check_coordinates";

        label.innerText = "Getting coordinates...";
        target.disabled = true;
        getCameraCoordinatesAsync().then(() => {
            label.innerText = "Commit coordinates" ;
            target.disabled = false;
        });
    } else {
        //console.log("entered else")
        //console.log(target.step_coordinate_processing)
        // this is the second step
        if ((target.step_coordinate_processing === "check_coordinates") || manipulatedFlag) {
            //console.log("really entered else")
            //target.checked = true; // REMOVE THIS FOR DOUBLE CLICK FIX
            delete target.step_coordinate_processing;
            setManipulatedFlag(false);
            return fun(jsonData).then((res) => {
                //target.labels[0].innerText = res.message;
                final(label, res);

                return res;
            });
        }
    }
}

/*function runGamemodeSteps(event, jsonData, subcontrol=(res)=>{}, fun=kp2Controller) {
    // wraps getCoordsAndConfirm, based on the steps of a gamemode. Loops over getCoordAndConfirm until the response has signal=finished => Display message to label.
    target = event.target;
    if (target.checked) {
        getCoordsAndConfirm(event, jsonData, fun=controller) // no output until finished
            .then((res) => {
                console.log(res);
                subcontrol(res);
                if (res.signal === "finished") {
                    target.labels[0].innerText = res.message;
                }
            })
    }
}
*/
