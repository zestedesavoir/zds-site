/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Close alert-boxes
   ========================================================================== */

$(".close-alert-box:not(.open-modal)").on('click', function(e) {
    $(this).parents('.alert-box:first').slideUp(150, function(){
    	$(this).remove();
    });
    e.preventDefault();
});