// by Thunderseb

(function(window, document, undefined){
    "use strict";

    if (localStorage.getItem('editor_choice') !== 'old') {
        return;
    }

    var zForm = {
        // Params
        // ~~~~~~
        buttons: "bold,italic,strike,abbr,key,monospace#sup,sub#center,right#ul,ol#titles,blockcode,image,quote,link#infoblocks,chars,smilies",

        tags: {
            bold:       { title: "Gras",                        start: "**",                end: "**",  useless: true },
            italic:     { title: "Italique",                    start: "*",                 end: "*",   useless: true },
            strike:     { title: "Barré",                       start: "~~",                end: "~~",  useless: true },
            sup:        { title: "Exposant",                    start: "^",                 end: "^"    },
            sub:        { title: "Indice",                      start: "~",                 end: "~"    },
            abbr:       { title: "Abréviation" },
            key:        { title: "Touche",                      start: "||",                end: "||"   },

            titles:     { title: "Titres",                      action: "buildTitles"                   },

            ul:         { title: "Liste à puces"                                                        },
            ol:         { title: "Liste ordonnée"                                                       },

            center:     { title: "Aligner au centre",           start: "-> ",               end: " <-"  },
            right:      { title: "Aligner à droite",            start: "-> ",               end: " ->", useless: true  },

            quote:      { title: "Citation"                                                             },
            image:      { title: "Image"                                                                },
            link:       { title: "Lien"                                                                 },

            table:      { title: "Tableau"                                                              },

            infoblocks: { title: "Blocs spéciaux",              action: "buildInfoblocks"               },
            information:{ title: "Bloc Information"                                                     },
            question:   { title: "Bloc Question"                                                        },
            attention:  { title: "Bloc Attention"                                                       },
            error:      { title: "Bloc Erreur"                                                          },
            neutre:     { title: "Bloc Neutre"                                                          },
            secret:     { title: "Bloc masqué"                                                          },

            monospace:  { title: "Code inline",                 start: "`",                 end: "`"    },
            blockcode:  { title: "Bloc de code coloré",         action: "buildCode"                     },

            math:       { title: "Formule mathématique",        start: "$",                 end: "$"    },
            hr:         { title: "Ligne horizontalle",          start: "\n\n------\n\n",    end: "",    useless: true },

            chars:      { title: "Caractères spéciaux",         action: "buildChars"                    },
            smilies:    { title: "Smileys",                     action: "buildSmilies",                 useless: true },

            footnote:   { title: "Note en bas de page"                                                  }
        },

        codes: {
            Web: {
                html:   { title: "HTML" },
                css:    { title: "CSS" },
                js:     { title: "Javascript" },
                php:    { title: "PHP" },
                jfx:    { title: "JavaFX" },
                pl:     { title: "Perl" },
                sql:    { title: "SQL" },
                xml:    { title: "XML" }
            },
            Prog: {
                arduino:{ title: "Arduino" },
                c:      { title: "C" },
                cpp:    { title: "C++" },
                csharp: { title: "C#" },
                java:   { title: "Java" },
                hs:     { title: "Haskell" },
                py:     { title: "Python" },
                ruby:   { title: "Ruby" },
                vbnet:  { title: "VB.NET" }
            },
            Autres: {
                bash:   { title: "Bash" },
                diff:   { title: "Diff" },
                scala:  { title: "Scala" },
                groovy: { title: "Groovy" },
                ps:     { title: "PowerShell" },
                text:   { title: "Autre" }
            }
        },

        chars: {
            Typo: {
                char_g0: { title: "« »", start: "« ", end: " »" },
                char_gl: { title: "« ", start: "« ", end: "" },
                char_gr: { title: " »", start: " »", end: "" },
                char_h0: { title: "“ ”", start: "“", end: "”" },
                char_hl: { title: "“", start: "“", end: "" },
                char_hr: { title: "”", start: "”", end: "" },
                char_su: { title: "…", start: "…", end: "" },
                char_ti: { title: "−", start: "−", end: "" },
                char_ca: { title: "—", start: "—", end: "" }
            },
            "Caractères": {
                char_in: { title: "Insécable", start: " ", end: "" },
                char_ag: { title: "À", start: "À", end: "" },
                char_cc: { title: "Ç", start: "Ç", end: "" },
                char_ea: { title: "É", start: "É", end: "" },
                char_eg: { title: "È", start: "È", end: "" },
                char_oe: { title: "œ", start: "œ", end: "" },
                char_eo: { title: "Œ", start: "Œ", end: "" }
            }
        },

        smilies: {
            0: {
                smiley_sm: { title: ":)",         start: ":)",         end: "", image: "/static/smileys/svg/smile.svg" },
                smiley_he: { title: ":D",         start: ":D",         end: "", image: "/static/smileys/svg/heureux.svg" },
                smiley_cl: { title: ";)",         start: ";)",         end: "", image: "/static/smileys/svg/clin.svg" },
                smiley_la: { title: ":p",         start: ":p",         end: "", image: "/static/smileys/svg/langue.svg" },
                smiley_ri: { title: ":lol:",      start: ":lol:",      end: "", image: "/static/smileys/svg/rire.svg" },
                smiley_un: { title: ":euh:",      start: ":euh:",      end: "", image: "/static/smileys/svg/unsure.svg" },
                smiley_tr: { title: ":(",         start: ":(",         end: "", image: "/static/smileys/svg/triste.svg" },
                smiley_hu: { title: ":o",         start: ":o",         end: "", image: "/static/smileys/svg/huh.svg" },
                smiley_ib: { title: ":B",         start: ":B",         end: "", image: "/static/smileys/svg/b.svg" }
            },
            1: {
                smiley_c1: { title: ":colere2:",  start: ":colere2:",  end: "", image: "/static/smileys/svg/mechant.svg" },
                smiley_oo: { title: "o_O",        start: "o_O",        end: "", image: "/static/smileys/svg/blink.svg" },
                smiley_uu: { title: "^^",         start: "^^",         end: "", image: "/static/smileys/svg/hihi.svg" },
                smiley_si: { title: ":-°",        start: ":-°",        end: "", image: "/static/smileys/svg/siffle.svg" },
                smiley_an: { title: ":ange:",     start: ":ange:",     end: "", image: "/static/smileys/svg/ange.svg" },
                smiley_c2: { title: ":colere:",   start: ":colere:",   end: "", image: "/static/smileys/svg/angry.svg" },
                smiley_di: { title: ":diable:",   start: ":diable:",   end: "", image: "/static/smileys/svg/diable.svg" },
                smiley_ma: { title: ":magicien:", start: ":magicien:", end: "", image: "/static/smileys/svg/magicien.svg" }
            },
            2: {
                smiley_ni: { title: ":ninja:",    start: ":ninja:",    end: "", image: "/static/smileys/svg/ninja.svg" },
                smiley_gd: { title: ">_<",         start: ">_<",       end: "", image: "/static/smileys/svg/pinch.svg" },
                smiley_pi: { title: ":pirate:",   start: ":pirate:",   end: "", image: "/static/smileys/svg/pirate.svg" },
                smiley_pl: { title: ":'(",        start: ":'(",        end: "", image: "/static/smileys/svg/pleure.svg" },
                smiley_ro: { title: ":honte:",    start: ":honte:",    end: "", image: "/static/smileys/svg/rouge.svg" },
                smiley_so: { title: ":soleil:",   start: ":soleil:",   end: "", image: "/static/smileys/svg/soleil.svg" },
                smiley_ww: { title: ":waw:",      start: ":waw:",      end: "", image: "/static/smileys/svg/waw.svg" },
                smiley_zz: { title: ":zorro:",    start: ":zorro:",    end: "", image: "/static/smileys/svg/zorro.svg" }
            }
        },

        titles: {
            "link" :    "Lien hypertexte",
            "abbr" :    "Abréviation",
            "image":    "Image",
        },

        isExecuted: false,
        selection: null,
        currentElemPopup: null,

        addEvent: function(elem, evt, listener) {
            if (elem.addEventListener) {
                elem.addEventListener(evt, listener, false);
            } else {
                elem.attachEvent("on" + evt, listener);
            }
        },

        init: function() {
            for(var category in this.smilies)
            {
                for(var name in this.smilies[category])
                {
                    var smiley = this.smilies[category][name];
                    smiley.start = " " + smiley.start + " ";
                }
            }
            var self = this,
                listTexta = document.getElementsByTagName("textarea");

            for (var i=0, c=listTexta.length; i<c; i++) {
                if (/md.editor/.test(listTexta[i].className)) {
                    this.setup(listTexta[i].id);
                }
            }

            this.addEvent(document.getElementById("content"), "DOMNodeInserted", (function(_this){
                return function(e) {
                    if (/md.editor/.test(e.target.className)) {
                        _this.setup(e.target.id);
                    }
                };
            }) (this));

            var validateButton = document.createElement("a");
            validateButton.className = "btn btn-submit";
            validateButton.innerHTML = "Valider";
            validateButton.href = "javascript:;";

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
                            "<label for=zform-modal-abbr-abbr>Abréviation :</label>" +
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
            var self = this;
            elemTools.className = "zform-toolbar hide-for-small";

            elemTexta.parentNode.insertBefore(elemTools, elemTexta);

            if (!this.isExecuted) {
                this.addEvent(document, "click", function(event) {
                    // If it's a root button and not a subbutton
                    if (~event.target.className.indexOf("zform-button") && !(~event.target.className.indexOf("zform-subbutton"))) {

                        return event.stopPropagation();
                    }

                    var menus = document.getElementsByClassName("zform-popup"), i = 0;

                    while (menus[i]) {
                        if (menus[i].getAttribute("data-zform-info") !== "dontclose" || event.target.nodeName.toLowerCase() === "textarea") {
                            menus[i].style.display = "none";
                            self.currentElemPopup = (menus[i] == self.currentElemPopup) ? null: self.currentElemPopup;
                        }
                        i++;
                    }
                }, false);

                this.isExecuted = true;
            }

            var groups = this.buttons.split("#"), buttons;
            var elemPopup, elemButtonLi, elemButton, currentButton;

            for (var g=0, cg=groups.length; g<cg; g++) {
                buttons = groups[g].split(",");

                for (var b=0, cb=buttons.length; b<cb; b++) {
                    if (!(currentButton = this.tags[buttons[b]])) {
                        alert("La valeur '" + buttons[b] + "' n\'est pas reconnue comme étant une valeur correcte pour un bouton de zForm ! Corrigez votre syntaxe.");
                        continue;
                    }

                    elemButtonLi = elemTools.appendChild(document.createElement("li"));
                    elemButton   = elemButtonLi.appendChild(this.createButton(currentButton, { display: "button", type: buttons[b], textarea: textareaId }));
                }

                elemButton.style.marginRight = "20px";
            }
        },

        createButton: function(currentButton, opts) {
            var elemButton = document.createElement((opts.display === "button") ? "a" : "span"), elemPopup;

            elemButton.className = (opts.display === "button") ? "ico-after zform-button zform-button-" + opts.type : "zform-subbutton-span-" + opts.type;
            if (currentButton.useless) { elemButton.className += " zform-button-useless" }
            elemButton.setAttribute("data-zform-textarea", opts.textarea);
            elemButton.title = currentButton.title;
            elemButton.innerHTML = currentButton.title;

            if (opts.display === "span") { elemButton.style.display = "block"; }
            if (currentButton.hasOwnProperty("image")) elemButton.innerHTML = '<img src="' + currentButton.image +  '" alt="' + currentButton.title + '" />';

            if (currentButton.action) { // Button with a submenu
                var self = this;
                elemButton.style.position = "relative";
                if (this.currentElemPopup){
                    elemButton.removeChild(this.currentElemPopup);
                    this.currentElemPopup = null;
                }
                this.addEvent(elemButton, "click", function(event, elemPopup) {
                    event.preventDefault();

                    if (elemPopup = this.getElementsByTagName("div")[0]) {
                        elemPopup.style.display = "block";

                        //>> align
                        var contentX = document.getElementById("content").offsetWidth,
                            posLeftSide = elemPopup.offsetParent.offsetLeft + elemPopup.offsetWidth,
                            isNotOut = (posLeftSide <= contentX);

                        elemPopup.style.left = (isNotOut) ? "0" : "inherit";
                        elemPopup.style.right = (isNotOut) ? "inherit" : "0";

                        var parentLeft = elemPopup.offsetParent.offsetLeft,
                            posRightSide = parentLeft - elemPopup.offsetWidth;
                        if (!isNotOut && posRightSide < 0) {
                            elemPopup.style.right = "inherit";
                            var left = -parentLeft;
                            left += Math.max((contentX - elemPopup.offsetWidth) / 2, 0);
                            elemPopup.style.left = left + "px";
                        }
                        //<<

                        if(self.currentElemPopup){
                            self.currentElemPopup.style.display = "none";
                        }
                        if(self.currentElemPopup == elemPopup){
                            self.currentElemPopup = null;
                        }else{
                            self.currentElemPopup = elemPopup;
                        }
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
                elemPopup = this[currentButton.action](elemPopup, currentButton, opts.textarea);

            } else {
                this.addEvent(elemButton, "click", (function(_button, _textareaId, _this, _tagtype, _extraoption) {
                    return function(event) {
                        //event.preventDefault();
                        _this.wrap(_button.start, _button.end, _textareaId, _tagtype, _extraoption);
                        this.style.fontWeight = "bold";
                    };
                }) (currentButton, opts.textarea, this, opts.type, opts.extra), false);
            }

            return elemButton;
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
            var ids = ["information", "question", "attention", "error", "neutre", "secret"];

            for (var i=0; i<6; i++) {
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

        buildColumnous: function(elemPopup, currentButton, opts) {
            var elemCol, elemItem, elemStg, i, c, name;

            for (var category in opts.src) {
                elemCol = elemPopup.appendChild(document.createElement("div"));
                elemCol.className = "zform-code-col";

                if (isNaN(category)) { // We put the title only if it's a string
                    elemStg = elemCol.appendChild(document.createElement("b"));
                       elemStg.style.display = "block";
                    elemStg.style.fontWeight = "bold";
                    elemStg.innerHTML = category;
                }

                for (name in opts.src[category]) {
                    opts.extra = name;
                    elemCol.appendChild(this.createButton(opts.src[category][name], opts));
                }
            }

            return elemPopup;
        },

        buildCode: function(elemPopup, currentButton, textareaId) {
            return this.buildColumnous(elemPopup, currentButton, {
                textarea: textareaId,
                src: this.codes,
                type: "blockcode",
                display: "span"
            });
        },

        buildChars: function(elemPopup, currentButton, textareaId) {
            return this.buildColumnous(elemPopup, currentButton, {
                textarea: textareaId,
                src: this.chars,
                type: "chars",
                display: "span"
            });
        },

        buildSmilies: function(elemPopup, currentButton, textareaId) {
            return this.buildColumnous(elemPopup, currentButton, {
                textarea: textareaId,
                src: this.smilies,
                type: "smiley",
                display: "span"
            });
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
            field.dispatchEvent(new Event('update'));
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

                        this.openPopup(type);

                        if (regex.test(selection.current)){
                            document.getElementById("zform-modal-link-href").value = selection.current;
                            document.getElementById("zform-modal-link-text").value = "";
                            document.getElementById("zform-modal-link-text").focus();
                        } else {
                            document.getElementById("zform-modal-link-text").value = selection.current;
                            document.getElementById("zform-modal-link-href").value = "";
                            document.getElementById("zform-modal-link-href").focus();
                        }

                        return false;
                    }
                    break;

                case "image":
                    if (isFromPopup) {
                        var src   = document.getElementById("zform-modal-image-src").value;
                        text  = document.getElementById("zform-modal-image-text").value || "Image utilisateur";

                        selection.current = "![" + text + "](" + src + ")";
                    } else {
                        regex = new RegExp("^(http[s]?:\\/\\/(www\\.)?|ftp:\\/\\/(www\\.)?|www\\.){1}([0-9A-Za-z-\\.@:%_+~#=]+)+((\\.[a-zA-Z]{2,3})+)(/(.)*)?(\\?(.)*)?");

                        this.openPopup(type);

                        if (regex.test(selection.current)){
                            document.getElementById("zform-modal-image-src").value = selection.current;
                            document.getElementById("zform-modal-image-text").value = "";
                            document.getElementById("zform-modal-image-text").focus();
                        } else {
                            document.getElementById("zform-modal-image-text").value = selection.current;
                            document.getElementById("zform-modal-image-src").value = "";
                            document.getElementById("zform-modal-image-src").focus();
                        }

                        return false;
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

                case "neutre":
                    selection.current = "[[" + type + "|Titre]]\n" + iterateRows(selection.current, "|");
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
                    this.openPopup(type);

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
                            document.getElementById("zform-modal-abbr-text").focus();
                        } else {
                            document.getElementById("zform-modal-abbr-text").value = selection.current;
                            document.getElementById("zform-modal-abbr-abbr").value = "";
                            document.getElementById("zform-modal-abbr-abbr").focus();
                        }
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

    zForm.addEvent(document, "DOMContentLoaded", (function(_this) {
        return function() {
            _this.init();
        };
    }) (zForm));
})(window, document);

function uploadImage (e, dataTransferAttr, csrf){
    var $editor = $(e.target);
    // need to use window[dataTransferAttr for IE-11
    var dataTransfert = e.originalEvent[dataTransferAttr] || window[dataTransferAttr];
    var files = [];
    if (dataTransfert.files) {
        files = dataTransfert.files;
    } else if (dataTransfert.items) {
        for (var i = 0; i < dataTransfert.items.length; i++) {
            if (dataTransfert.types[i].indexOf("Files") === 0) {
                files.push(dataTransfert.items[i].getAsFile())
            }
        }
    }
    if (!files.length) {
        return false;
    }
    var galleryUrl = '/api/galeries/'+ document.body.getAttribute('data-gallery') + '/images/';
    var printErr =  function (message) {
        var $div = $("<div>", {
            text: message,
            class: "alert-box error",
        });

        $div.append('<a href="#hidealert" class="close-alert-box close-alert-box-text">Cacher</a>');

        var borderTop = document.documentElement.scrollTop,
            borderBot = borderTop + $(window).height(),
            posTop = $div.offset().top,
            posBot = posTop + $div.outerHeight();

        var scrollAnimTo = function (pos) {
            $('body, html').animate({ scrollTop: pos }, 1000);
        };

        if (posTop < borderTop) {
            scrollAnimTo(posTop);
        } else if (borderBot < posBot) {
            scrollAnimTo(posBot - $(window).height());
        }

        return $div.insertAfter($editor);
    }
    Object.values(files).forEach(function (f) {
        var filesize = (f.size / 1024);
        if (f.type.indexOf("image") !== 0) {
            return printErr("Le format d'image est invalide !");
        } else if (filesize > 1024) {
            return printErr("Votre image est trop lourde (" + filesize + " Kio). La taille maximum est de 1024.0 Kio !");
        }

        var mdWaitingCode = '![' + f.name + ' en cours de téléchargement]()';
        var mdWaitingRegexp = mdWaitingCode.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        $editor.val($editor.val() + '\n' + mdWaitingCode );
        var formData = new FormData();
        formData.append('physical', f);
        formData.append('title', f.name);
        // WARN: if you test zds with sqlite, you can't upload multiple files at a time
        $.ajax({
            url: galleryUrl,
            data: formData, type: 'POST',
            processData: false,
            contentType: false,
            headers: {
                "X-CSRFToken": csrf
            },
            dataType: 'json'
        }).done(function (result) {
            var mdFinalCode = '![' + result.legend + '](' + result.url +')';

            $editor.val($editor.val().replace(new RegExp(mdWaitingRegexp), mdFinalCode));
            $editor[0].dispatchEvent(new Event('update'));
        }).fail(function (resp) {
            var error = "Erreur inconnue";
            if(resp.responseText !== undefined && resp.responseText.indexOf("RequestDataTooBig") !== -1) {
                error = "L'image est trop lourde.";
            } else if(resp.responseJSON !== undefined) {
                error = resp.responseJSON[0];
            } else if(resp.responseText !== undefined) {
                error = "Erreur " + resp.status + " " + resp.statusText + " : " + '"' + resp.responseText.split("\n")[0] + '"';
            } else if(resp.readyState === 0 && resp.statusText === "error") {
                error = "Oups ! Impossible de se connecter au serveur.";
            }

            printErr(error);

            $editor.val($editor.val().replace(new RegExp(mdWaitingRegexp), ''));
        });
    });
    return true;
}

(function($, undefined){
    "use strict";

    if (localStorage.getItem('editor_choice') !== 'old') {
        return;
    }

    var csrf = $("input[name=csrfmiddlewaretoken]").val();
    var dragEventNumber = 0;
    $(".md-editor").on("keydown", function(e){
        // the message is submitted if the user is pressing Ctrl or Cmd with Enter and isn't pressing Alt or Shift
        if((e.ctrlKey || e.metaKey) && e.which === 13 && !e.altKey && !e.shiftKey){
            e.preventDefault();

            $(".message-submit > button[name=answer]").click();
        }
    }).on("dragenter", function(e) {
        dragEventNumber++;
        e.preventDefault();
        if (dragEventNumber === 1) {
            $(e.target).addClass("selected");
        }
    }).on("dragover", function(e) {
        e.preventDefault();
    }).on("dragleave", function(e) {
        dragEventNumber--;
        e.preventDefault();
        if (dragEventNumber === 0) {
            $(e.target).removeClass("selected");
        }
    }).on("drop", function (e) {
        e.preventDefault();
        uploadImage(e, "dataTransfer", csrf);
        $(e.target).removeClass("selected");
        dragEventNumber = 0;
    }).on("paste", function(e) {
        var clipboard = e.originalEvent.clipboardData;
        var data = clipboard.files || clipboard.items;
        if (!data.length) { //                  ^^^^^ Edge
            return;
        }
        if (uploadImage(e, "clipboardData", csrf)) {
            e.preventDefault();
        }
    });
})(jQuery);

// Stores editor text into window.localStorage with a kind of LRU
// cache where old entries are automatically deleted.
(function(document){
    "use strict";

    if (localStorage.getItem('editor_choice') !== 'old') {
        return;
    }

    function toArray(arrayish) {
        return Array.prototype.slice.call(arrayish);
    }

    function setupPersistenceOnEditor(editor) {
        var name = editor.getAttribute("name") || "";
        var mdeUniqueKey = (window.location.pathname + window.location.search + '@' + editor.getAttribute('name')).replace(/[?|&]page=(\d+)/g, '')
        var form = editor.closest("form");

        var savedText = localStorage.getItem('smde_' + mdeUniqueKey)
        if (savedText && !editor.value) {
            editor.value = savedText;
        }

        function update() {
            // Do not save anything if the editor is empty
            if(editor.value === "") {
                localStorage.removeItem('smde_' + mdeUniqueKey)
            } else {
                localStorage.setItem('smde_' + mdeUniqueKey, editor.value)
            }
        }

        editor.addEventListener("input", update);
        editor.addEventListener("update", update);

        form.addEventListener("submit", function () {
            localStorage.removeItem('smde_' + mdeUniqueKey)
        });
    }

    toArray(document.querySelectorAll(".md-editor"))
        .forEach(setupPersistenceOnEditor);

})(document);


if (localStorage.getItem('editor_choice') === 'old') {
    /**
     * Preview the message
     */
    $(".message-bottom [data-ajax-input='preview-message'], .preview-btn").on("click", function(e) {
        e.stopPropagation();
        e.preventDefault();
        var $btn = $(this);
        var $form = $btn.parents("form:first");
        var text = "";
        if ( $form.find(".preview-source").length ) {
            var $textSource = $btn.parent().prev().find(".preview-source");
            text = $textSource.val();
        } else {
            text = $form.find("textarea[name=text]").val();
        }

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            lastPost = $form.find("input[name=last_post]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "text": text,
                "last_post": lastPost,
                "preview": "preview"
            },
            success: function(data){
                $(".previsualisation").remove();

                if (typeof $textSource === "undefined")
                    $(data).insertAfter($form);
                else
                    $(data).insertAfter($btn);
            }
        });
    });
}
