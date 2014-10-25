/* ===== Zeste de Savoir ====================================================
   Prevent from double clic on submit buttons
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    var buttonsSelector = "[type=submit], [type=reset]";

    $("body").on("submit", "form", function(){
        $(buttonsSelector)
            .addClass("disabled");

        $(buttonsSelector, $(this))
            .addClass("submitted")
            .append($("<span/>", { class: "line-loading" }));
    });
    $("form").on("click", buttonsSelector, function(e){
        if($(this).hasClass("disabled"))
            e.preventDefault();
    });
})(jQuery);