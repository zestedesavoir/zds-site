/* ===== Zeste de Savoir ====================================================
   Simulate click on element from another
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, document, undefined){
    "use strict";
    
    var dropdownMouseDown = false;

    function dataClick($elem){
        $elem
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
    }

    $(document).ready(function(){
        dataClick($("[data-click]"));
        $("#content").on("DOMNodeInserted", "[data-click]", function(e){
            dataClick($(e.target));
        });
    });
})(jQuery, document);