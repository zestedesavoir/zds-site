(function($, undefined) {
    "use strict";
    $(".date_picker_field").each(function() {
        new Pikaday({
            field: $(this)[0],
            format: "YYYY-MM-DD"
        });
    });
})(jQuery);
