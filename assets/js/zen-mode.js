/* ===== Zeste de Savoir ====================================================
   Zen mode for content-pages
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    if($(".open-zen-mode").length > 0){
        $(".open-zen-mode").on("click", function(e){
                $(".content-container").toggleClass("zen-mode tab-modalize");
                $(this).blur();
                e.preventDefault();
                e.stopPropagation();
            }
        );

        $("body").on("keydown", function(e){
            // Escape close modal
            if($(".zen-mode").length > 0 && e.which === 27){
                $(".content-container").toggleClass("zen-mode tab-modalize");
                $(this).blur();
                e.stopPropagation();
            }
        });
    }
})(jQuery);