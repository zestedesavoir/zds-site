$("form[action*='/membres/connexion'], form[action*='/membres/inscription']").submit(function() {
    /* If the "Enable TLS cipher is checked, change the action into https:// */
    if($("#id_enable_tls").prop("checked")) {
	var newAction = "https://" + window.location.hostname + window.location.pathname+window.location.search;
	$(this).attr("action", newAction);
    }
});
