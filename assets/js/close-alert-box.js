/* ===== Zeste de Savoir ====================================================
   Close alert-boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $(".main").on("click", ".close-alert-box:not(.open-modal)", function(e) {
        $(this).parents(".alert-box:first").slideUp(150, function(){
            $(this).remove();
        });
        $(this).parents(".markdown-help:first").slideUp(150, function(){
            $(this).remove();
        });
        e.preventDefault();
    });
})(jQuery);
