/* ===== Zeste de Savoir ====================================================
   Close alert-boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $(".close-alert-box:not(.open-modal)").on("click", function(e) {
        $(this).parents(".alert-box:first").slideUp(150, function(){
            $(this).remove();
        });
        e.preventDefault();
    });
})(jQuery);