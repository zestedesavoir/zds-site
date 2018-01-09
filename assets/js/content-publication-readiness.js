(function ($, undefined) {
   $("li").on("click", ".readiness", function (e) {
       var url = $(e.target).data("url");
       var readiness = $(e.target).data("is-ready") === "true";
       var csrf = $("input[name=csrfmiddlewaretoken]").val();

       $.ajax(url, {method: "PUT", data: {
           "ready_to_publish": readiness,
           "container_slug": $(e.target).data("container-slug"),
           "parent_container_slug": $(e.target).data("parent-container-slug") || ""
       }, success: function () {
           $(e.target).data("is-ready", readiness?"false":"true")
               .children("span")
               .removeClass("glyphicon-remove-sign")
               .removeClass("glyphicon-ok-sign")
               .addClass(readiness?"glyphicon-remove-sign":"glyphicon-ok-sign");
       }, headers: {
           "X-CSRFToken": csrf
       }});
   });
})($);
