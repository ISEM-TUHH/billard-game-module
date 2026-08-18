/*
dark / light theme switch
adds dark class to the body. Then uses colorscheeme defined in styles.css.
persistently saves the last used theme.
*/

document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("#theme_toggle");
    const icon = document.querySelector("#theme_toggle_icon");
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark");
        icon.className = "fa-solid fa-sun";
    } else {
        icon.className = "fa-solid fa-moon";
    }

    if (button) {
        button.addEventListener("click", () => {
            document.body.classList.toggle("dark");

            const isDark = document.body.classList.contains("dark");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            icon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
        });
    }
});