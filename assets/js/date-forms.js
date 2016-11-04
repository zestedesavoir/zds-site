(function($, undefined) {
    "use strict";
    $(".date_picker_field").each(function() {
        /* global Pikaday */
        new Pikaday({
            field: $(this)[0],
            format: "YYYY-MM-DD",
            minDate : new Date(),
            onOpen : function () {
                // correct the way to handle position in the case of modal flexbox
                var field = $(this._o.field);
                if (field.parents(".modal").length > 0) {
                    var offset = field.offset();
                    var $window = $(window);
                    var $el = $(this.el);
                    $el.css("position", "fixed");
                    $el.css("left", (offset.left - $window.scrollLeft()) + "px");
                    $el.css("top", (offset.top - $window.scrollTop() + field.height()) + "px");
                }
            }
        });
    });
})(jQuery);
