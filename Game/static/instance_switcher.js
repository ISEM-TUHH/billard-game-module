// this copy is done before the gamemode_retro loads all the listeners
var GM_COPY = document.querySelector(".instance").cloneNode(true);
var n_instances = 1;

var INSTANCES = {};
var INSTANCES_LAST_MODE = {};

function get_instances() {
    return document.querySelectorAll(".instance_selector");
}

function update_instance_switch_event_listeners() {
    get_instances().forEach((element) => {
        element.addEventListener("click", (e) => {
            activate_instance(e.target);
        });
    });
}

function activate_instance(button) {
    get_instances().forEach((elem) => {
        elem.classList.remove("active_instance_selector");
    })
    button.classList.add("active_instance_selector");
    
    // update global variable tracking the index of the instance


    // remove old instance from DOM
    INSTANCES[current_index] = document.getElementById("right-column").querySelector(".instance")
    INSTANCES[current_index].remove(); // remove from DOM
    INSTANCES_LAST_MODE[current_index] = current_gamemode;

    current_index = parseInt(button.innerText) - 1;
    console.log("Set current index to", current_index);

    current_gamemode = INSTANCES_LAST_MODE[current_index]
    document.getElementById("right-column").appendChild(INSTANCES[current_index]);

    // notify the gamemodule (-> beamer) of the changed gamemode (relevant for nested gamemodes)
    // see kp2Controller.js and update_gamemode.js
    document.dispatchEvent(gamemode_update_event);
}

document.getElementById("add_instance").addEventListener("click", (e) => {
    new_index = n_instances++;

    new_instance = GM_COPY.cloneNode(true);
    new_instance.classList.remove("instance-0");
    new_instance.classList.add("instance-" + new_index);

    // attach all event handlers, see gamemode_retro.js and game_configuration.js
    attach_events(new_instance.querySelectorAll(".mode"));
    attach_config_events(new_instance.querySelectorAll(".global-config"));
    attach_collapse_events(new_instance.querySelectorAll(".collapsible"));

    INSTANCES[new_index] = new_instance;
    INSTANCES_LAST_MODE[new_index] = "base"

    var button = document.createElement("button");
    button.classList.add("instance_selector");
    button.innerText = new_index+1;

    document.getElementById("instance_management").insertBefore(button, e.target);

    update_instance_switch_event_listeners();
    controller({
        "action": "add_instance"
    }).then(() => {
        activate_instance(button);
    })

    additional_instance_callback(new_instance);
});

update_instance_switch_event_listeners();