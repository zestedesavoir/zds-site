/* ===== Zeste de Savoir ====================================================
   Go to top button
   ========================================================================== */

(function($, undefined){
    "use strict";

    $(".go-to-top").click(function () {
      $("html,body").animate({
      scrollTop: 0
      }, 500);
      return false;
    });

    $(window).scroll(function(){  
      var posScroll = $(document).scrollTop();  
      if(posScroll >= 500)   
          $(".go-to-top").fadeIn(600);
      else  
          $(".go-to-top").fadeOut(600);
    });

})(jQuery);