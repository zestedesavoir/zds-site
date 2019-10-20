
(function($, undefined) {
    "use strict";
    let shareModal = $("#share-to-mastodon");

    shareModal.find("input[name='instance']").on("change paste keyup", function() {
        // start by chars (https://)
        if(this.value.startsWith("https://")) {
            shareButton.prop("disabled", false);
        } else {
            shareButton.prop("disabled", true);
        }
    });

    $form.on("submit", function() {
        $form.attr("action", shareModal.find("input[name='instance']").val() + "/share");
    });
})(jQuery);
