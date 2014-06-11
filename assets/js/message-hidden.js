/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Toggle message content for staff
   ========================================================================== */

(function($){
    "use strict";
    
    $("[href^=#show-message-hidden]").click(function(){
        $(this).parents(".message:first").find(".message-hidden-content").toggle();
    });
})(jQuery);