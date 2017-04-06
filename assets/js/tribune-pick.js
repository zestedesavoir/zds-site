(function ($, undefined) {
    var $opinions = $(".opinion");
    $opinions.on("click", ".unpick-action", function () {
       var $button = $(this);
       var $row = $button.parent().parent();
       var csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val();
       $.post($button.attr("data-url"), {
           operation: $button.attr("data-operation"),
           csrfmiddlewaretoken: csrfmiddlewaretoken
       }).done(function () {
           $row.remove();
       });
    });
})(jQuery);
