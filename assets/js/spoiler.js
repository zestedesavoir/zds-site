/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Toggle spoiler content
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