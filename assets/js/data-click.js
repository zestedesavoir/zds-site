/* ===== Zeste de Savoir ====================================================
   Simulate click on element from another
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    var dropdownMouseDown = false;
    
    $("body")
    .on("mousedown", "[data-click]", function(){
        dropdownMouseDown = true;
    })
    .on("mouseup", "[data-click]", function(){
        dropdownMouseDown = false;
    })
    .on("click focus", "[data-click]", function(e){
        if(e.type === "focus" && dropdownMouseDown)
            return false;

        if(!($(this).hasClass("dont-click-if-sidebar") && $(".header-container .mobile-menu-btn").is(":visible"))){
            e.preventDefault();
            e.stopPropagation();
            $("#" + $(this).attr("data-click")).trigger("click");
        }
    });
})(jQuery);