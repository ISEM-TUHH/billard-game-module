/*

    Hit up the server every 6s. If the return is succesfull, stop polling.

*/
let long_poll_interval_id
function run_long_poll() {
    long_poll_interval_id = setInterval(() => {
        controller({
            action: "long_poll"
        }).then((res) => {
            console.log("LONG POLL RESPONSE:", res);
            if (res.hasOwnProperty("resume") && res.resume) {
                clearInterval(long_poll_interval_id);
                // also activate the gamemode. It gets expanded (clicked) by the emit flag in the response (see vanillaController.js)
                // this is specific to monolithic gamemodes!! (no KP2)
                activate_step(document.querySelector(".mode"), res.signal);
            }
        })
    }, 6000);
    console.log("LONG POLL ID:", long_poll_interval_id)
}

window.addEventListener("start_long_poll", (e) => {
    console.log("Starting long poll.")
    run_long_poll();
})

window.addEventListener("stop_long_poll", (e) => {
    clearInterval(long_poll_interval_id);
    console.log("Cleared long poll by stop_long_poll event.")
})