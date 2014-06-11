/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Simulate click on element from another
   ========================================================================== */

(function($){
    "use strict";
    
    $("[data-click]").on("click focus", function(e){
        if(!($(this).hasClass("dont-click-if-sidebar") && $(".header-container .mobile-menu-btn").is(":visible"))){
            e.preventDefault();
            e.stopPropagation();
            $("#" + $(this).attr("data-click")).trigger("click");
        }
    });
})(jQuery);