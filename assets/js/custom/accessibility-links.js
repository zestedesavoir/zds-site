/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Managment of accessibility links
   ========================================================================== */

$('.accessibility a').on('focus', function(){
    $('.accessibility').addClass('focused');
});
$('.accessibility a').on('blur', function(){
    $('.accessibility').removeClass('focused');
});