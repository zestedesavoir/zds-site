/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function($, undefined){
    "use strict";

    /**
     * Toggle the text of the element by the text of an attribute
     *
     * @param {string} dataAttribute
     */
    $.fn.toggleText = function(dataAttribute){
        var textContainer = this.find(".a11y");
        if (textContainer.length === 0) {
            textContainer = this;
        }
        else {
            textContainer = $(textContainer[0]);
        }

        var text = textContainer.text(),
            textToPut = this.data(dataAttribute);

        textContainer.text(textToPut);
        this.data(dataAttribute, text);
    };

    function synchText() {
        $("#mobile-menu [data-ajax-input]").each(function () {
            var dataAjaxInput = $(this).data("ajax-input");
            $(this).text($(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']").text());
        });
    }

    /**
     * Follow a topic
     */
    $(".sidebar, .flexpage-title-tool .actions").on("click", "[data-ajax-input='follow-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $email = $(this).parents("li:first").next().find("[data-ajax-input='follow-topic-by-email']"),
            $followText = $act.find("span#follow_text"),
            $count = $form.find("span#subscriber_count"),
            $plural = $act.find("span#subscriber_plural"),
            $otherSubscriberCount = $($act.attr("data-raw-subscriber-count"));

        if ($email.length === 0) {
            $email = $(this).parents(".buttons-combined").find("[data-ajax-input='follow-topic-by-email']");
        }

        $email.prop("disabled", true);

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            follow = $form.find("input[name=follow]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "follow": follow,
                "page": page
            },
            success: function(data){
                if(data.follow){
                    $form.find("input[name=follow]").val(1);
                } else {
                    if($email.hasClass("blue") === false || $email.hasClass("is-following") === true){
                        $email.toggleText("content-on-click");
                        $email.addClass("blue").removeClass("is-following");

                        $email.parents("form:first").find("input[name=email]").val(0);
                    }

                    $form.find("input[name=follow]").val(0);
                }

                $followText.toggleText("content-on-click");
                $count.text(data.subscriberCount);
                $plural.text(data.subscriberCount > 1 ? "s" : "");

                if ($otherSubscriberCount) {
                    $otherSubscriberCount.text(data.subscriberCount);
                }

                $act.toggleClass("blue yellow is-following");
                $act.blur();

                synchText();
            },
            complete: function(){
                $email.prop("disabled", false);
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Be notified by email
     */
    $(".sidebar, .flexpage-title-tool .actions").on("click", "[data-ajax-input='follow-topic-by-email']", function(e){
        var $act = $(this),
            $follow = $(this).parents("li:first").prev().find("[data-ajax-input='follow-topic']"),
            $form = $(this).parents("form:first");

        if ($follow.length === 0) {
            $follow = $(this).parents(".buttons-combined").find("[data-ajax-input='follow-topic']");
        }

        $follow.prop("disabled", true);

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            email = $form.find("input[name=email]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "email": email,
                "page": page
            },
            success: function(data){
                if(data.email){
                    if($follow.hasClass("yellow") === false || $follow.hasClass("is-following") === false){
                        $follow.toggleText("content-on-click");
                        $follow.removeClass("blue");
                        $follow.addClass("yellow is-following");

                        $follow.parents("form:first").find("input[name=follow]").val(1);
                    }

                    $form.find("input[name=email]").val(1);
                } else {
                    $form.find("input[name=email]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("blue, is-following");
                $act.blur();

                synchText();
            },
            complete: function(){
                $follow.prop("disabled", false);
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Featured request
     */
    $(".sidebar").on("click", "[data-ajax-input='request-featured']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $requestText = $act.find("#request_text"),
            $count = $form.find("#featured_request_count"),
            $plural = $act.find("#featured_request_plural");

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            requestFeatured = $form.find("input[name=request_featured]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "request_featured": requestFeatured
            },
            success: function(data){
                $requestText.toggleText("content-on-click");
                $count.text(data.newCount);
                $plural.text(data.newCount > 1 ? "s" : "");
                $act.toggleClass("blue yellow");

                synchText();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Mark a topic solved
     */
    $(".sidebar").on("click", "[data-ajax-input='solve-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first");

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            solved = $form.find("input[name=solved]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "solved": solved,
                "page": page
            },
            success: function(data){
                if(data.solved){
                    $form.find("input[name=solved]").val(1);
                } else {
                    $form.find("input[name=solved]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("green blue");
                $("[data-ajax-output='solve-topic']").html("Vous venez de marquer ce sujet comme résolu.");
                $("[data-ajax-output='solve-topic']").toggleClass("empty");

                synchText();
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Mobile action
     */
    $("#mobile-menu").on("click", "[data-ajax-input]", function(e){
        var dataAjaxInput = $(this).data("ajax-input");
        var $button = $(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']");

        if ($button[0]) {
            $(this).toggleText("content-on-click");
            $button.click();

            e.stopPropagation();
            e.preventDefault();
        }
    });

    function getLineAt(string, index) {
        var before = string.slice(0, index).split("\n").slice(-1)[0] || "";
        var after = string.slice(index).split("\n")[0] || "";
        return before + after;
    }

    function insertCitation(editor, citation) {
        if (editor.value === "") {
            editor.value = citation + "\n\n";
            return;
        }
        if (editor.selectionStart !== editor.selectionEnd ||
            getLineAt(editor.value, editor.selectionStart).trim()) {
            editor.value = editor.value + "\n\n" + citation;
            return;
        }

        var before = editor.value.slice(0, editor.selectionStart);
        var after = editor.value.slice(editor.selectionEnd);
        editor.value = before + "\n" + citation + "\n" + after;
    }

    /**
     * Cite a message
     */
    $(".message-actions").on("click", "[data-ajax-input='cite-message']", function(e){
        e.stopPropagation();
        e.preventDefault();

        var $act = $(this);
        var editor = document.querySelector(".md-editor");

        $.ajax({
            url: $act.attr("href"),
            dataType: "json",
            success: function(data){
                insertCitation(editor, data.text);
            }
        });

        // scroll to the textarea and focus the textarea
        $("html, body").animate({ scrollTop: $(editor).offset().top }, 500);
        editor.focus();
    });

    /**
     * Preview the message
     */
    $(".message-bottom [data-ajax-input='preview-message'], .preview-btn").on("click", function(e) {
        e.stopPropagation();
        e.preventDefault();
        var $btn = $(this);
        var $form = $btn.parents("form:first");
        var idInstance;
        if ($form.find(".preview-source").length) {
            idInstance = $btn.closest("div").prev().find(".md-editor").prop("id");
        } else {
            idInstance = $form.find(".md-editor").prop("id");
        }
        var text = instancesMde[idInstance].value();

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

                if ($form.find(".preview-source").length)
                    $(data).insertAfter($btn);
                else
                    $(data).insertAfter($form);
            }
        });
    });


    /*
     * Mark a message useful
     */
    $(".topic-message").on("click", "[data-ajax-input='mark-message-as-useful']", function(e){
        var $button = $(this),
            $form = $button.parents("form:first"),
            $message = $form.parents("article"),
            $usefulText = $message.find("[data-ajax-output='mark-message-as-useful']"),
            csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken
            },
            success: function(){
                $message.toggleClass("helpful");
                $button.toggleText("content-on-click");
                $usefulText.toggleClass("hidden");
                $button.blur();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });


    /* Editor */
    const maxRange = 99999999999;
    let csrf = $("input[name=csrfmiddlewaretoken]").val();
    let instancesMde = {};
    let elements = document.getElementsByClassName("md-editor");

    function checkMatch(str, reg) {
        var found = String(str).match(reg);
        if(found) {
            if (typeof found !== "undefined") {
                return found.length > 0;
            }
        }

    }
    function getStateZmd(cm) {
        var posStart = cm.getCursor("start");
        var posEnd = cm.getCursor("end");
        var line = cm.getLine(posStart.line);

        var beforeChars = line.slice(0, posStart.ch).match(/^(\S)+/g);
        var afterChars = line.slice(posEnd.ch).match(/(\S)+$/g);
        var ret = {};

        if (typeof beforeChars === "undefined" || typeof afterChars === "undefined" || (! beforeChars) || (! afterChars) ) {

        } else {
            if(checkMatch(beforeChars, /(.*)*\|\|$/) && checkMatch(afterChars, /^\|\|(.*)*/)) {
                ret.keyboard = true;
            }
            if(checkMatch(beforeChars, /(.*)`|$/) && checkMatch(afterChars, /^`(.*)/)) {
                ret.codeInline = true;
            }
            else if(checkMatch(beforeChars, /(.*)~$/) && checkMatch(afterChars, /^~(.*)/)) {
                ret.subscript = true;
            }
            else if(checkMatch(beforeChars, /(.*)\^$/) && checkMatch(afterChars, /^\^(.*)/)) {
                ret.superscript = true;
            }
            else if(checkMatch(beforeChars, /^->($|\s)+/) && checkMatch(afterChars, /(^|\s)+->$/)) {
                ret.alignRight = true;
            }
            else if(checkMatch(beforeChars, /^->($|\s)+/) && checkMatch(afterChars, /(^|\s)+<-$/)) {
                ret.alignCenter = true;
            }
            else if(checkMatch(beforeChars, /^\$\$($|\s)+/) && checkMatch(afterChars, /(^|\s)+\$\$$/)) {
                ret.math = true;
            }
        }

        if(checkMatch(line, /^\[\[(.+)\]\]$/)) { // it's a bloc
            var isBlock = true;
            for (var i = (posStart.line) + 1; i <= posEnd.line; i++) {
                if((! cm.getLine(i).startsWith("| ")) && (cm.getLine(i) !== "")) {
                    isBlock = false;
                    break;
                }
            }
            if (isBlock) {
                var reg = /^\[\[(.+)\]\]$/;
                var m = reg.exec(line);
                var _titleContents = m[1].split("|");
                if(_titleContents[0].trim() === "i" || _titleContents[0].trim() === "information") {
                    ret.blocInformation = true;
                } else if(_titleContents[0].trim() === "q" || _titleContents[0].trim() === "question") {
                    ret.blocQuestion = true;
                } else if(_titleContents[0].trim() === "e" || _titleContents[0].trim() === "erreur") {
                    ret.blocError = true;
                } else if(_titleContents[0].trim() === "s" || _titleContents[0].trim() === "secret") {
                    ret.blocSecret = true;
                } else {
                    ret.blocNeutral = true;
                }
            }
        } else {
            // find checklist
            var isCheckList = true;
            for (var j = (posStart.line) + 1; j <= posEnd.line; j++) {
                if((! cm.getLine(j).match(/^- \[(.{1})\](\s*)/)) && (cm.getLine(j) !== "")) {
                    isCheckList = false;
                    break;
                }
            }
            if(isCheckList) {
                ret.checklist = true;
            }
        }

        return ret;
    }

    function shiftLines(cm, lineNumber, replText) {
        var nextText;
        var currentText;
        var lastLine = cm.lastLine();
        for(var i=lineNumber; i<=lastLine+1; i++) {
            currentText=cm.getLine(i);
            if(i === lineNumber) {
                cm.replaceRange(replText, {line: i, ch:0} , {line:i, ch:maxRange});
            } else {
                cm.replaceRange(nextText, {line: i, ch:0} , {line:i, ch:maxRange});
            }
            nextText=currentText;
            if(i === lastLine) {
                nextText = cm.lineSeparator()+nextText;
            }
        }
    }

    function unShiftLines(cm, lineStart, lineEnd) {
        for(var i=lineStart+1; i<=lineEnd; i++) {
            cm.replaceRange(cm.getLine(i).slice(2), {line: i, ch:0} , {line: i, ch:maxRange});
        }
        cm.replaceRange("", {line: lineStart, ch:0} , {line: lineStart+1, ch: 0});
    }

    function _toggleBlockZmd(editor, type, startChars, endChars) {
        if (/editor-preview-active/.test(editor.codemirror.getWrapperElement().lastChild.className))
            return;
        endChars = (typeof endChars === "undefined") ? startChars : endChars;
        var cm = editor.codemirror;
        var stat = getStateZmd(cm);

        var text;
        var i,j;
        var start = startChars;
        var end = endChars;

        var startPoint = cm.getCursor("start");
        var endPoint = cm.getCursor("end");

        if (stat[type]) {
            text = cm.getLine(startPoint.line);
            start = text.slice(0, startPoint.ch);
            end = text.slice(startPoint.ch);
            var offset = 0;
            if(type === "bloc_information" || type === "bloc_question" || type === "bloc_error" || type === "bloc_secret" || type === "bloc_neutral") {
                unShiftLines(cm, startPoint.line, endPoint.line);
                startPoint.ch = 0;
            } else if (type === "checklist") {
                for(i=startPoint.line; i<=endPoint.line; i++) {
                    cm.replaceRange(cm.getLine(i).slice(startChars.length), {line: i, ch: 0}, {line: i, ch: maxRange});
                }
                endPoint.ch -= startChars.length;
            } else {
                const regAlign = /(->)(\s*)/;
                if (type === "keyboard") {
                    start = start.replace(/(\|\|)(?![\s\S]*(\|\|))/, "");
                    end = end.replace(/(\|\|)/, "");
                    offset = 2;
                } else if (type === "code_inline") {
                    start = start.replace(/(\`)(?![\s\S]*(\`))/, "");
                    end = end.replace(/(\`)/, "");
                    offset = 1;
                } else if (type === "subscript") {
                    start = start.replace(/(~)(?![\s\S]*(~))/, "");
                    end = end.replace(/(~)/, "");
                    offset = 1;
                } else if (type === "superscript") {
                    start = start.replace(/(\^)(?![\s\S]*(\^))/, "");
                    end = end.replace(/(\^)/, "");
                    offset = 1;
                } else if (type === "align_right") {
                    var m = regAlign.exec(start);
                    start = start.replace(/(->)(\s*)/, "");
                    end = end.replace(/(\s*)(->)/, "");
                    offset = m[0].length;
                } else if (type === "align_center") {
                    var m = regAlign.exec(start);
                    start = start.replace(/(->)(\s*)/, "");
                    end = end.replace(/(\s*)(<-)/, "");
                    offset = m[0].length;
                } else if (type === "math") {
                    start = start.replace(/(\$\$)(?![\s\S]*(\$\$))/, "");
                    end = end.replace(/(\$\$)/, "");
                    offset = 2;
                }

                cm.replaceRange(start + end, {
                    line: startPoint.line,
                    ch: 0,
                }, {
                    line: startPoint.line,
                    ch: maxRange,
                });

                startPoint.ch -= offset;
                if (startPoint !== endPoint) {
                    endPoint.ch -= offset;
                }
            }

        } else {
            if(type === "bloc_information" || type === "bloc_question" || type === "bloc_error" || type === "bloc_secret" || type === "bloc_neutral" ) {
                // blocs
                for(j = startPoint.line; j <= endPoint.line; j++) {
                    let text = startChars+cm.getLine(j);
                    cm.replaceRange(text, {line: j, ch: 0}, {line: j, ch: maxRange});
                }
                if(type === "bloc_information") {
                    shiftLines(cm, startPoint.line, "[[information]]");
                } else if(type === "bloc_question") {
                    shiftLines(cm, startPoint.line, "[[question]]");
                } else if(type === "bloc_error") {
                    shiftLines(cm, startPoint.line, "[[erreur]]");
                } else if(type === "bloc_secret") {
                    shiftLines(cm, startPoint.line, "[[secret]]");
                } else if(type === "bloc_neutral") {
                    shiftLines(cm, startPoint.line, "[[n|titre]]");
                }
                startPoint.ch = 0;
                endPoint.line += 1;
                endPoint.ch = endPoint.line.length;
            } else if(type === "checklist") {
                // checklists
                for(j=startPoint.line; j<=endPoint.line; j++) {
                    let text = startChars+cm.getLine(j);
                    cm.replaceRange(text, {line: j, ch: 0}, {line: j, ch: maxRange});
                }
                endPoint.ch += startChars.length;
            } else {
                // inline codes
                text = cm.getSelection();
                if (type === "keyboard") {
                    text = text.split("||").join("");
                } else if (type === "code_inline") {
                    text = text.split("`").join("");
                } else if (type === "subscript") {
                    text = text.split("~").join("");
                } else if (type === "superscript") {
                    text = text.split("^").join("");
                } else if (type === "align_right") {
                    text = text.split("-> ").join("");
                } else if (type === "align_center") {
                    text = text.split("-> ").join("").split(" <-").join("");
                } else if (type === "math") {
                    text = text.split("$$").join("");
                }
                cm.replaceSelection(start + text + end);

                startPoint.ch += startChars.length;
                endPoint.ch = startPoint.ch + text.length;
            }
        }

        cm.setSelection(startPoint, endPoint);
        cm.focus();
    }

    var uploadImage = function(file, onSuccess, onError) {
        var galleryUrl = "/api/galeries/"+ document.body.getAttribute("data-gallery") + "/images/";

        var formData = new FormData();
        formData.append("physical", file);
        formData.append("title", file.name);
        // WARN: if you test zds with sqlite, you can"t upload multiple files at a time
        $.ajax({
            url: galleryUrl,
            data: formData, type: "POST",
            processData: false,
            contentType: false,
            headers: {
                "X-CSRFToken": csrf
            },
            dataType: "json"
        }).done(function (result) {
            onSuccess(result.url);
        }).fail(function (resp) {
            var error = "Erreur inconnue";
            if(resp.responseText !== undefined && resp.responseText.indexOf("RequestDataTooBig") !== -1) {
                error = "L\"image est trop lourde.";
            } else if(resp.responseJSON !== undefined) {
                error = resp.responseJSON[0];
            } else if(resp.responseText !== undefined) {
                error = "Erreur " + resp.status + " " + resp.statusText + " : " + "'" + resp.responseText.split("\n")[0] + "'";
            } else if(resp.readyState === 0 && resp.statusText === "error") {
                error = "Oups ! Impossible de se connecter au serveur.";
            }
            onError(error);
        });
    };

    var customMarkdownParser = function(plainText) {
        var result;
        $.ajax({
            url: formEditor.attr("action"),
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrf,
                "text": plainText,
                "last_post": "",
                "preview": "preview"
            },
            success: function(data){
                result = data;
            },
            async: false
        });
        return result;
    };

    for (var i = 0; i < elements.length; i++) {
        var formEditor = $(elements[i]).closest("form");
        var easyMDE = new EasyMDE({
                element: elements[i],
                autosave: {
                    enabled: true,
                    uniqueId: elements[i].id,
                    delay: 1000,
                },
                indentWithTabs: false,
                minHeight: "500px",
                placeholder: "Votre message au format Markdown",
                promptURLs: true,
                promptTexts: {
                    image: "Url de votre image",
                    link: "Url de votre lien"
                },
                uploadImage: true,
                imageUploadFunction: uploadImage,
                imageTexts: {
                    sbInit: "Joindre des images par glisser-déposer ou coller depuis le presse-papiers.",
                    sbOnDragEnter: "Déposer l\"image pour l\"envoyer dans votre galérie",
                    sbOnDrop: "Téléchargement d\"images #images_names#",
                    sbProgress: "Téléchargement #file_name#: #progress#%",
                    sbOnUploaded: "Image téléchargée #image_name#"
                },
                spellChecker: false,
                promptAbbrv: true,
                theme: "idea",
                previewRender: function(plainText) {
                    return customMarkdownParser(plainText); // Returns HTML from a custom parser
                },
                syncSideBySidePreviewScroll: false,
                toolbar: [
                    {
                        name: "bold",
                        action: EasyMDE.toggleBold,
                        className: "fa fa-bold",
                        title: "Gras",
                    },
                    {
                        name: "italic",
                        action: EasyMDE.toggleItalic,
                        className: "fa fa-italic",
                        title: "Italique",
                    },
                    {
                        name: "strikethrough",
                        action: EasyMDE.toggleStrikethrough,
                        className: "fa fa-strikethrough",
                        title: "Barré",
                    },
                    {
                        name: "abbr",
                        action: (e) => {
                            var abbr = e.codemirror.getSelection();
                            var options = e.options;
                            var description = "";
                            if (options.promptAbbrv) {
                                if (abbr.length === 0) {
                                    abbr = prompt("Mot abrégé", "");
                                    if (abbr.length === 0) {
                                        return false;
                                    }
                                }
                                description = prompt("Description de l\"abbréviation", "");
                            }
                            e.codemirror.setCursor(e.codemirror.lastLine());
                            e.codemirror.replaceSelection("*["+abbr+"]: "+description);
                            e.codemirror.focus();
                        },
                        className: "fa fa-text-width",
                        title: "Abbréviation",
                    },
                    {
                        name: "keyboard",
                        action: (e) => {
                            _toggleBlockZmd(e, "keyboard", "||");
                        },
                        className: "fa fa-keyboard-o",
                        title: "Touche clavier",
                    },
                    {
                        name: "code_inline",
                        action: (e) => {
                            _toggleBlockZmd(e, "code_inline", "`");
                        },
                        className: "fa fa-terminal",
                        title: "Code inline",
                    },
                    "|",
                    {
                        name: "superscript",
                        action: (e) => {
                            _toggleBlockZmd(e, "superscript", "^");
                        },
                        className: "fa fa-superscript",
                        title: "Exposant",
                    },
                    {
                        name: "subscript",
                        action: (e) => {
                            _toggleBlockZmd(e, "subscript", "~");
                        },
                        className: "fa fa-subscript",
                        title: "Indice",
                    },
                    "|",
                    {
                        name: "align_center",
                        action: (e) => {
                            _toggleBlockZmd(e, "align_center", "-> ", " <-");
                        },
                        className: "fa fa-align-center",
                        title: "Aligner au centre",
                    },
                    {
                        name: "align_right",
                        action: (e) => {
                            _toggleBlockZmd(e, "align_right", "-> ", " ->");
                        },
                        className: "fa fa-align-right",
                        title: "Aligner a droite",
                    },
                    "|",
                    {
                        name: "list-ul",
                        action: EasyMDE.toggleItalic,
                        className: "fa fa-list-ul",
                        title: "Liste à puces",
                    },
                    {
                        name: "ordered-list",
                        action: EasyMDE.toggleOrderedList,
                        className: "fa fa-list-ol",
                        title: "Liste ordonnée",
                    },
                    {
                        name: "checklist",
                        action: (e) => {
                            _toggleBlockZmd(e, "checklist", "- [ ] ");
                        },
                        className: "fa fa-check-square-o",
                        title: "Liste de taches",
                    },
                    "|",
                    {
                        name: "heading",
                        action: EasyMDE.toggleHeadingSmaller,
                        className: "fa fa-header",
                        title: "Titres",
                    },
                    "|",
                    {
                        name: "image",
                        action: EasyMDE.drawImage,
                        className: "fa fa-picture-o",
                        title: "Image",
                    },
                    {
                        name: "link",
                        action: EasyMDE.drawLink,
                        className: "fa fa-link",
                        title: "Lien",
                    },
                    "|",
                    {
                        name: "quote",
                        action: EasyMDE.toggleBlockquote,
                        className: "fa fa-quote-left",
                        title: "Citation",
                    },
                    {
                        name: "code",
                        action: EasyMDE.toggleCodeBlock,
                        className: "fa fa-code",
                        title: "Bloc de code coloré",
                    },
                    {
                        name: "math",
                        action: (e) => {
                            _toggleBlockZmd(e, "math", "$$");
                        },
                        className: "fa fa-percent",
                        title: "Formule mathématique",
                    },
                    {
                        name: "table",
                        action: EasyMDE.drawTable,
                        className: "fa fa-table",
                        title: "Table",
                    },
                    "|",
                    {
                        name: "bloc_info",
                        action: (e) => {
                            _toggleBlockZmd(e, "bloc_information", "| ");
                        },
                        className: "fa fa-info",
                        title: "Bloc information",
                    },
                    {
                        name: "bloc_question",
                        action: (e) => {
                            _toggleBlockZmd(e, "bloc_question", "| ");
                        },
                        className: "fa fa-question",
                        title: "Bloc question",
                    },
                    {
                        name: "bloc_error",
                        action: (e) => {
                            _toggleBlockZmd(e, "bloc_error", "| ");
                        },
                        className: "fa fa-times",
                        title: "Bloc erreur",
                    },
                    {
                        name: "bloc_secret",
                        action: (e) => {
                            _toggleBlockZmd(e, "bloc_secret", "| ");
                        },
                        className: "fa fa-eye-slash",
                        title: "Bloc secret",
                    },
                    {
                        name: "bloc_neutral",
                        action: (e) => {
                            _toggleBlockZmd(e, "bloc_neutral", "| ");
                        },
                        className: "fa fa-square",
                        title: "Bloc neutre",
                    },
                    "|",
                    {
                        name: "preview",
                        action: EasyMDE.togglePreview,
                        className: "fa fa-eye no-disable",
                        title: "Aperçu",
                    },
                    {
                        name: "side-by-side",
                        action: EasyMDE.toggleSideBySide,
                        className: "fa fa-columns no-disable no-mobile",
                        title: "Aperçu sur le coté",
                    },
                    {
                        name: "fullscreen",
                        action: EasyMDE.toggleFullScreen,
                        className: "fa fa-arrows-alt no-disable no-mobile",
                        title: "Plein écran",
                    },
                ]
            }
        );
        instancesMde[elements[i].id]=easyMDE;
    }

})(jQuery);
