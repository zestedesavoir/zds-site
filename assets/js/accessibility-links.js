/* ===== Zeste de Savoir ====================================================
   Managment of accessibility links
   ---------------------------------
   Author: Alex-D / Alexandre Demode, firm1
   ========================================================================== */

(function() {
  function isHidden(el) {
    const style = window.getComputedStyle(el)
    return (style.display === 'none')
  }

  function accessibility(element) {
    element.addEventListener('focus', () => {
      Array.from(document.querySelectorAll('.header-dropdown'))
        .filter(item => !isHidden(item))
        .forEach(item => item.parentElement.querySelector('.active').classList.remove('active'))
      document.querySelector('#accessibility').classList.add('focused')
    })
    element.addEventListener('blur', () => {
      document.querySelector('#accessibility').classList.remove('focused')
    })
    element.addEventListener('click', () => {
      const link = this.getAttribute('href')
      setTimeout(() => { // Forces the focus on next tick
        document.querySelectorAll(link).item(0).focus() // Focus the first focusable element
      })
    })
  }

  window.addEventListener('DOMContentLoaded', () => {
    Array.from(document.querySelectorAll('#accessibility a')).forEach(item => accessibility(item))
  })
})()
