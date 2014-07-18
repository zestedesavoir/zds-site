/* ===== Zeste de Savoir ====================================================
   Accordeon for sidebar
   ---------------------------------
   Author: Alex-D
   ========================================================================== */

(function($){
    "use strict";
    
    $(".main .sidebar.accordeon, .main .sidebar .accordeon").each(function(){
        var $that = this;

        $("h4 + ul, h4 + ol", $that).each(function(){
            if($(".current", $(this)).length === 0)
                $(this).hide();
        });

        $("h4", $that).click(function(e){
            $("+ ul, + ol", $(this)).slideToggle(100);

            e.preventDefault();
            e.stopPropagation();
        });
    });
})(jQuery);