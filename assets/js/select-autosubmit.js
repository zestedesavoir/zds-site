/* ===== Zeste de Savoir ====================================================
   Auto submit forms
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($){
    "use strict";
    
    $(".select-autosubmit").change(function() {
        $(this).parents("form:first").submit();
    });
})(jQuery);