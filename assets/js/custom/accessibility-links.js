/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Managment of accessibility links
   ========================================================================== */

$('.accessibility a').on('focus', function(){
	$('.dropdown:visible').parent().find('.active').removeClass('active');
    $('.accessibility').addClass('focused');
});
$('.accessibility a').on('blur', function(){
    $('.accessibility').removeClass('focused');
});