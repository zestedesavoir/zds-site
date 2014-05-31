/* ===== Zeste de Savoir ====================================================
   Author: Alex-D
   ---------------------------------
   Font-face async load with webfontloader :
   https://github.com/typekit/webfontloader
   ========================================================================== */

WebFontConfig = {
    google: {
      families: ['Source Sans Pro', 'Droid Serif']
    }
};

(function() {
    var wf = document.createElement('script');
    wf.src = ('https:' == document.location.protocol ? 'https' : 'http') +
              '://ajax.googleapis.com/ajax/libs/webfont/1.4.7/webfont.js';
    wf.type = 'text/javascript';
    wf.async = 'true';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(wf, s);
})();