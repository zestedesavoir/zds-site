/* ===== Zeste de Savoir ====================================================
   Toggle message content for staff
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $("[href^=#show-message-hidden]").click(function(){
        $(this).parents(".message:first").find(".message-hidden-content").toggle();
    });
})(jQuery);