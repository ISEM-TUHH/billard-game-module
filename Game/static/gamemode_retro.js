/*

    This file provides further gamemode_controller relevant functions, but needs to be loaded after the page html has loaded.

*/

function getAllInputValues(container) {
    values = {}
    container.querySelectorAll("input").forEach((input, index) => {
        if (input.name != "") {
            if (input.type === "checkbox") {
                values[input.name] = input.checked;
            } else {
                values[input.name] = input.value;
            }
        }
    })
    container.querySelectorAll("select").forEach((input, index) => {
        if (input.name != "") {
            values[input.name] = input.value;
        }
    })
    return values;
}

// check if all values are set
function checkAllSet(values) {
    var values_available = true;
    for (var k in values) {
        if (values[k] === "") {
            values_available = false;
            break;
        }
    }
    return values_available
}

function activate_step(gamemode, new_step, index=NaN) {
    // gamemode is the DOM container (~html object) that contains the relevant steps.
    console.log("ACTIVATE STEP", new_step, gamemode)
    gamemode.querySelectorAll(".step").forEach((step, i) => {
        if (!isNaN(index)) {
            if (index === i) {
                step.classList.remove("deactivated");
            } else {
                step.classList.add("deactivated");
            }
            return;
        }
        // new_step is the out.signal
        // last part of the step.id (separated by "-")
        if (step.id.split("-").slice(-1)[0] === new_step) {
            step.classList.remove("deactivated");
        } else {
            step.classList.add("deactivated");
        }
    })
}

function send_setting(setting_container, print=false, meta=false) {
    var values = getAllInputValues(setting_container);
    jsonData = {};
    if (meta) {
        jsonData.kp2_activity = "settings";
    }
    jsonData.action = "settings";
    jsonData.settings = values;
    jsonData.container = setting_container.id;

    //return kp2Controller(jsonData, set_activity=(!meta)).then((res) => {
    return controller(jsonData, set_activity=(!meta)).then((res) => {
        if (print) {
            setting_container.querySelector(".output").innerText = res.message
        }
        if (res.hasOwnProperty("history")) {
            update_scoreboard(res.history);
        }

        return res
    })
}

// if this is true, events like sending the requests to the game module are used. If false, nothing get send.
var DOEVENTS = true;

