/* ===== Zeste de Savoir ====================================================
   Managment of accessibility links
   ---------------------------------
   Author: Alex-D / Alexandre Demode, firm1
   ========================================================================== */

(function() {
  function isHidden(el) {
    var style = window.getComputedStyle(el)
    return (style.display === 'none')
  }

  function accessibility(element) {
    element.addEventListener('focus', function() {
      Array.from(document.querySelectorAll('.dropdown'))
        .filter(item => !isHidden(item))
        .forEach(item => item.parentElement.querySelector('.active').classList.remove('active'))
      document.querySelector('#accessibility').classList.add('focused')
    })
    element.addEventListener('blur', function() {
      document.querySelector('#accessibility').classList.remove('focused')
    })
    element.addEventListener('click', function() {
      var link = this.getAttribute('href')
      setTimeout(function() { // Forces the focus on next tick
        document.querySelectorAll(link).item(0).focus() // Focus the first focusable element
      })
    })
  }

  window.addEventListener('DOMContentLoaded', function() {
    Array.from(document.querySelectorAll('#accessibility a')).forEach(item => accessibility(item))
  })
})()
