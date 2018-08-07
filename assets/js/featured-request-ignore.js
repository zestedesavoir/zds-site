(function ($, undefined) {
    var $featuredRequest = $(".featured-request");
    $featuredRequest.on("click", ".unpick-action", function () {
        var $button = $(this);
        var $row = $button.parent().parent();
        var $table = $row.parent();
        var csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val();
        var operation = $button.data("operation");
        var data = {
            csrfmiddlewaretoken: csrfmiddlewaretoken
        };
        if (operation) {
            data.operation = $button.data("operation");
        }
        $.post($button.attr("data-url"), data).done(function (result) {
            if (result.result === "OK") {
                if (operation === "REJECT") {
                    $row.remove();
                    if ($table.find("tr").length === 0) {
                        $table.append("<tr><td colspan=\"4\"><i>Plus rien à afficher pour le moment !</i></td></tr>");
                    }
                }
                else {
                    $button.toggleClass("cross hide");
                    $button.text("Ignorer");
                    $button.data("operation", "REJECT");
                }
            }
            else {
                $button.prop("disabled", true);
            }
        });
    });
})(jQuery);
