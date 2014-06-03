/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Zen mode for content-pages
   ========================================================================== */

if($('.article-content').length > 0){
    $('.content-container .authors').before($('<button/>', {
        'class': 'btn btn-grey ico-after view',
        'text': 'Zen mode',
        'click': function(e){
            $('.content-container').toggleClass('zen-mode tab-modalize');
            e.preventDefault();
            e.stopPropagation();
        }
    }));

    $('body').on('keydown', function(e){
        if($('.zen-mode').length > 0){
            // Espace close modal
            if(e.keyCode === 27){
                $('.content-container').toggleClass('zen-mode tab-modalize');
                e.stopPropagation();
            }
        }
    });
}