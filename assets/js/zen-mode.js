/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Zen mode for content-pages
   ========================================================================== */

(function($){
    "use strict";

    if($(".article-content").length > 0){
        $(".content-container .taglist + .authors").before($("<button/>", {
            "class": "btn btn-grey ico-after view open-zen-mode",
            "text": "Mode zen",
            "click": function(e){
                $(".content-container").toggleClass("zen-mode tab-modalize");
                $(this).blur();
                e.preventDefault();
                e.stopPropagation();
            }
        }));

        $("body").on("keydown", function(e){
            if($(".zen-mode").length > 0){
                // Escape close modal
                if(e.keyCode === 27){
                    $(".content-container").toggleClass("zen-mode tab-modalize");
                    $(this).blur();
                    e.stopPropagation();
                }
            }
        });
    }
})(jQuery);