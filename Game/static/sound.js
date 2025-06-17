/*

Provide logic for playing random sounds based on ratings

The html file including this js-file must have a div with the id "sounds" (can be invisible) with audio tags like:

<div id="sound" style="display: none;">
    <audio name="sound-0" data-group="0">
        <source src="file.mp3" type="audio/mpeg">
    </audio>
    ...
</div>

As this is a flask-rendered template, get the src as "{{ url_for('static', filename='sounds/file.mp3') }}".

Group (0 to 3 at the moment) rates it from perfect (0) to bad (3).

*/
soundDiv = document.getElementById("sounds")
function playSound(name, duration=8000) {
    console.log(name)
    var sound = document.getElementsByName(name)[0];
    sound.onplaying = function() {
        setTimeout(() => {
            sound.pause();
            sound.currentTime = 0;
        }, duration);
    }
    
    sound.play()
}

const lastGroup = 4; // create groups from 0 to lastGroup
function loadSoundGroups(div) {
    //groups = {"0": [], "1": [], "2": [], "3": []};
    groups = {};
    for (let i=0; i<=lastGroup; i++) {
        groups[i.toString()] = [];
    }

    for (let d of div.children) {
        //console.log(groups, d.dataset.group)
        groups[d.dataset.group].push(d.getAttribute("name"))
    }

    return groups;
}
var soundGroups = loadSoundGroups(soundDiv);
console.log(soundGroups);

function playRandomSound(group) {
    // group can be int or str
    var g = soundGroups[group.toString()] 
    var random_index = Math.floor(Math.random() * g.length);
    var random_name = g[random_index];
    playSound(random_name);
}

function soundPerfectResult() {
    playRandomSound("0");
}

function soundGoodResult() {
    playRandomSound("1");
}


function soundMediumResult() {
    playRandomSound("2");
}

function soundBadResult() {
    playRandomSound("3");
}


// give the result and a list with cutoff values for each step (perfect, good, medium, bad)
function soundJudge(result, steps) {
    console.log("there are " + steps.length + " steps provided to the sound judge")

    for (let i = 0; i < steps.length; i++) {
        if (result <= steps[i]) {
            playRandomSound(i);
            return;
        }
    }
    playRandomSound(lastGroup)
    return;
}