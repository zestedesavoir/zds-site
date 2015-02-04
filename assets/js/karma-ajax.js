/* ===== Zeste de Savoir ====================================================
   Manage karma AJAX requests (+1/-1 on messages)
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

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
})(jQuery);
