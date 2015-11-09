/* ===== Zeste de Savoir ====================================================
   Single line/Multi lines signatures
   ========================================================================== */

(function($, undefined){
    "use strict";

    $(".message-bottom .signature").on("click", function(){
        $(this).toggleClass("full");
    });
})(jQuery);
