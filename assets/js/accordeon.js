/* ===== Zeste de Savoir ====================================================
   Accordeon for sidebar
   ---------------------------------
   Author: Alex-D
   ========================================================================== */

(function($, undefined){
    "use strict";

    function accordeon($elem){
        $("h4 + ul, h4 + ol", $elem).each(function(){
            if(!$(this).hasClass("unfolded")){
                if($(".current", $(this)).length === 0)
                    $(this).hide();
            }
        });

        $("h4", $elem).click(function(e){
            $("+ ul, + ol", $(this)).slideToggle(100);

            e.preventDefault();
            e.stopPropagation();
        });
    }
    
    $(document).ready(function(){
        $(".main .sidebar.accordeon, .main .sidebar .accordeon")
        .each(function(){
            accordeon($(this));
        })
        .on("DOMNodeInserted", function(e){
            accordeon($(e.target));
        });
    });
})(jQuery);