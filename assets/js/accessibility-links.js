/* ===== Zeste de Savoir ====================================================
   Managment of accessibility links
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    $("#accessibility a").on("focus", function(){
        $(".dropdown:visible").parent().find(".active").removeClass("active");
        $("#accessibility").addClass("focused");
    });
    $("#accessibility a").on("blur", function(){
        $("#accessibility").removeClass("focused");
    });
})(jQuery);