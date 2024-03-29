const website_wrapper = document.getElementById("website_wrapper");
class Website {
    constructor(name, info, color_rgba, disabled) {
        this.name = name;
        this.info = info;
        this.color = color_rgba;
        this.dark_color = color_rgba.replace("1)", "0.5)"); //dirty but simple rgba trick
        this.sign = disabled ? "❌" : "✅"
        this.disabled = disabled ? " unavailable" : ""
    }
}

const websites = [
    new Website("Youtube", "Working fine, may be missing domains.", "rgba(255, 0, 0, 1)"),
    new Website("Youtube Music", "Same as Youtube.", "rgba(255, 0, 0, 1)"),
    new Website("Reddit", "Working fine.", "rgba(255, 67, 0, 1)"),
    new Website("Twitter", "First media only when multiple in a tweet, may be missing domains.", "rgba(29, 161, 242, 1)"),
    new Website("Twitch", "Unavailable, in progress. Need to filter out playlist links & paid links.", "rgba(127, 17, 224, 1)", true),
    new Website("Dailymotion", "Unavailable, in progress. Need to filter out playlist links.", "rgba(219, 219, 221, 1)", true),
    new Website("Instagram", "First media only when multiple available.", "rgba(221, 42, 123, 1)"),
    new Website("Youtube Kids", "Disabled for now, need to filter out playlist links.", "rgba(255, 163, 26, 1)", true),
    new Website("Snapchat", "Limited to content you can share with a link (eg. spotlight).", "rgba(255, 252, 0, 1)"),
    new Website("Odysee", "Disabled for now, need to filter out playlist links.", "rgba(192, 4, 78, 1)", true),
    new Website("Facebook", "Working fine, may be missing domains.", "rgba(66, 103, 178, 1)"),
]
websites.forEach(website => 
    website_wrapper.innerHTML += generate_website_div(website)
);

function generate_website_div(website) {
    console.log(website);
    return `<div class="website_div biggerfont" style="border: 3px solid ${website.color};">
        <span class="name" style="border-right: 3px solid ${website.color}; 
            background: ${website.dark_color}">${website.name}</span>
        <span class="info${website.disabled}"> ${website.sign}    ${website.info}</span>
    </div>`
}