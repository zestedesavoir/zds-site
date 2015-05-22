/**
 * Used by recovering password and send again validation email functionality.
 */
(function($, undefined) {
    "use strict";

    if($("body").hasClass("form-email-username")) {
        var $emailInput = $("#id_email"),
            $emailForm = $("#form-email"),
            $emailButton = $("[data-form-email-username-button=email]");

        var $usernameInput = $("#id_username"),
            $usernameForm = $("#form-username"),
            $usernameButton = $("[data-form-email-username-button=username]");

        if ($emailInput.val() === "") {
            $emailForm.addClass("hidden");
        }
        else {
            $emailForm.removeClass("hidden");
        }

        $emailButton.on("click", function(e) {
            $emailForm.toggleClass("hidden");
            $usernameForm.addClass("hidden");

            $usernameInput.val("");

            e.preventDefault();
        });

        if ($usernameInput.val() === "") {
            $usernameForm.addClass("hidden");
        }
        else {
            $usernameForm.removeClass("hidden");
        }

        $usernameButton.on("click", function(e) {
            $usernameForm.toggleClass("hidden");
            $emailForm.addClass("hidden");

            $emailInput.val("");

            e.preventDefault();
        });
    }
})(jQuery);

