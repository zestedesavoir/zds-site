/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Dropdown menu open/close
   ========================================================================== */
var dropdownMouseDown = false;

$('.dropdown').each(function(){
	$elem = $(this).parent().find('> a');

	if(!$elem.parents('.logbox').length)
		$elem.addClass('has-dropdown');

	$elem
	.on('mousedown', function(){
		dropdownMouseDown = true;
	})
	.on('mouseup', function(){
		dropdownMouseDown = false;
	})
	.on('click', function(e){
		e.preventDefault();
		e.stopPropagation();

		if(!$(this).hasClass('active')){
			activeDropdown($(this));
			$(this).off('blur');
		} else {
			$(this).removeClass('active');
			triggerCloseDropdown($(this));
		}
	})
	.on('focus', function(e){
		e.preventDefault();

		if(!dropdownMouseDown && !$(this).hasClass('active')){
			activeDropdown($(this));
			
			$(this)
			.one('blur', function(e){
				$elem = $(this);
				setTimeout(function(){
					if($('a:focus', $elem.parent().find('.dropdown')).length){
						$('a:last', $elem.parent().find('.dropdown')).one('blur', function(){
							$elem.removeClass('active');
							triggerCloseDropdown($elem);
						});
					} else {
						$elem.removeClass('active');
						triggerCloseDropdown($elem);
					}
				}, 10);
			})
			.one('mousemove', function(){
				$(this).off('blur');
			});
		}
	});
});

$('.dropdown-list').on('focus', function(){
	$(this).find('a:first').focus();
});

$('body').on('keydown', function(e){
	if(e.keyCode == 27)
		$('body').trigger('click');
});

function activeDropdown($elem){
	$('body').trigger('click');
	$elem.addClass('active');
	$elem.parent().find('.dropdown-list').scrollTop(0);

	if($elem.is('[data-active]'))
		$('#' + $elem.attr('data-active')).addClass('active');

	if($elem.parents('.logbox').length)
		$('html').addClass('dropdown-active');

	triggerCloseDropdown($elem);
}
function triggerCloseDropdown($that){
	if($that.hasClass('active')){
		$('body').one('click', function(e){
			if(!$(e.target).hasClass('dropdown') && !$(e.target).parents('.dropdown').length) {
				$that.removeClass('active');

				if($that.is('[data-active]'))
					$('#' + $that.attr('data-active')).removeClass('active');
			}
			
			triggerCloseDropdown($that);
		});
	} else {
		$('html').removeClass('dropdown-active');
		$('body').off('click');
		$('.dropdown a').off('blur');

		if($that.is('[data-active]'))
			$('#' + $that.attr('data-active')).removeClass('active');
	}
}