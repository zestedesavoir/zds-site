/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  function buildOldSpoilers($elem) {
    $elem.each(function() {
      const $this = $(this)
      if (!$this.hasClass('spoiler-build')) {
        let text = 'Afficher/Masquer le contenu masqué'
        const $header = $this.find('.custom-block-heading')
        if ($header[0]) {
          text = $header.text() + ' (Afficher/Masquer)'
          $header.remove()
        }
        $this.before($('<a/>', {
          text: text,
          class: 'spoiler-title ico-after view',
          href: '#',
          click: function(e) {
            $(this).next('.custom-block-spoiler').toggle()
            e.preventDefault()
          }
        }))
        $this.addClass('spoiler-build')
      }
    })
  }

  function buildNewSpoilers() {
    for (const spoiler of document.querySelectorAll('details.custom-block-spoiler')) {
      let summary = spoiler.querySelector('summary')
      if (summary === null) {
        summary = document.createElement('summary')
        summary.classList.add('custom-block-heading')
        summary.textContent = 'Afficher/Masquer le contenu masqué'
        const body = spoiler.querySelector('.custom-block-body')
        spoiler.insertBefore(summary, body)
      }
      if (!summary.classList.contains('ico-after')) {
        summary.classList.add('ico-after', 'view', 'light')
      }
    }
  }

  $(document).ready(function() {
    const $content = $('#content')
    $('div.spoiler').addClass('custom-block-spoiler') /* for compatibility */
    buildOldSpoilers($content.find('div.custom-block-spoiler'))
    buildNewSpoilers()
    $content.on('DOMNodeInserted', function(e) {
      const $spoilers = $(e.target).find('div.custom-block-spoiler')
      buildOldSpoilers($spoilers)
      return buildNewSpoilers()
    })
  })
})(jQuery)
