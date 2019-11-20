(function($){
    "use strict";

    let source = localStorage.getItem("savedEditorText");
    let entries = source ? JSON.parse(source) : [];
    for (let n in entries) {
        console.log(entries[n]);
        localStorage.setItem("smde_" + entries[n].id, entries[n].value);
    }
    localStorage.removeItem("savedEditorText");
})(jQuery);
