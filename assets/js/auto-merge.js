

$(document).ready(function () {
    console.log('oooooo');
    
	$('.compare-introduction').mergely({
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
	
	$('.compare-conclusion').mergely({
		width: 'auto',
		height: 400,
		sidebar: false,
		cmsettings: { readOnly: false, lineNumbers: true },
		lhs: function(setValue) {
			setValue($("#your_conclusion").html());
		},
		rhs: function(setValue) {
			setValue($("#id_conclusion").text());
		}
	});
	
	// TODO a voir comment on peut factoriser ce code.
	
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
		    if (classList[i].indexOf('need-to-merge-') >= 0) {

		    	// Cut the string to get the ending part
		    	console.log(classList[i])
		    	var substring = classList[i].substring(14)
		    	
		    	// TODO : problème des retours à la ligne qui s'en vont (ou normal car markdown ?) ?
		        $intro = $("#id_" + substring);
		        $to_merge = $(".compare-" + substring).mergely('get','rhs');
		        $intro.val($to_merge);
		        
		        console.log($intro.val());
		        // TODO : un bon petit alert des familles
		        alert('Contenu bien mergé');
		    }
		}
    });
	
});
