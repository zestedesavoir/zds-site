/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined) {
    "use strict";

    function buildSpoilers($elem) {
        $elem.each(function() {
            $(this).addClass("spoiler-build");
            $(this).before($("<a/>", {
                text: "Afficher/Masquer le contenu masqué",
                class: "spoiler-title ico-after view",
                href: "#",
                click: function(e) {
                    $(this).next(".spoiler").toggle();
                    e.preventDefault();
                }
            }));
        });
    }

    $(document).ready(function() {
        var $content = $("#content");
        buildSpoilers($content.find(".spoiler"));
        $content.on("DOMNodeInserted", function() {
            var $spoilers = $(this).find(".spoiler:not(.spoiler-build)");
            if ($spoilers.length > 0)
                return buildSpoilers($spoilers);
            else if ($(this).is(".spoiler:not(.spoiler-build)"))
                return buildSpoilers($(this));
        });
    });
})(document, jQuery);