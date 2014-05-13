/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Keyboard navigation in navigables lists, with j/k keys
   ========================================================================== */

var $list = $('.navigable-list');

if($list.length == 1){
	$('body').on('keydown', function(e){
		if(e.keyCode == 74 || e.keyCode == 75){
			if($list.find('.navigable-elem.active').length == 0){
				activeNavigableElem($list.find('.navigable-elem:first'));
				return;
			}

			var $old = $list.find('.navigable-elem.active');
			var $next;
			if(e.keyCode == 74){ // J
				$next = $old.next('.navigable-elem:first');
			} else if(e.keyCode == 75) { // K
				$next = $old.prev('.navigable-elem:first');
			}

			if ($next.length == 0)
				return false;

			$old.removeClass('active');
			activeNavigableElem($next);
		}
	});

	$list.find('.navigable-link').on('focus', function(){
		if(!$(this).parents('.navigable-elem:first').hasClass('active')){
			$list.find('.navigable-elem.active').removeClass('active');
			activeNavigableElem($(this).parents('.navigable-elem'));
		}
	});
	$list.find('.navigable-link').on('blur', function(){
		$(this).parents('.navigable-elem:first').removeClass('active');
	});
} else if($list.length > 1){
	console.error("There is more than one .navigable-list element in this page !");
}

function activeNavigableElem($elem){
	$elem
		.addClass('active')
		.find('.navigable-link')
			.focus();
}