/* ===== Zeste de Savoir ====================================================
   Managment of accessibility links
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    $("#accessibility a").on("focus", function() {
        $(".dropdown:visible").parent().find(".active").removeClass("active");
        $("#accessibility").addClass("focused");
    }).on("blur", function() {
        $("#accessibility").removeClass("focused");
    }).on("click", function() {
        var link = $(this).attr("href");
        setTimeout(function() { // Forces the focus on next tick
            $(link).find(":tabbable").first().focus(); // Focus the first focusable element
        });
    });
})(jQuery);
