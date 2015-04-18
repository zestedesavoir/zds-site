/**
 * Display the form for recorvering a password.
 */
(function($, undefined){
    "use strict";
    if ($("#id_email").val() === "")
        $("#form-email").addClass("hidden");
    else
        $("#form-email").removeClass("hidden");

    $("[data-forgot-password-button=email]").on("click", function(e) {
        $("#form-email").toggleClass("hidden");
        $("#form-username").addClass("hidden");

        $("#id_username").val("");

        e.preventDefault();
    });

    if ($("#id_username").val() === "")
        $("#form-username").addClass("hidden");
    else
        $("#form-username").removeClass("hidden");

    $("[data-forgot-password-button=username]").on("click", function(e) {
        $("#form-username").toggleClass("hidden");
        $("#form-email").addClass("hidden");

        $("#id_email").val("");

        e.preventDefault();
    });
})(jQuery);

