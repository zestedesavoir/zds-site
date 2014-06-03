/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Manage modals boxes
   ========================================================================== */

$overlay = $('<div/>', {
    'id': 'modals-overlay'
}).on('click', function(e){
    closeModal($("#modals .modal:visible"));
    e.preventDefault();
    e.stopPropagation();
});

$('body').append($('<div/>', { 'id': 'modals' }));
$('.modal').each(function(){
    $('#modals').append($(this));
    $(this).append($('<a/>', {
        'class': 'btn btn-cancel ' + ($(this).is('[data-modal-close]') ? 'btn-modal-fullwidth' : ''),
        'href': '#close-modal',
        'text': $(this).is('[data-modal-close]') ? $(this).attr('data-modal-close') : "Annuler"
    }).on('click', function(e){
        closeModal();
        e.preventDefault();
        e.stopPropagation();
    }));
    var $link = $('[href=#'+$(this).attr('id')+']:first');
    $(this).prepend($('<span/>', {
        'class': 'modal-title light ' + $link.attr('class'),
        'text': $link.text()
    }));
});
$('#modals').append($overlay);



$('.open-modal').on('click', function(e){
    $overlay.show();
    $($(this).attr('href')).show(0, function(){
        $(this).find('input:visible, select, textarea').first().focus();
    });
    if(!$('html').hasClass('enable-mobile-menu'))
        $('html').addClass('dropdown-active');

    e.preventDefault();
    e.stopPropagation();
});

$('body').on('keydown', function(e){
    var $modal = $('#modals .modal:visible');
    if($modal.length > 0){
        // Espace close modal
        if(e.keyCode === 27){
            closeModal();
            e.stopPropagation();
        }

        // Tab do not go out modal
        if(e.keyCode === 9){
            var $current = $modal.find(':focus'),
                $tabbables = $modal.find(':tabbable'),
                nextIndex = e.shiftKey ? $tabbables.length - 1 : 0;

            if($current.length === 1){
                var currentIndex = $tabbables.index($current);
                if(e.shiftKey){
                    if(currentIndex > 0)
                        nextIndex = currentIndex - 1;
                } else {
                    if(currentIndex + 1 < $tabbables.length)
                        nextIndex = currentIndex + 1;
                }
            }

            $tabbables.eq(nextIndex).focus();
            e.stopPropagation();
            e.preventDefault();
        }
    }
});

function closeModal($modal){
    $modal = $modal || $('#modals .modal:visible');
    $modal.fadeOut(150);
    $overlay.fadeOut(150);
    $('html').removeClass('dropdown-active');
}