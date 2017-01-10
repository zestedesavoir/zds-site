

$(document).ready(function () {
    console.log('oooooo');
    
	$('#compare').mergely({
		width: 'auto',
		height: 400,
		sidebar: false,
		cmsettings: { readOnly: false, lineNumbers: true },
		lhs: function(setValue) {
			setValue($("#your_introduction").html());
		},
		rhs: function(setValue) {
			setValue($("#id_introduction").text());
		}
	});
	
	$("#compare-editor-lhs").append('Votre Version');
	$("#compare-editor-rhs").append('La version courante');
	
	
	
	/**
     * Merge introduction
     */
    $(".merge-btn").on("click", function(e){
    	console.log('click');
    	e.stopPropagation();
        e.preventDefault();
        // var $form = $(this).parents("form:first");
        var button = $(this);
        
        console.log(button);
        
        var classList = button.attr('class').split(/\s+/);
        console.log(classList);
		for (var i = 0; i < classList.length; i++) {
			// Pour un POC on pourrait faire plus simple, mais je m'intéresse au cas ou il y aura plusieurs
			// boutons par page, voila un moyen de les différencier.
			// on pourrait probablement automatiser ça avec une regex ou autre
		    if (classList[i] === 'need-to-merge-introduction') {
		        $intro = $("#id_introduction");
		        $to_merge = $("#compare").mergely('get','rhs');
		        $intro.val($to_merge);
		        
		        console.log($intro.val());
		        // TODO : un bon petit alert des familles
		        alert('Contenu bien mergé');
		    }
		}
    });
	
});
