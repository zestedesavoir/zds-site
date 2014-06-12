/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Search for solved topics when create a new topic
   ========================================================================== */

var $solvedTopicsElem = $('main [data-solved-topics-url]');
if($solvedTopicsElem.length > 0){
	var solvedTopicsUrl = $solvedTopicsElem.attr('data-solved-topics-url');
	// TODO : back-end HS, impossible de dev ça pour l'instant
}