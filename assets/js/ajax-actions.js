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
            console.log($(this).text(), $(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']").text(), dataAjaxInput);

            $(this).text($(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']").text());
        });
    }

    /**
     * Karma of the messages
     */
    $(".topic-message").on("click", "button.upvote, button.downvote", function(e){
        var $thumb = $(this),
            $form = $(this).parents("form:first"),
            $karma = $thumb.parents(".message-karma:first"),
            $upvote = $karma.find(".upvote"),
            $downvote = $karma.find(".downvote"),
            $otherThumb = $thumb.hasClass("downvote") ? $upvote : $downvote;

        var message = $form.find("input[name=message]").val(),
            csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "message": message,
                "csrfmiddlewaretoken": csrfmiddlewaretoken
            },
            success: function(data){
                var title = "";
                // Update upvotes
                if(data.upvotes > 0){
                    $upvote.addClass("has-vote").text("+" + data.upvotes);
                    title = "Ce message est utile (" + data.upvotes + " personne";
                    if(data.upvotes > 1)
                        title += "s ont";
                    else
                        title += " a";
                    title += " trouvé ce message utile)";
                    $upvote.attr("title",  title);
                } else {
                    $upvote.removeClass("has-vote").empty();
                    $upvote.attr("title", "Ce message est utile");
                }
                // Update downvotes
                if(data.downvotes > 0){
                    $downvote.addClass("has-vote").text("-" + data.downvotes);
                    title = "Ce message n'est pas utile (" + data.downvotes + " personne";
                    if(data.downvotes > 1)
                        title += "s n'ont";
                    else
                        title += " n'a";
                    title += " pas trouvé ce message utile)";
                    $downvote.attr("title",  title);
                } else {
                    $downvote.removeClass("has-vote").empty();
                    $downvote.attr("title", "Ce message n'est pas utile");
                }

                // Show to the user what thumb is voted
                $thumb.toggleClass("voted");
                $otherThumb.removeClass("voted");

                // Show to the user what thumb is the more voted
                if(data.upvotes > data.downvotes) {
                    $upvote.addClass("more-voted");
                } else {
                    $upvote.removeClass("more-voted");
                }
                if(data.downvotes > data.upvotes) {
                    $downvote.addClass("more-voted");
                } else {
                    $downvote.removeClass("more-voted");
                }

                $thumb.blur();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Follow a topic
     */
    $(".sidebar").on("click", "[data-ajax-input='follow-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $email = $(this).parents("li:first").next().find("[data-ajax-input='follow-topic-by-email']");

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

                $act.toggleText("content-on-click");
                $act.toggleClass("blue yellow");

                synchText();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Be notify by email
     */
    $(".sidebar").on("click", "[data-ajax-input='follow-topic-by-email']", function(e){
        var $act = $(this),
            $follow = $(this).parents("li:first").prev().find("[data-ajax-input='follow-topic']"),
            $form = $(this).parents("form:first");

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

    /**
     * Cite a message
     */
    $(".message-actions").on("click", "[data-ajax-input='cite-message']", function(e){
        var $act = $(this),
            $editor = $(".md-editor");

        $.ajax({
            url: $act.attr("href"),
            dataType: "json",
            success: function(data){
                $editor.val($editor.val() + data.text + "\n\n");
            }
        });

        // scroll to the textarea and focus the textarea
        $("html, body").animate({ scrollTop: $editor.offset().top }, 500);
        $editor.focus();

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Preview the message
     */
    $(".message-bottom").on("click", "[data-ajax-input='preview-message']", function(e){
        var $form = $(this).parents("form:first");
        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            text = $form.find("textarea[name=text]").val(),
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

                $(data).insertAfter($form);

                /* global MathJax */
                if ($(data).find("$").length > 0)
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            }
        });
        e.stopPropagation();
        e.preventDefault();
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
