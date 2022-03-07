/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  function buildSpoilers($elem) {
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

  $(document).ready(function() {
    const $content = $('#content')
    $('div.spoiler').addClass('custom-block-spoiler') /* for compatibility */
    buildSpoilers($content.find('.custom-block-spoiler'))
    $content.on('DOMNodeInserted', function(e) {
      const $spoilers = $(e.target).find('.custom-block-spoiler')
      return buildSpoilers($spoilers)
    })
  })
})(jQuery)
