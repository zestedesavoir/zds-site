(function ($) {
    $(".export-button").click(function (e) {
        e.preventDefault();
        var $link = $(e.target);
        var url = $link.attr("href");
        var csrf = $("input[name=csrfmiddlewaretoken]").val();
        $link.prop("disabled", true);
        $.ajax(url, {
            method: "POST",
            headers: {
               "X-CSRFToken": csrf,
            },
            data: {},
        });
    });
})(jQuery);
