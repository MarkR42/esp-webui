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
        xhr.addEventListener("load", upload_done);
        xhr.send(file);
    }
    function upload_done() {
        var st = this.status;
        console.log("Status=" + st);
        if ((st == 200) || (st == 201)) {
            // Reload the page to show newly created file.
            // window.location.reload();
            window.location = window.location.href;
        } else {
            console.log("Sorry, it did not work");
        }
    }
    
}

add_controls();
