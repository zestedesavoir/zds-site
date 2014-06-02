/* ===== Zeste de Savoir ====================================================
   Author: Sandhose / Quentin Gliech
   ---------------------------------
   Hide distraction in reader mode
   ========================================================================== */

(function(window, document, undefined) { 
  var ReaderMode = {
    init: function() {
      ReaderMode.button = document.getElementById("readerModeBtn");
      if(ReaderMode.button) ReaderMode.button.addEventListener("click", ReaderMode.toggle, false);
    },
    toggle: function() {
      document.body.classList.toggle("reader-mode");
      return false;
    }
  };

  document.addEventListener("DOMContentLoaded", ReaderMode.init);
})(window, document);
