var contextmenuElement;

function pingUser() {
    copyStringToClipboard("@" + contextmenuElement.explicitOriginalTarget.data);
}

function markdownLink() {
    console.log("TTT", contextmenuElement);
    var text = contextmenuElement.explicitOriginalTarget.data;
    var url = contextmenuElement.explicitOriginalTarget.parentElement.parentElement.href;
    console.log("[" + text + "](" + url + ")");
    copyStringToClipboard("[" + text + "](" + url + ")");
}

function setContextualMenuElement(e) {
    //console.log(e);
    contextmenuElement = e;
    console.log(contextmenuElement);
}

// https://techoverflow.net/2018/03/30/copying-strings-to-the-clipboard-using-pure-javascript/
function copyStringToClipboard(str) {
    var el = document.createElement("textarea");
    el.value = str;
    el.setAttribute("readonly", "");
    el.style = {display: "none"};
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
}
