$("form[action*='/membres/connexion'], form[action*='/membres/inscription']").submit(function() {
    $(this).attr("action", "https://" + window.location.hostname + window.location.pathname + window.location.search);
});
