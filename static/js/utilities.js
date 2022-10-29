class Utilities {
    static reset_results() {
        results_best.style = "";
        results_best.innerHTML = results_best.className = "";
        results_all.innerHTML = results_all.className = "";
        results_info.innerHTML = "";

        results_all.style.display = "none";
        results_info.style.display = "none";
        results_best.style.display = "none";
        showmore_button.style.display = "none";
    }

    static toggle_all_downloadbuttons() {
        const buttons = document.getElementsByClassName("downloadbutton");
        Array.from(buttons).forEach(button => {
            button.classList.contains("disabled") ?
                button.classList.remove("disabled") :
                button.classList.add("disabled");
        })
    }

    static toggle_button(button_id) {
        const element = document.getElementById(button_id);
        element.classList.contains("disabled") ?
            element.classList.remove("disabled") :
            element.classList.add("disabled");
    }

    static toggle_elements(ids) {
        ids.forEach(id => Utilities.toggle_element(id))
    }
    static toggle_element(id, display_style) {
        if (typeof display_style === "undefined") display_style = "block";

        let elem = document.getElementById(id)
        elem.style.display == "none" ?
            elem.style.display = display_style :
            elem.style.display = "none";
    }

    static is_event_disabled(event) {
        return event.target.classList.contains("disabled");
    }
}
Utilities.reset_results()