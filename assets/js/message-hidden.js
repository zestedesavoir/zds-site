/* ===== Zeste de Savoir ====================================================
   Toggle message content for staff
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    $("#content [href^='#show-message-hidden']").on("click", function(e){
        $(this).parents(".message:first").find(".message-hidden-content").toggle();
		e.preventDefault();
    });
})(jQuery);
