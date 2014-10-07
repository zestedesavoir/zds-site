/* ===== Zeste de Savoir ====================================================
   Prevent from double clic on submit buttons
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    $("body").on("submit", "form", function(){
    	$("button", $(this)).attr("disabled", true);
    });
})(jQuery);