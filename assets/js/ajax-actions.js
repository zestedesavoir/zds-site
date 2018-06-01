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
        var text = this.text(),
            textToPut = this.data(dataAttribute);

        this.text(textToPut);
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
    $(".sidebar").on("click", "[data-ajax-input='follow-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $email = $(this).parents("li:first").next().find("[data-ajax-input='follow-topic-by-email']"),
            $followText = $act.find("span#follow_text"),
            $count = $form.find("span#subscriber_count"),
            $plural = $act.find("span#subscriber_plural");

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
                    if($email.hasClass("blue") === false){
                        $email.toggleText("content-on-click");
                        $email.addClass("blue");

                        $email.parents("form:first").find("input[name=email]").val(0);
                    }

                    $form.find("input[name=follow]").val(0);
                }

                $followText.toggleText("content-on-click");
                $count.text(data.subscriberCount);
                $plural.text(data.subscriberCount > 1 ? "s" : "");
                $act.toggleClass("blue yellow");

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
    $(".sidebar").on("click", "[data-ajax-input='follow-topic-by-email']", function(e){
        var $act = $(this),
            $follow = $(this).parents("li:first").prev().find("[data-ajax-input='follow-topic']"),
            $form = $(this).parents("form:first");

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
                    if($follow.hasClass("yellow") === false){
                        $follow.toggleText("content-on-click");
                        $follow.removeClass("blue");
                        $follow.addClass("yellow");

                        $follow.parents("form:first").find("input[name=follow]").val(1);
                    }

                    $form.find("input[name=email]").val(1);
                } else {
                    $form.find("input[name=email]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("blue");

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
    var previewTimeout;
    var previewInput;
    var previewContent;
    var previewDelay = 10000;
    var previewTime;
    $(".message-bottom [data-ajax-input='preview-message'], .preview-btn").on("mouseover click", function(e){
        e.stopPropagation();
        e.preventDefault();
        var $btn = $(this);
        var $form = $btn.parents("form:first");
        var isForm = !!$form.find(".preview-source").length;
        var $insertTarget = isForm ? $btn : $form;
        var text = "";
        if (isForm) {
            text = $btn.parent().prev().find(".preview-source").val();
        } else {
            text = $form.find("textarea[name=text]").val();
        }
        if (!previewInput) {
            previewInput = text;
        }

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            lastPost = $form.find("input[name=last_post]").val();

        if (previewInput === text && e.type === "click" && previewContent && (Date.now() - previewTime) < previewDelay) {
            return showPreview();
        }

        var later = function() {
            previewTimeout = null;
        };

        var callNow = previewInput !== text || !previewTimeout;
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(later, previewDelay);

        if (callNow) {
            $.ajax({
                url: $form.attr("action"),
                type: "POST",
                data: {
                    "csrfmiddlewaretoken": csrfmiddlewaretoken,
                    "text": text,
                    "last_post": lastPost,
                    "preview": "preview"
                }
            }).done(function(preview){
                previewContent = preview;
            }).fail(function(j, textStatus, err) {
                console.error(err);
            }).always(function() {
                previewTime = Date.now();
                previewInput = text;
                if (e.type === "click") {
                    showPreview();
                }
            });
        }

        function showPreview () {
            $(".previsualisation").remove();
            $(previewContent).insertAfter($insertTarget);
        }
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
})(jQuery);
