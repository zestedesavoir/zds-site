(function ($, undefined) {
    var $opinions = $(".opinion");
    $opinions.on("click", ".unpick-action", function () {
       var $button = $(this);
       var $row = $button.parent().parent();
       var csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val();
       var data = {
           csrfmiddlewaretoken: csrfmiddlewaretoken
       };
       if ($button.data("operation")) {
           data.operation = $button.data("operation");
       }
       $.post($button.attr("data-url"), data).done(function () {
           if (data.operation) {
               $row.remove();
           }
           else {
               $button.prop("disabled", true);
               var $stateCol = $row.find(".state");
               $stateCol.text($stateCol.data("toogle"));
           }
       });
    });
})(jQuery);
