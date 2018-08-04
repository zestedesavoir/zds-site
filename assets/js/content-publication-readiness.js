(function ($) {
   $(".readiness").on("click", function (e) {
       var url = $(e.target).data("url");
       var readiness = $(e.target).data("is-ready").toString() === "true";
       var csrf = $("input[name=csrfmiddlewaretoken]").val();
       var toggledReadiness = !readiness;
       $.ajax(url, {method: "PUT", data: {
           "ready_to_publish": toggledReadiness,
           "container_slug": $(e.target).data("container-slug"),
           "parent_container_slug": $(e.target).data("parent-container-slug") || ""
       }, success: function () {
           var readinessAsString = String(toggledReadiness);
           var newDisplayedText = $(e.target).data("is-ready-" + readinessAsString);
           $(e.target).attr("data-is-ready", readinessAsString)
               .text(newDisplayedText);
       }, headers: {
           "X-CSRFToken": csrf
       }});
   });
})($);
