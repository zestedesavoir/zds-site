(function($, undefined) {
    "use strict";
	
	$(document).ready(function () {
		
		/**
		 * Sets up the merge interface (using mergely). 
		 */
		function mergelySetUp(div, left, right)
		{
			div.mergely({
				width: "auto",
				height: 400,
				sidebar: false,
				cmsettings: { readOnly: false, lineNumbers: true, lineWrapping: true },
				lhs: function(setValue) {
					setValue(left.html());
				},
				rhs: function(setValue) {
					setValue(right.html());
				}
			});
		}

		mergelySetUp($(".compare-introduction"),$("#your_introduction"),$("#id_introduction"));
		mergelySetUp($(".compare-conclusion"),$("#your_conclusion"),$("#id_conclusion"));

		$("#compare-editor-lhs").append("Votre Version");
		$("#compare-editor-rhs").append("La version courante");
		
		
		/**
	     * Merge content
	     */
	    $(".merge-btn").on("click", function(e){

	    	e.stopPropagation();
	        e.preventDefault();
	        
	        var button = $(this);
	        var classList = button.attr("class").split(/\s+/);
	        
			for (var i = 0; i < classList.length; i++) {
			    if (classList[i].indexOf("need-to-merge-") >= 0) {
	
			    	// Cut the string to get the ending part
			    	var substring = classList[i].substring(14);
			    	
			        var $intro = $("#id_" + substring);
			        var $toMerge = $(".compare-" + substring).mergely("get","rhs");
			        $intro.val($toMerge);
			        
	
					// Display confirmation message
	                var msg = "<div class='alert-box success'>" + 
	                                "<span>Le merge a bien été effectué</span>" + 
	                                "<a href='#close-alert-box' class='close-alert-box ico-after cross white'>Masquer l'alerte</a>" +
	                           "</div>";
	                            
	                 button.before(msg);
			    }
			}
	    });
		
	});
})(jQuery);
