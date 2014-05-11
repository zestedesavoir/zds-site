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
    $(this).prepend($('<a/>', {
        'class': 'btn btn-cancel',
        'href': '#close-modal',
        'text': "Annuler"
    }).on('click', function(e){
        closeModal($(this).parents('.modal:first'));
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
    $($(this).attr('href')).show();
    $('html').addClass('dropdown-active');

    e.preventDefault();
    e.stopPropagation();
});

function closeModal($modal){
    $modal.fadeOut(150);
    $overlay.fadeOut(150);
    $('html').removeClass('dropdown-active');
}