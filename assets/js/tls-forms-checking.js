$("form[action*='/membres/connexion'], form[action*='/membres/inscription']").submit(function() {
    /* If we want to enable TLS, then change the action to https:// */
    if($("#id_enable_tls").prop("checked")) {
	var newAction = "https://" + window.location.hostname + window.location.pathname+window.location.search;
	$(this).attr("action", newAction);
    }
});
