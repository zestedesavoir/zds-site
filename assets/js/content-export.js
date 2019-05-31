(function ($) {
    $("[data-export-button]").click(function (e) {
        e.preventDefault();
        var $button = $(e.target);
        var url = $button.data("export-button");
        var csrf = $("input[name=csrfmiddlewaretoken]").val();
        $button.prop("disabled", true);
        $.ajax(url, {
            method: "POST",
            headers: {
               "X-CSRFToken": csrf,
            },
            data: {},
        });
    });
})(jQuery);
