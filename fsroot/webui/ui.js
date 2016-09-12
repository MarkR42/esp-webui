// UI Javascript code. Loaded with defer.

function add_controls()
{
    /*
     * Add controls to page.
     */
    var d = document.createElement("div");
    d.setAttribute("id", "controls");
    d.innerHTML = 'ESP-8266 (esp-webui) \
        UPLOAD: <input type="file" id="upf">\
        more todo\
        ';
    document.documentElement.appendChild(d);
    var uploader = document.getElementById("upf");
    uploader.addEventListener("change", trigger_upload);
}

function trigger_upload()
{
    var file = this.files[0];
    if (file) {
        var xhr = new XMLHttpRequest();
        var target_url= new URL(window.location);
        target_url.href += file.name;
        console.log(target_url.toString());
        xhr.open("PUT", target_url.toString());
        xhr.send(file);
    }
    
}

add_controls();
