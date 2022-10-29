class APIUtilities {
    static async fetch_url_header(api_url, requested_url) {
        return await fetch(api_url, {
            headers: {
                'Content-Type': 'text/json; charset="utf-8"',
                'Requested-Url': requested_url
            }
        });
    }
    static async fetch_url_header_json(api_url, requested_url) {
        return (await APIUtilities.fetch_url_header(api_url, requested_url)).json()
    }

    static async download_video_id(event, requested_url, id) {
        if (Utilities.is_event_disabled(event)) { return; }

        Utilities.toggle_all_downloadbuttons();
        Utilities.toggle_elements(["results_all", "loading"])

        const headers_dict = {
            'Format-Extension': 'mkv',
            'Requested-Url': requested_url,
            'Id': id
        };

        fetch(download_api, { headers: headers_dict })
            .then(res => res.blob())
            .then(blob => {
                const file = window.URL.createObjectURL(blob);
                window.location.assign(file);
                Utilities.toggle_element("results_all", "inline-flex")
                Utilities.toggle_element("loading")
                Utilities.toggle_all_downloadbuttons();
            });
    }
}