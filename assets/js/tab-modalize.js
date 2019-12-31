/* ===== Zeste de Savoir ====================================================
   Keyboad accessibility for overlayed boxes (modals, etc)
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $("body").on("keydown", function(e){
        var $modal = $(".tab-modalize:visible");
        if($modal.length > 0){
            // Tab do not go out modal
            if(e.which === 9){
                var $current = $modal.find(":focus"),
                    $tabbables = $modal.find(":tabbable"),
                    nextIndex = e.shiftKey ? $tabbables.length - 1 : 0;

                if($current.length === 1){
                    var currentIndex = $tabbables.index($current);
                    if(e.shiftKey){
                        if(currentIndex > 0)
                            nextIndex = currentIndex - 1;
                    } else {
                        if(currentIndex + 1 < $tabbables.length)
                            nextIndex = currentIndex + 1;
                    }
                }

                $tabbables.eq(nextIndex).focus();
                e.stopPropagation();
                e.preventDefault();
            }
        }
    });
})(jQuery);
