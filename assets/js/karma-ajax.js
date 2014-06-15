/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Manage karma AJAX requests (+1/-1 on messages)
   ========================================================================== */

(function($){
    "use strict";
    
    $(".upvote, .downvote").click(function(e){
        var $thumb = $(this),
            $karma = $thumb.parents(".message-karma:first"),
            $otherThumb = $thumb.hasClass("downvote") ? $karma.children(".upvote") : $karma.children(".downvote");

        $.ajax({
            url: $thumb.attr("href"),
            type: "GET", // TODO : use POST method (CSRF in GET)
            dataType: "json",
            success: function(data){
                if(data.upvotes > 0){
                    $karma.children(".upvote").addClass('has-vote').text("+" + data.upvotes);
                } else {
                    $karma.children(".upvote").removeClass('has-vote').empty();
                }
                if(data.downvotes > 0){
                    $karma.children(".downvote").addClass('has-vote').text("-" + data.downvotes);
                } else {
                    $karma.children(".downvote").removeClass('has-vote').empty();
                }
                $thumb.toggleClass("voted");
                $otherThumb.removeClass("voted");
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });
})(jQuery);