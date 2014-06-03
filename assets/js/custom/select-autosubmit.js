/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Auto submit forms
   ========================================================================== */

$(".select-autosubmit").change(function() {
    $(this).parents('form:first').submit();
});