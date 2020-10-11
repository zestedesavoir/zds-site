/* ===== Zeste de Savoir ====================================================
   Accordeon for sidebar
   ---------------------------------
   Author: Alex-D, firm1
   ========================================================================== */

(function() {
  function accordeon(element) {
    const nextSearchElt = ['OL', 'UL']

    Array.from(element.querySelectorAll('h4 + ul, h4 + ol'))
      .filter(item => !item.classList.contains('unfolded'))
      .filter(item => item.querySelectorAll('.current').length === 0)
      .forEach(item => item.setAttribute('hidden', 'true'))


    Array.from(element.querySelectorAll('h4'))
      .filter(item => nextSearchElt.includes(item.nextElementSibling.nodeName))
      .forEach(item => item.addEventListener('click', (e) => {
        if (item.nextElementSibling.getAttribute('hidden') === null) {
          item.nextElementSibling.setAttribute('hidden', 'true')
        } else {
          item.nextElementSibling.removeAttribute('hidden')
        }

        e.preventDefault()
        e.stopPropagation()
      }))
  }

  window.addEventListener('DOMContentLoaded', () => {
    Array.from(document.querySelectorAll('.main .sidebar.accordeon, .main .sidebar .accordeon')).forEach(item => accordeon(item))
  })
})()
