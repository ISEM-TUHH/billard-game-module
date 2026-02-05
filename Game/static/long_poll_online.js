/*

    Hit up the server every 6s. If the return is succesfull, stop polling.

*/
function run_long_poll() {
    let interval_id = setInterval(() => {
        controller({
            action: "long_poll"
        }).then((res) => {
            console.log("LONG POLL RESPONSE:", res);
            if (res.hasOwnProperty("resume") && res.resume) {
                clearInterval(interval_id);
                // also activate the gamemode. It gets expanded (clicked) by the emit flag in the response (see vanillaController.js)
                // this is specific to monolithic gamemodes!! (no KP2)
                activate_step(document.querySelector(".mode"), res.signal);
            }
        })
    }, 6000);
}

window.addEventListener("start_long_poll", (e) => {
    console.log("Starting long poll.")
    run_long_poll();
})