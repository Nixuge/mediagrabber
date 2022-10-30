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

    static _filename_from_headers(headers) {
        const content_disposition_header = headers.get('Content-Disposition')
        const regex_filename = /filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?;?/;

        const filename = content_disposition_header.match(regex_filename)[1];
        return filename
    }

    static async _download_res(res, filename) {
        let blob = await res.blob()
        const blob_url = window.URL.createObjectURL(blob);

        let a = document.createElement("a");
        a.download = filename;
        a.href = blob_url;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
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
            .then(res => {
                const filename = APIUtilities._filename_from_headers(res.headers);
                APIUtilities._download_res(res, filename);

                Utilities.toggle_element("results_all", "inline-flex");
                Utilities.toggle_element("loading");
                Utilities.toggle_all_downloadbuttons();
            });
    }
}