//console.log("all gamemodes:", document.querySelectorAll(".mode"))
document.querySelectorAll(".mode").forEach((gamemode) => { // for all gamemodes:
    //console.log(gamemode)

    activate_step(gamemode, "not relevant yet", index=0); // activate the first step, deactivate all the others

    // setup event listeners for the settings
    gamemode.querySelectorAll(".setting").forEach((setting) => {
        setting.addEventListener("change", (e) => {
            send_setting(setting, print=true, meta=false)
        })
    })

    // setup main gamemode step interactions
    gamemode.querySelectorAll(".step").forEach((step) => { // for all steps:

        // to every step, add an event listener, that enables the submit button if all other inputs exist
        if (step.querySelectorAll("input").length > 1) {
            step.addEventListener("change", (e) => {
                //console.log("change triggered on", step)
                var values = getAllInputValues(step);
                console.log("value of all inputs", values)
                var values_available = true;
                for (var v in Object.entries(values)) {
                    if (v === "") {
                        values_available = false;
                        break;
                    }
                }
                if (values_available) {
                    step.querySelector("input.submit-step").disabled = false;
                } else {
                    step.querySelector("input.submit-step").disabled = true
                }

            })
            step.dispatchEvent(new Event("change")); // disable submit button // TODO NOT WORKING
        }
        
        
        var fetchFun = getCoordsAndConfirm;
        var event_to_listen = "change";
        submit_inputs = [step.querySelector("input[type=checkbox].submit-step")];
        if (submit_inputs[0] != step.querySelector("input.submit-step")) { // on special occasions like the longest break gamemode, we have interactions that dont need coordinates. They can be detected if the first input is not a checkbox (this is a definiton!!).
            var all_input_types = [];
            step.querySelectorAll("input.submit-step").forEach((otherInput) => {all_input_types.push(otherInput.type); })
            if (all_input_types.every((v, i, arr) => v === arr[0])) { // if all input types are equal
                if (all_input_types[0] === "button") {// if they are all buttons
                    submit_inputs = step.querySelectorAll("input[type=button]")
                    fetchFun = (e, jd) => {return controller(jd)}; // directly commit data and return response without step between. Using an anonymous function to mimick the interface of getCoordsAndConfirm
                    event_to_listen = "click"
                }
            }
        }
        // the first input is the submit
        //step.querySelector("input").addEventListener("change", (e) => {
        submit_inputs.forEach((submit_input) => {
            submit_input.addEventListener(event_to_listen, (e) => {
                if (!DOEVENTS) {
                    console.log("Event blocked due to DOEVENTS = false:", e)
                    return;
                }

                var jsonData = getAllInputValues(step);
                jsonData.action = "game";
                jsonData.coordinates = coordinatesBackend();
                if (e.target.name != "") {
                    jsonData.clicked_on = e.target.value; // for button inputs
                }
                // console.log("TRYING TO SEND:", jsonData)
                // since all inputs must be set (otherwise the submit button wouldn't be available): now fetch the current coordinates, show them to the user to be able to correct them. On the next click, they are submitted and processed.
                // after backend processing, updated the step
                //console.log("Now fetch from", e, jsonData);
                //console.log(fetchFun)
                fetchFun(e, jsonData)
                    .then((res) => {
                        //DOEVENTS = false;
                        activate_step(gamemode, res.signal); // show the next step, disable the previous /////////////////////////////////////////////////////// HERE THE KP2 signal is chosen, TODO: unify with normal games?
                        if (step.id.split("-").slice(-1)[0] === "finished") {
                            // if this gamemode round is finished: reset all labels to their data-og value

                            gamemode.querySelectorAll(".step [data-og]").forEach((element) => {
                                element.innerText = element.dataset.og;
                            })
                            gamemode.querySelectorAll("input[type=number]").forEach((element) => {
                                element.value = "";
                            })
                            gamemode.querySelectorAll("input[type=checkbox]").forEach((element) => {
                                element.checked = false;
                            })
                        } 
                        if (res.signal === "finished") {
                            // update the result bar
                            var element = gamemode.querySelector(".results").querySelectorAll("div")[res.was_round];//.querySelector(".open-game")// automatically selects the first available open game
                            if (res.hasOwnProperty("was_round")) {
                                console.log(element, res.was_round, res.score);
                                if (!res.hasOwnProperty("discarded")) {
                                    element.innerText = res.message; // 
                                    element.classList.add("finished-game");
                                    element.classList.remove("open-game");
                                } else {
                                    element.innerText = res.message;
                                    element.classList.add("failed-game");
                                    element.classList.remove("open-game")
                                }
                            }
                        } else {
                            if (res.hasOwnProperty("message")) {
                                if (res.hasOwnProperty("log_to")) { // if the logging location is specified, write to that object (must have innerText property, so e.g. a button is not possible yet. Should be easy to add.). Logging location must be inside step container.
                                    gamemode.querySelector(res.log_to).innerText = res.message;
                                } else if (e.target.labels.length > 0) {
                                    e.target.labels[0].innerText = res.message;
                                }
                            }
                            e.target.disabled = false;
                        }

                        if (res.hasOwnProperty("history")) {
                            var ev = new CustomEvent("update_scoreboard", {detail: res.history});
                            //console.log("HISTORY EVENT", ev, ev.detail);
                            window.dispatchEvent(ev);
                        }

                        DOEVENTS = true;
                    })
            })
        })
    })
})


// upon loading the page, uncheck ALL checkboxes on the page
document.querySelectorAll("#right-column input[type=checkbox]").forEach((element) => {
    element.checked = false
})