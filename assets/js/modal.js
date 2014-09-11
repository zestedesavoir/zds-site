/* ===== Zeste de Savoir ====================================================
   Manage modals boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined){
    "use strict";
    
    var $overlay = $("<div/>", {
        "id": "modals-overlay"
    }).on("click", function(e){
        closeModal();
        e.preventDefault();
        e.stopPropagation();
    });

    var $modals = $("body").append($("<div/>", { "id": "modals" }));
    $modals.append($overlay);

    function buildModals($elems){
        $elems.each(function(){
            $("#modals").append($(this).addClass("tab-modalize"));
            $(this).append($("<a/>", {
                "class": "btn btn-cancel " + ($(this).is("[data-modal-close]") ? "btn-modal-fullwidth" : ""),
                "href": "#close-modal",
                "text": $(this).is("[data-modal-close]") ? $(this).attr("data-modal-close") : "Annuler"
            }).on("click", function(e){
                closeModal();
                e.preventDefault();
                e.stopPropagation();
            }));
            var $link = $("[href=#"+$(this).attr("id")+"]:first");
            var linkIco = $link.hasClass("ico-after") ? " light " + $link.attr("class").replace(/btn[a-z-]*/g, "") : "";
            $(this).prepend($("<span/>", {
                "class": "modal-title" + linkIco,
                "text": $link.text()
            }));
        });
    }

    $("body").on("click", ".open-modal", function(e){
        $overlay.show();
        $($(this).attr("href")).show(0, function(){
            $(this).find("input:visible, select, textarea").first().focus();
        });
        if(!$("html").hasClass("enable-mobile-menu"))
            $("html").addClass("dropdown-active");

        e.preventDefault();
        e.stopPropagation();
    });

    $("body").on("keydown", function(e){
        // Escape close modal
        if($(".modal:visible", $modals).length > 0 && e.which === 27){
            closeModal();
            e.stopPropagation();
        }
    });

    function closeModal(){
        $(".modal:visible", $modals).fadeOut(150);
        $overlay.fadeOut(150);
        $("html").removeClass("dropdown-active");
    }


    $(document).ready(function(){
        buildModals($(".modal"));
        $("#content").on("DOMNodeInserted", ".modal", function(e){
            buildModals($(e.target));
        });
    });
})(document, jQuery);