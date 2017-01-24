(function($, undefined) {
    "use strict";

	$(document).ready(function () {

		/**
		 * Sets up the merge interface (using mergely) in the $div Object. Data is generally retrieved from a form field
		 * or an aditionnal div exposing the old data, also generated in the form.
		 * @param {Object} $div - The base object used to set up the interface. Generally created in forms files.
         * @param {Object} $left - The object from which we will pick the content to put in the left hand side (lhs) of the editor.
         * @param {Object} $right - The object from which we will pick the content to put in the right hand side (rhs) of the editor.
		 */
		function mergelySetUp($div, $left, $right)
		{
			$div.mergely({
				width: "auto",
				height: 400,
				sidebar: false,
				cmsettings: { readOnly: false, lineNumbers: true, lineWrapping: true },
				lhs: function(setValue) {
					setValue($left.html());
				},
				rhs: function(setValue) {
					setValue($right.html());
				}
			});
		}

		mergelySetUp($(".compare-introduction"),$("#your_introduction"),$("#id_introduction"));
		mergelySetUp($(".compare-conclusion"),$("#your_conclusion"),$("#id_conclusion"));
		mergelySetUp($(".compare-text"),$("#your_text"),$("#id_text"));

		$("#compare-editor-lhs").append("Votre Version");
		$("#compare-editor-rhs").append("La version courante");


		/**
	     * Merge content
	     */
	    $(".merge-btn").on("click", function(e){

	    	e.stopPropagation();
	        e.preventDefault();

	        var button = $(this);

			Array.from(this.classList).forEach(function(element){
				if (element.indexOf("need-to-merge-") >= 0) {

			    	// Cut the string to get the ending part
			    	var substring = element.substring(14);

			        var $intro = $("#id_" + substring);
			        var $toMerge = $(".compare-" + substring).mergely("get","rhs");
			        $intro.val($toMerge);

					// Confirmation message
	                var msg = "<div class='alert-box success alert-merge'>" +
	                                "<span>Le contenu a bien été validé.</span>" +
	                                "<a href='#close-alert-box' class='close-alert-box ico-after cross white'>Masquer l'alerte</a>" +
	                           "</div>";

					button.before(msg);

					setTimeout(function() {
					    $('.alert-merge').fadeOut('fast');
					}, 2000);
					
			    }

			});

	    });

	});
})(jQuery);
