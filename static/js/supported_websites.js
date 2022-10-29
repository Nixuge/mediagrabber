const website_wrapper = document.getElementById("website_wrapper");
class Website {
    constructor(name, info, color_rgba) {
        this.name = name;
        this.info = info;
        this.color = color_rgba;
        this.dark_color = color_rgba.replace("1)", "0.5)"); //dirty but simple rgba trick
    }
}

const websites = [
    new Website("Youtube", "No playlist, working fine.", "rgba(255, 0, 0, 1)"),
    new Website("Youtube Music", "Same as Youtube.", "rgba(255, 0, 0, 1)"),
    new Website("Reddit", "Working fine.", "rgba(255, 67, 0, 1)"),
    new Website("Twitter", "First media only when multiple in a tweet.", "rgba(29, 161, 242, 1)"),
    new Website("Instagram", "First media only when multiple available.", "rgba(221, 42, 123, 1)"),
    new Website("Youtube Kids", "Working fine.", "rgba(255, 163, 26, 1)"),
    new Website("Snapchat", "Limited to content you can share with a link (eg. spotlight).", "rgba(255, 252, 0, 1)"),
    new Website("Odysee", "Working fine.", "rgba(192, 4, 78, 1)"),
    new Website("Facebook", "Working fine.", "rgba(66, 103, 178, 1)"),
]
websites.forEach(website => 
    website_wrapper.innerHTML += generate_website_div(website)
);

function generate_website_div(website) {
    return `<div class="website_div biggerfont" style="border: 3px solid ${website.color};">
        <span class="name" style="border-right: 3px solid ${website.color}; 
            background: ${website.dark_color}">${website.name}</span>
        <span class="info">${website.info}</span>
    </div>`
}