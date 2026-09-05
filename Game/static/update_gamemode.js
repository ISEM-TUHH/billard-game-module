/* 

    This file implements the updated challenge selector. Challenges are selected by opening their collapsing section, which closes all other sections.
    Upon changing the gamemode, a global (document) event "gamemode_updated" is triggered. This activates elements in the gamemode controller to initialise gamemodes on the server

*/
try {
    current_gamemode = "base";
} catch(error) {
    // if the current gamemode is defined as const (like in local_game.js), this will throw an error. 
}
gamemode_update_event = document.createEvent("HTMLEvents");
gamemode_update_event.initEvent("gamemode_updated", true, true);

function attach_collapse_events(collapsibles) {
    collapsibles.forEach((element) => {
        element.addEventListener("click", (e) => {

            var new_gamemode = e.target.parentElement.id;
            if (current_gamemode === new_gamemode) {
                // this handles closing the current gamemode
                new_gamemode = "base";
            }    
            
            try {
                current_gamemode = new_gamemode;
            } catch(error) {
                // if the current gamemode is defined as const, this will throw an error. 
            }

            var coll = document.querySelectorAll(".collapsible");
            coll.forEach((elem) => {
                var content = elem.nextElementSibling;
                var this_gamemode = elem.parentElement.id;
                if (this_gamemode === new_gamemode) {
                    content.style.display = "block";
                    content.style.height = "fit-content"
                } else {
                    content.style.display = "none"
                }
            });
            document.dispatchEvent(gamemode_update_event);
        })
    });
}

attach_collapse_events(document.querySelectorAll(".collapsible"));