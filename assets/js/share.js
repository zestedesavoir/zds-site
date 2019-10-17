
(function($, undefined) {
    "use strict";
    var shareModal = $("#share-to-mastodon");
    var shareButton = shareModal.find("button");

    shareModal.find("input[name='instance']").on("change paste keyup", function() {
        // start by chars (https://)
        if(this.value.startsWith("https://")) {
            shareButton.attr("disabled", false);
        } else {
            shareButton.attr("disabled", true);
        }
    });

    shareButton.on("click", function() {

        var instance = shareModal.find("input[name='instance']").val();
        var text = shareModal.find("input[name='text']").val();
        var mastodonUrl = instance + "/share?text=" + encodeURIComponent(text);

        window.open(mastodonUrl);
    });
})(jQuery);
