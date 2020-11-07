/* ===== Zeste de Savoir ====================================================
   Close alert-boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode, firm1
   ========================================================================== */

(function() {
  window.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', e => {
      if (!e.target.classList.contains('close-alert-box')) return
      e.target.parentElement.remove()
      e.preventDefault()
    })
  })
})()
