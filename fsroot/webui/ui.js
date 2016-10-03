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
    
    // Add special buttons to items
    var anchors = document.getElementsByTagName("a");
    for (var i= anchors.length - 1; i>=0; i--) {
        var a = anchors[i];
        var parent = a.parentNode;
        // Check parent, should be class "d" or "f" for dir or files.
        var is_dir = parent.classList.contains("d");
        var is_file = parent.classList.contains("f");
        if (is_dir || is_file) {
            var btn = document.createElement("a");
            // 0x2026 = horizonal ellipsis.
            var file_icon = String.fromCodePoint(0x2026);
            var folder_icon = String.fromCodePoint(0x2026);
            btn.textContent = is_dir ? folder_icon : file_icon;
            btn.classList.add("actionsbut");
            btn.classList.add(is_dir ? "d" : "f");
            btn.setAttribute("href", a.href);
            btn.setAttribute("title", "Actions for this object...");
            btn.addEventListener("click", trigger_popup);
            parent.appendChild(btn);
        }
    }
}

function trigger_popup(ev)
{
    var href = this.href;
    var is_dir = this.classList.contains("d");
    var ok;
    if (is_dir) {
        ok = confirm("TODO: Actions for directory " + href);
    } else {
        ok = confirm("TODO: Actions for file " + href);
    }
    ev.preventDefault();
}

function send_xhr_put(file, done_func)
{
    var xhr = new XMLHttpRequest();
    var target_url= new URL(window.location);
    target_url.href += file.name;
    console.log(target_url.toString());
    xhr.open("PUT", target_url.toString());
    xhr.addEventListener("load", done_func);
    xhr.send(file);    
    return xhr;
}

function trigger_directory_reload()
{
    // Reload the page to show newly created file.
    // window.location.reload();
    window.location = window.location.href;
}

function trigger_upload()
{
    var file = this.files[0];
    if (file) {
        send_xhr_put(file, upload_done);
    }
    function upload_done() {
        var st = this.status;
        console.log("Status=" + st);
        if ((st == 200) || (st == 201)) {
            trigger_directory_reload();
        } else {
            console.log("Sorry, it did not work");
        }
    }
}

function init_drop_events()
{
    /*
    var dropelement = document.createElement("div");
    dropelement.style.position = "absolute";
    dropelement.style.display = "none";
    dropelement.style.width = "80%";
    dropelement.style.height = "80%";
    dropelement.style.left = "10%";
    dropelement.style.top = "10%";
    dropelement.style.backgroundColor = "black";
    dropelement.style.opacity = "0.5";
    dropelement.id = "d42";
    document.documentElement.appendChild(dropelement);
    */
    
    var target = document.documentElement;
    target.addEventListener("dragstart", function(e) { }, false);
    target.addEventListener("dragover", function(e) { 
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        return false;
        }, false);
    target.addEventListener("dragenter", function(e) { 
        target.classList.add("dragging");
        }, false);    
    target.addEventListener("dragleave", function(e) {
        target.classList.remove("dragging");
         }, false);
    target.addEventListener("dragend", function(e) { 
        target.classList.remove("dragging");
        }, false);
    //  Now the proper event: drop.
    target.addEventListener("drop", handle_drop, false);
    console.log("drop events ok");
}

var UPLOAD_QUEUE = [];
var UPLOAD_BUSY = false;
var UPLOAD_COUNT = 0;

function handle_drop(e) {
    e.stopPropagation();
    e.preventDefault();
    console.log("Dropped");
    this.classList.remove("dragging");
    // Handle datatransfer.
    var files = e.dataTransfer.files;
    for (var i=0; i < files.length; i++) {
        var f = files[i];
        UPLOAD_QUEUE.push(f);
    }
    if (! UPLOAD_BUSY) {
        start_upload_queue();
    }
    return false;
}

function start_upload_queue() {
    UPLOAD_BUSY = true;
    if (UPLOAD_QUEUE.length > 0) {
        // Submit PUT request using xhr.
        var f = UPLOAD_QUEUE.shift();
        send_xhr_put(f, upload_done);
    } else {
        UPLOAD_BUSY = false;
        if (UPLOAD_COUNT > 0) {
            // We uploaded something, great!
            trigger_directory_reload();
        }
    }
    function upload_done()
    {
        // this = xmlhttprequest.
        // We really should check the status.
        var st = this.status;
        if ((st == 200) || (st == 201)) {
            UPLOAD_COUNT += 1;
        }
        // Start next upload.
        start_upload_queue();
    }
}

add_controls();
init_drop_events();
