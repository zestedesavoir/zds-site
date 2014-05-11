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
        'class': 'btn btn-cancel',
        'href': '#close-modal',
        'text': "Annuler"
    }).on('click', function(e){
        closeModal();
        e.preventDefault();
        e.stopPropagation();
    }));
    $(this).prepend($('<span/>', {
        'class': 'modal-title',
        'text': $('[href=#'+$(this).attr('id')+']:first').text()
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
    if($('#modals .modal:visible').length > 0){
        // Espace close modal
        if(e.keyCode == 27){
            closeModal();
            e.stopPropagation();
        }

        // Tab do not go out modal
        if(e.keyCode == 9){
            $next = $('#modals .modal:visible :focus').next(':tabbable');
            if($next.length == 0)
                $next = $('#modals .modal:visible :tabbable:first');
            $next.focus();
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