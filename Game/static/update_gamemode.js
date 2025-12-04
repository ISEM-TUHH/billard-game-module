/* 

    This file implements the updated challenge selector. Challenges are selected by opening their collapsing section, which closes all other sections.
    Upon changing the gamemode, a global (document) event "gamemode_updated" is triggered. This activates elements in the gamemode controller to initialise gamemodes on the server

*/
current_gamemode = "base";
ev = document.createEvent("HTMLEvents");
ev.initEvent("gamemode_updated", true, true);

modeSections = document.getElementsByClassName("collapsible")

function update_gamemode(button) {

    var new_gamemode = button.parentElement.id;
    if (current_gamemode === new_gamemode) {
        new_gamemode = "base";
    }
    for (var i = 0; i < modeSections.length; i++) {
        var content = modeSections[i].nextElementSibling;
        var this_gamemode = modeSections[i].parentElement.id;
        if (this_gamemode === new_gamemode) {
            content.style.height = (content.children[0].clientHeight + 20) + "px"
        } else {
            content.style.height = "0px";
        }
    }
    //console.log("Updated gamemode from " + current_gamemode + " to " + new_gamemode + ".");

    current_gamemode = new_gamemode;

    document.dispatchEvent(ev);
}

for (var i = 0; i < modeSections.length; i++) {
    modeSections[i].addEventListener("click", (event) => {update_gamemode(event.target);});
}