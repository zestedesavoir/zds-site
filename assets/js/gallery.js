/* ===== Zeste de Savoir ====================================================
   Gallery list and grid views management
   ---------------------------------
   Author: Sandhose / Quentin Gliech
   ========================================================================== */

(function($){
    "use strict";

    var $btn = $(".toggle-gallery-view"),
        $galleryView = $(".gallery");

    var updateBtn = function(){
        $btn.text($galleryView.hasClass("list-view") ? "Vue grille" : "Vue liste");
    };

    if($btn.length > 0){
        $btn.on("click", function(){
            if($galleryView.hasClass("list-view")) 
                $galleryView.removeClass("list-view").addClass("grid-view");
            else 
                $galleryView.removeClass("grid-view").addClass("list-view");
            updateBtn();
        });

        updateBtn();
    }

    var updateCheckbox = function(){
        if(this.checked) $(this).parents(".gallery-item").addClass("selected");
        else $(this).parents(".gallery-item").removeClass("selected");
    };

    if($galleryView.length > 0){
        $(".gallery-item input[type=checkbox]")
            .on("change", updateCheckbox)
            .each(updateCheckbox)
        ;
    }
})(jQuery);
