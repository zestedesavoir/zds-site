/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Auto submit forms
   ========================================================================== */

(function($){
    "use strict";
    
    $(".select-autosubmit").change(function() {
        $(this).parents("form:first").submit();
    });
})(jQuery);