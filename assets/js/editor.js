
(function(window, document, undefined){
    "use strict";

    var zForm = {
        buttons: "bold,italic,strike,abbr,key#sup,sub#center,right#ul,ol#titles,blockcode,image,quote,link#infoblocks",
        isExecuted: false,
        selection: null,

        addEvent: function(elem, evt, listener) {
            if (elem.addEventListener) {
                elem.addEventListener(evt, listener, false);
            } else {
                elem.attachEvent("on" + evt, listener);
            }
        },

        tags: {
            bold:       { title: "Gras",                        start: "**",                end: "**"   },
            italic:     { title: "Italique",                    start: "*",                 end: "*"    },
            strike:     { title: "Barré",                       start: "~~",                end: "~~"   },
            sup:        { title: "Exposant",                    start: "^",                 end: "^"    },
            sub:        { title: "Indice",                      start: "~",                 end: "~"    },
            abbr:       { title: "Abréviation" },
            key:        { title: "Touche",                      start: "||",                end: "||"   },

            titles:     { title: "Titres",                      action: "buildTitles"                   },

            ul:         { title: "Liste à puces"                                                        },
            ol:         { title: "Liste ordonnée"                                                       },

            center:     { title: "Aligner au centre",           start: "-> ",               end: " <-"  },
            right:      { title: "Aligner à droite",            start: "-> ",               end: " ->"  },

            quote:      { title: "Citation"                                                             },
            image:      { title: "Image"                                                                },
            link:       { title: "Lien"                                                                 },

            table:      { title: "Tableau"                                                              },

            infoblocks: { title: "Blocs spéciaux",              action: "buildInfoblocks"               },
            information:{ title: "Bloc Information"                                                     },
            question:   { title: "Bloc Question"                                                        },
            attention:  { title: "Bloc Attention"                                                       },
            error:      { title: "Bloc Erreur"                                                          },
            secret:     { title: "Bloc masqué"                                                          },

            monospace:  { title: "Code inline",                 start: "`",                 end: "`"    },
            blockcode:  { title: "Bloc de code coloré",         action: "buildCode"                     },

            math:       { title: "Formule mathématique",        start: "$",                 end: "$"    },
            hr:         { title: "Ligne horizontalle",          start: "\n\n------\n\n",    end: ""     },

            footnote:   { title: "Note en bas de page"                                                  }
        },

        codes: {
            Web: [
                ["html",    "HTML"],
                ["css",     "CSS"],
                ["js",      "Javascript"],
                ["php",     "PHP"],
                ["jfx",     "JavaFX"],
                ["cf",      "ColdFusion"],
                ["as3",     "Actionscript 3"],
                ["pl",      "Perl"],
                ["sql",     "SQL"],
                ["xml",     "XML"]
            ],
            Prog: [
                ["c",       "C"],
                ["cpp",     "C++"],
                ["csharp",  "C#"],
                ["java",    "Java"],
                ["delphi",  "Delphi"],
                ["py",      "Python"],
                ["ruby",    "Ruby"],
                ["pascal",  "Pascal"],
                ["vb",      "Visual Basic"],
                ["vbnet",   "VB.NET"],
            ],
            Autres: [
                ["bash",    "Bash"],
                ["diff",    "Diff"],
                ["erl",     "Erlang"],
                ["scala",   "Scala"],
                ["groovy",  "Groovy"],
                ["ps",      "PowerShell"],
                ["text",    "Autre"]
            ]
        },

        titles: {
            "link" :    "Lien hypertexte",
            "abbr" :    "Abréviation",
            "image":    "Image",
        },

        init: function() {
            var self = this,
                listTexta = document.getElementsByTagName("textarea");

            for (var i=0, c=listTexta.length; i<c; i++) {
                if (/md.editor/.test(listTexta[i].className)) {
                    this.setup(listTexta[i].id);
                }
            }

            this.addEvent(document.getElementById("content"), "DOMNodeInserted", (function(_this){
                return function(e) {
                    var element = e.target;
                    if (/md.editor/.test(element.className)) {
                        if(element.previousElementSibling.indexOf("zform-toolbar") > -1) {
                            _this.setup(element.id);
                        }
                    }
                };
            }) (this));

            var validateButton = document.createElement("a");
            validateButton.className = "btn btn-submit";
            validateButton.innerHTML = "Valider";
            validateButton.href = "#";

            function buildButton(type) {
                var btn = validateButton.cloneNode(true);
                btn.addEventListener("click", self.validatePopup.bind(self, type));
                return btn;
            }

            this.modals = {};
            this.modals.link = new window.Modal({
                "title": this.titles.link,
                "body": "<div>" +
                            "<label for=zform-modal-link-href>Lien :</label>" +
                            "<input type=text id=zform-modal-link-href />" +
                        "</div><div>" +
                            "<label for=zform-modal-link-text>Texte :</label>" +
                            "<input type=text id=zform-modal-link-text />" +
                        "</div>",
                "footer": buildButton("link")
            });

            this.modals.image = new window.Modal({
                "title": this.titles.image,
                "body": "<div>" +
                            "<label for=zform-modal-image-src>URL :</label>" +
                            "<input type=text id=zform-modal-image-src />" +
                        "</div><div>" +
                            "<label for=zform-modal-image-text>Texte :</label>" +
                            "<input type=text id=zform-modal-image-text />" +
                        "</div>",
                "footer": buildButton("image")
            });

            this.modals.abbr = new window.Modal({
                "title": this.titles.abbr,
                "body": "<div>" +
                            "<label for=zform-modal-abbr-abbr>Abbréviation :</label>" +
                            "<input type=text id=zform-modal-abbr-abbr />" +
                        "</div><div>" +
                            "<label for=zform-modal-abbr-text>Texte :</label>" +
                            "<input type=text id=zform-modal-abbr-text />" +
                        "</div>",
                "footer": buildButton("abbr")
            });
        },

        setup: function(textareaId) {
            var elemTexta = document.getElementById(textareaId);
            var elemTools = document.createElement("ul");
            elemTools.className = "zform-toolbar hide-for-small";

            elemTexta.parentNode.insertBefore(elemTools, elemTexta);

            if (!this.isExecuted) {
                this.addEvent(document, "click", function(event) {
                    if (~event.target.className.indexOf("zform-button") && !(~event.target.className.indexOf("zform-subbutton"))) {
                        return event.stopPropagation();
                    }

                    var menus = document.getElementsByClassName("zform-popup"), i = 0;

                    while (menus[i]) {
                        if (menus[i].getAttribute("data-zform-info") !== "dontclose" || event.target.nodeName.toLowerCase() === "textarea") {
                            menus[i].style.display = "none";
                        }
                        i++;
                    }
                }, false);

                this.isExecuted = true;
            }

            var groups = this.buttons.split("#");
            var buttons;

            var elemButtonLi, elemButton, currentButton;
            var elemPopup;

            for (var g=0, cg=groups.length; g<cg; g++) {
                buttons = groups[g].split(",");

                for (var b=0, cb=buttons.length; b<cb; b++) {
                    if (!(currentButton = this.tags[buttons[b]])) {
                        alert("La valeur '" + buttons[b] + "' n\'est pas reconnue comme étant une valeur correcte pour un bouton de zForm ! Corrigez votre syntaxe.");
                        continue;
                    }

                    elemButtonLi = elemTools.appendChild(document.createElement("li"));
                    elemButton = elemButtonLi.appendChild(document.createElement("a"));
                    elemButton.style.position = "relative";

                    elemButton.className = "ico-after zform-button zform-button-" + buttons[b];
                    elemButton.setAttribute("data-zform-textarea", textareaId);
                    elemButton.title = currentButton.title;
                    elemButton.innerText = currentButton.title;

                    if (currentButton.action) {
                        elemButton.href = "#";
                        this.addEvent(elemButton, "click", function(event, elemPopup) {
                            event.preventDefault();

                            if (elemPopup = this.getElementsByTagName("div")[0]) {
                                elemPopup.style.display = "block";
                            }
                        });

                        elemPopup = elemButton.appendChild(document.createElement("div"));
                        elemPopup.className = "zform-popup";
                        elemPopup.style.position = "absolute";
                        elemPopup.style.display = "none";
                        elemPopup.style.left = "0";
                        elemPopup.style.width = "auto";
                        elemPopup.style.whiteSpace = "nowrap";
                        elemPopup.style.textAlign = "left";

                            elemPopup = this[currentButton.action](elemPopup, currentButton, textareaId);
                    } else {
                        elemButton.addEventListener("click", (function(_button, _textareaId, _this, _tagtype) {
                            return function() {
                                _this.wrap(_button.start, _button.end, _textareaId, _tagtype);
                            };
                        }) (currentButton, textareaId, this, buttons[b]), false);

                    }
                }

                elemButton.style.marginRight = "20px";
            }
        },

        openPopup: function(popupGuid) {
            this.modals[popupGuid].open();

            return false;
        },

        closePopup: function() {
            window.Modal.closeCurrent();
        },

        validatePopup: function(type) {
            //var wrapper = document.getElementById("zform-modal-wrapper");
            type = type || this.selection.type;

            if (this.selection && this.selection.type) {
                this.wrap("___", "+++", this.selection.textareaId, type, null, true);
            }

            this.closePopup();
        },

        buildTitles: function(elemPopup, currentButton, textareaId, elemItem) {
            for (var i=1; i<=4; i++) {
                elemItem = elemPopup.appendChild(document.createElement("a"));
                elemItem.className = "ico-after zform-button zform-subbutton zform-button-title" + i;
                elemItem.title = "Titre de niveau " + i;
                elemItem.innerText = "Titre de niveau " + i;
                this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                    return function(event) {
                        event.preventDefault(); // IE madafaker
                        _this.wrap("", "", _textareaId, _options);
                    };
                }) (this, textareaId, "title" + i), false);
            }

            return elemPopup;
        },

        buildInfoblocks: function(elemPopup, currentButton, textareaId, elemItem) {
            var ids = ["information", "question", "attention", "error", "secret"];

            for (var i=0; i<5; i++) {
                elemItem = elemPopup.appendChild(document.createElement("a"));
                elemItem.className = "ico-after zform-button zform-subbutton zform-button-" + ids[i];
                elemItem.title = this.tags[ids[i]].title;
                elemItem.innerText = this.tags[ids[i]].title;
                this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                    return function(event) {
                        event.preventDefault(); // IE
                        _this.wrap("", "", _textareaId, _options);
                    };
                }) (this, textareaId, ids[i]), false);
            }

            return elemPopup;
        },

        buildCode: function(elemPopup, currentButton, textareaId) {
            var elemCol, elemItem, elemStg, i, c;

            for (var category in this.codes) {
                elemCol = elemPopup.appendChild(document.createElement("div"));
                elemCol.className = "zform-code-col";
                elemStg = elemCol.appendChild(document.createElement("b"));
                elemStg.style.display = "block";
                elemStg.style.fontWeight = "bold";
                elemStg.innerHTML = category;

                for (i=0, c=this.codes[category].length; i<c; i++) {
                    elemItem = elemCol.appendChild(document.createElement("span"));
                    elemItem.innerHTML = this.codes[category][i][1];

                    this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                        return function(event) {
                            event.preventDefault();
                            _this.wrap("", "", _textareaId, "blockcode", _options);
                        };
                    }) (this, textareaId, this.codes[category][i][0]));
                }
            }

            return elemPopup;
        },

        wrap: function(startTag, endTag, textareaId, type, options, isFromPopup) {
            var field       = document.getElementById(textareaId);
            var scroll      = field.scrollTop;
            var selection   = (!isFromPopup) ? {
                before:     null,
                current:    null,
                after:      null,
                range:      null,
                startTag:   startTag,
                endTag:     endTag,
                textareaId: textareaId,
                type:       type,
                options:    options
            } : this.selection;

            field.focus();

            if (field.setSelectionRange) {
                if (!isFromPopup) {
                    selection.before    = field.value.substring(0, field.selectionStart);
                    selection.current   = field.value.substring(field.selectionStart, field.selectionEnd);
                    selection.after     = field.value.substring(field.selectionEnd);
                }

                field.blur();

                if (selection = this.tagType(selection, selection.type, selection.options, isFromPopup)) {
                    field.value = selection.before + selection.startTag + selection.current + selection.endTag + selection.after;
                    field.focus();
                    field.setSelectionRange(selection.before.length + selection.startTag.length, selection.before.length + selection.startTag.length + selection.current.length);
                }
            } else { // IE < 9 with IE-only stuff
                if (!isFromPopup) {
                    selection.range     = document.selection.createRange();
                    selection.current   = selection.range.text;
                }

                if (selection = this.tagType(selection, selection.type, selection.options, isFromPopup)) {
                    selection.range.text = selection.startTag + selection.current + selection.endTag;
                    selection.range.moveStart("character",  -selection.endTag.length - selection.current.length);
                    selection.range.moveEnd("character",    -selection.endTag.length);
                    selection.range.select();
                }
            }

            field.scrollTop = scroll;
        },

        tagType: function(selection, type, options, isFromPopup) {
            if (!type)
                return selection;

            this.selection = selection;

            var input = "", href, text, regex;

            function iterateRows(txt, char) {
                var spltd = txt.split("\n");
                var order = (char === 0);

                for (var i=0, c=spltd.length; i<c; i++) {
                    spltd[i] = ((order) ? ++char + "." : char) + " " + spltd[i];
                }

                return spltd.join("\n");
            }

            switch (type) {
                case "link":
                    if (isFromPopup) {
                        href = document.getElementById("zform-modal-link-href").value;
                        text = document.getElementById("zform-modal-link-text").value;

                        selection.current = "[" + text + "](" + href + ")";
                    } else {
                        regex = new RegExp("^(http[s]?:\\/\\/(www\\.)?|ftp:\\/\\/(www\\.)?|www\\.){1}([0-9A-Za-z-\\.@:%_+~#=]+)+((\\.[a-zA-Z]{2,3})+)(/(.)*)?(\\?(.)*)?");

                        if (regex.test(selection.current)){

                            document.getElementById("zform-modal-link-href").value = selection.current;
                            document.getElementById("zform-modal-link-text").value = "";
                            document.getElementById("zform-modal-link-text").focus();
                        } else {
                            document.getElementById("zform-modal-link-text").value = selection.current;
                            document.getElementById("zform-modal-link-href").value = "";
                            document.getElementById("zform-modal-link-href").focus();
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "image":
                    if (isFromPopup) {
                        var src   = document.getElementById("zform-modal-image-src").value;
                        text  = document.getElementById("zform-modal-image-text").value || "Image utilisateur";

                        selection.current = "![" + text + "](" + src + ")";
                    } else {
                        regex = new RegExp("^(http[s]?:\\/\\/(www\\.)?|ftp:\\/\\/(www\\.)?|www\\.){1}([0-9A-Za-z-\\.@:%_+~#=]+)+((\\.[a-zA-Z]{2,3})+)(/(.)*)?(\\?(.)*)?");

                        if (regex.test(selection.current)){
                            document.getElementById("zform-modal-image-src").value = selection.current;
                            document.getElementById("zform-modal-image-text").value = "";
                        } else {
                            document.getElementById("zform-modal-image-text").value = selection.current;
                            document.getElementById("zform-modal-image-src").value = "";
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "quote":
                    selection.current = iterateRows(selection.current, ">");
                    break;

                case "information":
                case "attention":
                case "question":
                case "secret":
                    selection.current = "[[" + type + "]]\n" + iterateRows(selection.current, "|");
                    break;

                case "error":
                    selection.current = "[[erreur]]\n" + iterateRows(selection.current, "|");
                    break;

                case "ul":
                    selection.current = iterateRows(selection.current, "-");
                    break;

                case "ol":
                    selection.current = iterateRows(selection.current, 0);
                    break;

                case "title1":
                case "title2":
                case "title3":
                case "title4":
                    for (var i=0, c=parseInt(type.charAt(5)); i<c; i++) {
                        input += "#";
                    }

                    selection.current = selection.current.replace(/^\s*?/, input + " ");
                    break;

                case "footnote":
                    if (!selection.current) return;

                    if (input = prompt("Entrez la signification de cette abréviation")) {
                        selection.after += "\n\n*[" + selection.current +"]: " + input;
                    }
                    break;

                case "abbr":
                    if (isFromPopup) {
                        var valtext = document.getElementById("zform-modal-abbr-text").value;
                        if (valtext.trim() === "") {
                            valtext = document.getElementById("zform-modal-abbr-abbr").value;
                        }
                        selection.after += "\n\n*[" + document.getElementById("zform-modal-abbr-abbr").value + "]: "+ valtext;
                    } else {
                        if (selection.current.length < 10) {
                            document.getElementById("zform-modal-abbr-abbr").value = selection.current;
                            document.getElementById("zform-modal-abbr-text").value = "";
                        } else {
                            document.getElementById("zform-modal-abbr-text").value = selection.current;
                            document.getElementById("zform-modal-abbr-abbr").value = "";
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "blockcode":
                    selection.startTag = "```" + selection.options + ((selection.current.indexOf("\n") === 0) ? "" : "\n");
                    selection.endTag = "\n```";
                    break;
            }

            if (!selection.startTag)
                selection.startTag = "";

            if (!selection.endTag)
                selection.endTag = "";

            return selection;
        }
    };

    zForm.addEvent(window, "load", (function(_this) {
        return function() {
            _this.init();
        };
    }) (zForm));
})(window, document);


(function($, undefined){
    "use strict";

    $(".md-editor").on("keydown", function(e){
        // the message is submitted if the user is pressing Ctrl or Cmd with Enter and isn't pressing Alt or Shift
        if((e.ctrlKey || e.metaKey) && e.which === 13 && !e.altKey && !e.shiftKey){
            e.preventDefault();

            $(".message-submit > button[name=answer]").click();
        }
    });
})(jQuery);
