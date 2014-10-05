/* ===== Zeste de Savoir ====================================================
   Dropdown menu open/close
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    var mouseDown = false,
        shiftHold = false;

    $(document).on("keydown keyup", function(e){
        shiftHold = e.shiftKey;
    });

    $(".dropdown").each(function(){
        var $dropdown = $(this),
            $elem = $(this).parent().find("> a");

        if(!$elem.parents(".logbox").length)
            $elem.addClass("has-dropdown");

        $elem
        .on("mousedown", function(){
            mouseDown = true;
        })
        .on("mouseup", function(){
            mouseDown = false;
        })
        .on("click", function(e){
            if(($(this).parents(".header-menu-list").length > 0 && parseInt($("html").css("width")) < 960))
                return true;

            e.preventDefault();
            e.stopPropagation();

            if(!$(this).hasClass("active")){
                activeDropdown($(this));
                $(this).off("blur");
            } else {
                $(this).removeClass("active");
                triggerCloseDropdown($(this));
            }
        })
        .on("focus", function(e){
            e.preventDefault();

            if(!mouseDown && !$elem.hasClass("active")){
                activeDropdown($elem);
                
                $elem
                .off("blur")
                .on("blur", function(){
                    $elem
                    .one("blur", function(){
                        if(shiftHold)
                            triggerCloseDropdown($elem);
                    });

                    setTimeout(function(){
                        if($(":tabbable:focus", $dropdown).length){
                            var listenBlurLast = function(){
                                $(":tabbable:last", $dropdown)
                                .one("blur", function(){
                                    if(shiftHold){
                                        listenBlurLast();
                                        return;
                                    }
                                    $elem.removeClass("active");
                                    triggerCloseDropdown($elem);
                                });
                            };
                            listenBlurLast();
                        } else {
                            $elem.removeClass("active");
                            triggerCloseDropdown($elem);
                        }
                    }, 10);
                })
                .one("mousemove", function(){
                    $(this).off("blur");
                });
            }
        });
    });

    $(".dropdown-list").on("focus", function(){
        $(this).find(":tabbable:first").focus();
    });

    $("body").on("keydown", function(e){
        if(e.which === 27)
            $(".has-dropdown.active, .ico-link.active, #my-account.active").focus().removeClass("active");
    });

    function activeDropdown($elem){
        $("body").trigger("click");
        $elem.addClass("active");
        $elem.parent().find(".dropdown-list").scrollTop(0);

        if($elem.is("[data-active]"))
            $("#" + $elem.attr("data-active")).addClass("active");

        if($elem.parents(".logbox").length)
            $("html").addClass("dropdown-active");

        triggerCloseDropdown($elem);
    }
    function triggerCloseDropdown($that){
        if($that.hasClass("active")){
            $("body").one("click", function(e){
                if(!$(e.target).hasClass("dropdown") && !$(e.target).parents(".dropdown").length) {
                    $that.removeClass("active");
                    $that.next(":tabbable").focus();

                    if($that.is("[data-active]"))
                        $("#" + $that.attr("data-active")).removeClass("active");
                }
                
                triggerCloseDropdown($that);
            });
        } else {
            $("html").removeClass("dropdown-active");
            $("body").off("click");
            $(".dropdown :tabbable").off("blur");

            if($that.is("[data-active]"))
                $("#" + $that.attr("data-active")).removeClass("active");
        }
    }
})(jQuery);