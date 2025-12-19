/*

    This file implements methods for updating a gamemodes global settings.

    Uses getAllInputValues() and send_settings() from gamemode_retro.js
*/


// as soon as anything else is clicked, update the configuration
document.querySelectorAll(".global-config").forEach((config_container) => {
    config_container.addEventListener("focusout", (e) => {
        var values = getAllInputValues(config_container);

        // check if all values are available
        var values_available = true;
        console.log(values)
        for (var k in values) {
            if (values[k] === "") {
                values_available = false;
                break;
            }
        }
        if (values_available) {
            send_setting(config_container, print=false, meta=true) // already handles updating the scoreboard to show, e.g., only the current semester
        }
    })
})