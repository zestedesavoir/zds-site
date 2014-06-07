/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Auto submit forms
   ========================================================================== */

(function($){
    $(".select-autosubmit").change(function() {
        $(this).parents('form:first').submit();
    });
})(jQuery);