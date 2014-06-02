/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Manage karma AJAX requests (+1/-1 on messages)
   ========================================================================== */

$('.upvote, .downvote').click(function(e){
    var $thumb = $(this),
        $karma = $thumb.parents('.message-karma:first'),
        $otherThumb = $thumb.hasClass('downvote')
                        ? $karma.children('.upvote')
                        : $karma.children('.downvote');

    $.ajax({
        url: $thumb.attr('href'),
        type: 'GET', // TODO : use POST method (CSRF in GET)
        dataType: 'json',
        success: function(data){
            $karma.children('.upvote').text("+" + data.upvotes);
            $karma.children('.downvote').text("-" + data.downvotes);
            $thumb.toggleClass('voted');
            $otherThumb.removeClass('voted');
        }
    });

    e.stopPropagation();
    e.preventDefault();
});