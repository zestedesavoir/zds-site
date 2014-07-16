/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $(".spoiler").each(function(){
        $(this).before($("<a/>", {
            "text": "Afficher/Masquer le contenu masqué",
            "class": "spoiler-title ico-after view",
            "href": "#",
            "click": function(e){
                $(this).next(".spoiler").toggle();
                e.preventDefault();
            }
        }));
    });
})(jQuery);