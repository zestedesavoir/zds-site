/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function($){
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

    function insertCitation(editor, citation) {
        let cm = window.editors[editor.id].codemirror;
        let doc = cm.getDoc();
        let cursor = doc.getCursor();

        if (cm.getValue() === "") {
            cm.setValue(citation + "\n\n");
            cm.setCursor(cm.lineCount(), 0);
        } else if (cm.somethingSelected()) {
            doc.replaceSelection("\n\n" + citation + "\n\n");
        } else {
            doc.replaceRange("\n\n" + citation + "\n\n", cursor);
        }

        cm.focus();
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

        // scroll to the textarea
        $("html, body").animate({ scrollTop: $(editor).siblings(".CodeMirror").offset().top }, 500);
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
