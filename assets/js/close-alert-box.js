/* ===== Zeste de Savoir ====================================================
   Close alert-boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode, firm1
   ========================================================================== */

(function() {
  window.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
      Array.from(document.querySelectorAll('.close-alert-box'))
        .forEach(item => {
          item.addEventListener('click', function(e) {
            this.parentElement.remove()
            e.preventDefault()
          })
        })
    }, 1000)
  })
})()
