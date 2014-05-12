$('a[href=#en-savoir-plus]').on('click', function(e){
	e.preventDefault();
	$('main section:not(#en-savoir-plus)').fadeOut(150, function(){
		$('#en-savoir-plus').fadeIn(200);
	});
});

$('a[href=#retour]').on('click', function(e){
	e.preventDefault();
	$('#en-savoir-plus').fadeOut(150, function(){
		$('main section:not(#en-savoir-plus)').fadeIn(200);
	});
});