(function ($) {
    $("[data-export-button]").click(function (e) {
        e.preventDefault();
        const $button = $(e.target);
        const url = $button.data("export-button");
        const csrf = $("input[name=csrfmiddlewaretoken]").val();
        $button.prop("disabled", true);
        $button.prop("aria-busy", true);
        $.ajax(url, {
            method: "POST",
            headers: {
               "X-CSRFToken": csrf,
            },
            data: {},
        }).done(() => {
            $button.prop("disabled", false);
            $button.text($button.attr("data-success-text"));
            $button.prop("aria-busy", false);
            setTimeout(() => $button.text($button.attr("data-base-text")), 5000);
        }).fail(() => {
            $button.prop("disabled", false);
            $button.text($button.attr("data-error-text"));
            $button.prop("aria-busy", false);
            setTimeout(() => $button.text($button.attr("data-base-text")), 5000);
        });
    });
})(jQuery);
