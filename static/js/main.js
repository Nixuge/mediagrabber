Utilities.reset_results()

async function list_qualities(event) {
    if (Utilities.is_event_disabled(event)) { return; }

    // Reset the bottom part & disable button
    Utilities.reset_results()
    Utilities.toggle_button("ddlbutton")
    Utilities.toggle_element("loading");

    // Constants
    const requested_url = document.getElementById("urlinput").value;
    const api_response = await APIUtilities.fetch_url_header(info_api, requested_url);

    // Big dirty block because yes
    if (!api_response.ok) {
        results_best.innerHTML = "Invalid link.";
        results_best.className = "biggestfont";
        results_best.style.color = "#e70606";
        results_best.style.textAlign = "center";
        results_best.style.width = "100%";
        results_best.style.marginLeft = "50%";
        results_best.style.transform = "translateX(-95%)";
        Utilities.toggle_button("ddlbutton")
        Utilities.toggle_elements(["loading", "results_best"]);
        return;
    }

    const api_json = await api_response.json();

    results_info.innerHTML += `<img src="${api_json['thumbnail']}">
    <label>"${api_json['title']}" from ${api_json['uploader']}</label><br>
    <label>on ${api_json['extractor_key']} (${api_json['duration']})</label><br>
    `

    show_results()
}

async function show_results() {
    // Constants
    const requested_url = document.getElementById("urlinput").value;

    // Request the provided link
    const api_response = await APIUtilities.fetch_url_header_json(best_qualities_api, requested_url);


    // Good old manual string building
    for (result in api_response) {
        if (result == "See all formats") continue;

        const id = api_response[result]["value"];

        results_best.innerHTML += `<div class='result'>
            <a class='button' onclick='APIUtilities.download_video_id(event, \"${requested_url}\", \"${id}\")'>
                <div class='innerbutton downloadbutton noanimation lessimportant'>Download ${result}</div>
            </a>`;
    }
    Utilities.toggle_button("ddlbutton")
    Utilities.toggle_elements(["showmore", "loading", "results_info"]);
    Utilities.toggle_element("results_best", "inline-block")
}

async function show_more_results() {
    Utilities.toggle_elements(["showmore", "loading"]);
    Utilities.toggle_all_downloadbuttons();

    const requested_url = document.getElementById("urlinput").value;
    const api_response = await APIUtilities.fetch_url_header_json(all_qualities_api, requested_url);

    Utilities.toggle_all_downloadbuttons();

    for (result in api_response) {
        if (result == "Choose custom value") continue;
        const resolution = result.match("\\) (.*)")[1]
        const format = result.match("\\((.*)\\)")[1]
        const id = api_response[result]["value"]
        results_all.innerHTML += `<div class='result'>
            <a class='button' onclick='APIUtilities.download_video_id(event, \"${requested_url}\", \"${id}\")'>
                <div class='innerbutton downloadbutton noanimation lessimportant'>${resolution} ${format}</div>
            </a>`;
    }

    Utilities.toggle_element("results_all", "inline-flex")
    Utilities.toggle_element("loading");
}