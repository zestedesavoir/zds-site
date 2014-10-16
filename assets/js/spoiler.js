/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined){
    "use strict";
    
    function buildSpoilers($elem){
        $elem.each(function(){
            $(this).addClass("spoiler-build");
            $(this).before($("<a/>", {
                text: "Afficher/Masquer le contenu masqué",
                class: "spoiler-title ico-after view",
                href: "#",
                click: function(e){
                    $(this).next(".spoiler").toggle();
                    e.preventDefault();
                }
            }));
        });
    }

    $(document).ready(function(){
        buildSpoilers($("#content .spoiler"));
        $("#content").on("DOMNodeInserted", ".spoiler", function(e){
            if($(e.target).is(".spoiler:not(.spoiler-build)")){
                buildSpoilers($(e.target));
            }
        });
    });
})(document, jQuery);