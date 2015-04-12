/* ===== Zeste de Savoir ====================================================
   Suggest Topice when user makes topic
   ---------------------------------
   Author: A-312
   ========================================================================== */

(function($, undefined) {
	"use strict";

	if (!$("#topic-suggest")[0])
		return;

    var __TIMEOUT_Hidden = 0,
        __TIMEOUT_Call = 0;

	var myHandler = function() {
		var titleURI = encodeURIComponent($(this).val()),
            $container = $("#topic-result-container");

        var solvedTopicsURL = $("div[data-solved-topics-url]").data("solved-topics-url");

        if (titleURI === "")
            return;

		if ($container.data("ajax-load") !== true) {
			$.getJSON(solvedTopicsURL + "?q=" + titleURI, function(json) {
				var $ul = $("<ul></ul>"),
					$title = null,
                    count = 0;

                // clearTimeout
                clearTimeout(__TIMEOUT_Hidden);
                clearTimeout(__TIMEOUT_Call);

				$.each(json, function(pk, topic) {
					$title = $("<a></a>").attr("target", "_blank");
					$title.text(topic.title).attr("href", topic.url).attr("title", topic.subtitle);

					$("<li></li>").text(" de " + topic.author).prepend($title).appendTo($ul);
                    count++;
				});
                if (!count) {
					$("<li></li>").addClass("neither").text($container.data("neither")).appendTo($ul);
                    __TIMEOUT_Hidden = setTimeout(function () {
                        $("#topic-suggest").hide(800);
                    }, 6000)
                }
				$container.html("").append($ul);

				$container.data("ajax-load", false);
                $("#topic-suggest").show(800);
			});

			$container.data("ajax-load", true);
		}
	};

    $("#id_title").on("blur", myHandler);

    $("#id_title").on("keypress", function() {
        var that = this,
            length = $(this).val().length;

        clearTimeout(__TIMEOUT_Call);
        __TIMEOUT_Call = setTimeout(function () {
            myHandler.call(that);
        }, (length < 5) ? (12 - length * 2) * 1000 : 2000); // ANTI-FLOOD
    });
})(jQuery);