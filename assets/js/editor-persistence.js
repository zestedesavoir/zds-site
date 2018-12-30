
// Stores editor text into window.localStorage with a kind of LRU
// cache where old entries are automatically deleted.
(function(document){
    "use strict";

    var MAX_SAVED_ENTRIES = 32;

    function getSavedEntries() {
        var source = localStorage.getItem("savedEditorText");
        return source ? JSON.parse(source) : [];
    }

    function saveEntries(entries) {
        localStorage.setItem("savedEditorText", JSON.stringify(entries));
    }

    // Returns `undefined` if not found.
    function get(id) {
        var entries = getSavedEntries();
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].id === id) {
                return entries[i].value;
            }
        }
    }

    function remove(id) {
        saveEntries(
            getSavedEntries()
                .filter(function (entry) {
                    return entry.id !== id;
                })
        );
    }

    function save(id, value) {
        remove(id);

        var entry = {id: id, value: value};
        var entries = [entry].concat(getSavedEntries())
                             .slice(0, MAX_SAVED_ENTRIES);
        saveEntries(entries);
    }

    function toArray(arrayish) {
        return Array.prototype.slice.call(arrayish);
    }

    function getFormSubmit(element) {
        if (!element) {
            return null;
        }

        if (element.tagName === "FORM") {
            return element.querySelector(
                "button[type=submit], input[type=submit]"
            );
        }

        return getFormSubmit(element.parentElement);
    }

    function setupPersistenceOnEditor(editor) {
        var name = editor.getAttribute("name") || "";
        var uniqueId = window.location.pathname + "@" + name;

        var savedText = get(uniqueId);
        if (savedText && !editor.value) {
            editor.value = savedText;
            save(uniqueId, savedText); // Mark it as used.
        }

        editor.addEventListener("input", function() {
            // It’s not a big deal, but this event is not fired when
            // editor buttons are clicked.
            save(uniqueId, editor.value); // TODO: Throttle?
        });

        var submit = getFormSubmit(editor);
        if (submit) {
            submit.addEventListener("click", function () {
                remove(uniqueId);
            });
        }
    }

    toArray(document.querySelectorAll(".md-editor"))
        .forEach(setupPersistenceOnEditor);

})(document);
