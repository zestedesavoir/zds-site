/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Manage karma AJAX requests (+1/-1 on messages)
   ========================================================================== */

(function($){
    "use strict";

    $(".upvote, .downvote").click(function(e){
        var $thumb = $(this),
            $form = $(this).parents("form:first"),
            $karma = $thumb.parents(".message-karma:first"),
            $otherThumb = $thumb.hasClass("downvote") ? $karma.find(".upvote") : $karma.find(".downvote");

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
                debugger;
                if(data.upvotes > 0){
                    $karma.find(".upvote").addClass("has-vote").text("+" + data.upvotes);
                } else {
                    $karma.find(".upvote").removeClass("has-vote").empty();
                }
                if(data.downvotes > 0){
                    $karma.find(".downvote").addClass("has-vote").text("-" + data.downvotes);
                } else {
                    $karma.find(".downvote").removeClass("has-vote").empty();
                }
                $thumb.toggleClass("voted");
                $otherThumb.removeClass("voted");
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });
})(jQuery);
