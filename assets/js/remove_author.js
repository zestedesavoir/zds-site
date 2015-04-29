(function(document, $, undefined){
    "use strict";

    var remove_buttons = $("#manage-author button");
    var username_input = $("#remove-username");
    remove_buttons.click(function(e){
                    username_input.val(remove_buttons.attr("data-value"));
                });
})(document, jQuery);