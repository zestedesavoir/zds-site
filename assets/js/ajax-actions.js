/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function(window, $, undefined){
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

    /**
     * Karma of the messages
     */
    $(".topic-message").on("click", ".upvote, .downvote", function(e){
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
                // Update upvotes
                if(data.upvotes > 0){
                    $upvote.addClass("has-vote").text("+" + data.upvotes);
                } else {
                    $upvote.removeClass("has-vote").empty();
                }
                // Update downvotes
                if(data.downvotes > 0){
                    $downvote.addClass("has-vote").text("-" + data.downvotes);
                } else {
                    $downvote.removeClass("has-vote").empty();
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
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Cite a message
     */
    $(".message-actions").on("click", "[data-ajax-input='cite-message']", function(e){
        var $act = $(this),
            $editor = $(".md-editor");

        // quote the selection 
        var doAjax = !(function() {
            var $message = $act.closest(".message"),
                $msgcontent = $message.find("[itemprop=text]"),
                username = $message.find("[itemprop=name]").text(),
                href = $message.find("> .message-metadata > a.date")[0].href;


            if (window.getSelection) {
                var selection = window.getSelection(),
                    range = selection.getRangeAt(0),
                    node = null;

                if (selection.isCollapsed)
                    return false;

                if (!$(range.startContainer).closest($msgcontent)[0])
                    return false;

                if (!$(range.endContainer).closest($msgcontent)[0]) {
                    node = $msgcontent[0].childNodes;
                    node = node[node.length - 1];

                    range.setEnd(node, node.nodeValue.length);
                }

                var markdown = window.html2markdown(range.cloneContents());

                markdown = markdown.replace(/(^|\n)/g, "\n> ");
                markdown += "\nSource:[" + username + "](" + href + ")";

                $editor.val($editor.val() + markdown + "\n\n\n");
                return true;
            }

            return false;
        })();

        if (doAjax) {
            $.ajax({
                url: $act.attr("href"),
                dataType: "json",
                success: function(data){
                    $editor.val($editor.val() + data.text + "\n\n");
                }
            });
        }

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
            },
        });
        e.stopPropagation();
        e.preventDefault();
    });
})(window, jQuery);
