
(function($, undefined) {
    "use strict";
    let shareModal = $("#share-to-mastodon");
    let shareButton = shareModal.find("button");

    shareModal.find("input[name='instance']").on("change paste keyup", function() {
        // start by chars (https://)
        if(this.value.startsWith("https://")) {
            shareButton.prop("disabled", false);
        } else {
            shareButton.prop("disabled", true);
        }
    });

    shareButton.on("click", function() {
        let instance = shareModal.find("input[name='instance']").val();
        let text = shareModal.find("input[name='text']").val();
        let mastodonUrl = instance + "/share?text=" + encodeURIComponent(text);
        window.open(mastodonUrl);
    });
})(jQuery);
