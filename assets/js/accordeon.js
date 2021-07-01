/* ===== Zeste de Savoir ====================================================
   Accordeon for sidebar
   ---------------------------------
   Author: Alex-D, firm1
   ========================================================================== */

(function() {
  function accordeon(element) {
    const nextSearchElt = ['OL', 'UL']

    Array.from(element.querySelectorAll('h4 + ul:not(.unfolded), h4 + ol:not(.unfolded)'))
      .filter(item => item.querySelectorAll('.current').length === 0)
      .forEach(item => item.classList.add('hidden'))


    Array.from(element.querySelectorAll('h4'))
      .filter(item => nextSearchElt.includes(item.nextElementSibling.nodeName))
      .forEach(item => item.addEventListener('click', (e) => {
        item.nextElementSibling.classList.toggle('hidden')

        e.preventDefault()
        e.stopPropagation()
      }))
  }

  window.addEventListener('DOMContentLoaded', () => {
    Array.from(document.querySelectorAll('.main .sidebar.accordeon, .main .sidebar .accordeon')).forEach(item => accordeon(item))
  })
})()
