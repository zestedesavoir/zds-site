/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Manage modals boxes
   ========================================================================== */

(function($){
    "use strict";
    
    var $overlay = $("<div/>", {
        "id": "modals-overlay"
    }).on("click", function(e){
        closeModal($("#modals .modal:visible"));
        e.preventDefault();
        e.stopPropagation();
    });

    $("body").append($("<div/>", { "id": "modals" }));
    $(".modal").each(function(){
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
    $("#modals").append($overlay);



    $(".open-modal").on("click", function(e){
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
        if($("#modals .modal:visible").length > 0){
            // Espace close modal
            if(e.keyCode === 27){
                closeModal();
                e.stopPropagation();
            }
        }
    });

    function closeModal($modal){
        $modal = $modal || $("#modals .modal:visible");
        $modal.fadeOut(150);
        $overlay.fadeOut(150);
        $("html").removeClass("dropdown-active");
    }
})(jQuery);