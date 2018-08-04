(function ($, undefined) {
    var $featured_request = $(".featured-request");
    $featured_request.on("click", ".unpick-action", function () {
        var $button = $(this);
        var $row = $button.parent().parent();
        var csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val();
        var operation = $button.data("operation");
        var data = {
            csrfmiddlewaretoken: csrfmiddlewaretoken
        };
        if (operation) {
            data.operation = $button.data("operation");
        }
        $.post($button.attr("data-url"), data).done(function (result) {
            if (result.result === 'OK') {
                if (operation === 'REJECT') {
                    $row.remove();
                }
                else {
                    $button.toggleClass('cross hide');
                    $button.text('Ignorer');
                    $button.data('operation', 'REJECT');
                }
            }
            else {
                $button.prop("disabled", true);
            }
        });
    });
})(jQuery);
