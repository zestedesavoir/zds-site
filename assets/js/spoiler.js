/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined) {
    "use strict";

    function buildSpoilers($elem) {
        $elem.each(function() {
            var $this = $(this);

            if(!$this.hasClass("spoiler-build")) {
                $this.before($("<a/>", {
                    text: "Afficher/Masquer le contenu masqué",
                    class: "spoiler-title ico-after view",
                    href: "#",
                    click: function(e) {
                        $(this).next(".spoiler").toggle();
                        e.preventDefault();
                    }
                }));
                $this.addClass("spoiler-build");
            }
        });
    }

    $(document).ready(function() {
        var $content = $("#content");
        buildSpoilers($content.find(".spoiler"));
        $content.on("DOMNodeInserted", function(e) {
            var $spoilers = $(e.target).find(".spoiler");
            return buildSpoilers($spoilers);
        });
    });
})(document, jQuery);
