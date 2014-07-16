/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Simulate click on element from another
   ========================================================================== */

(function($){
    "use strict";
    
    var dropdownMouseDown = false;
    
    $("[data-click]")
    .on("mousedown", function(){
        dropdownMouseDown = true;
    })
    .on("mouseup", function(){
        dropdownMouseDown = false;
    })
    .on("click focus", function(e){
        if(e.type === "focus" && dropdownMouseDown)
            return false;

        if(!($(this).hasClass("dont-click-if-sidebar") && $(".header-container .mobile-menu-btn").is(":visible"))){
            e.preventDefault();
            e.stopPropagation();
            $("#" + $(this).attr("data-click")).trigger("click");
        }
    });
})(jQuery);