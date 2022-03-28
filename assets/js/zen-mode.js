/* ===== Zeste de Savoir ====================================================
   Zen mode for content-pages
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  if ($('.open-zen-mode').length > 0) {
    $('.open-zen-mode').on('click', function(e) {
      const Text = $('.open-zen-mode').text()
      const TextToPut = $('.open-zen-mode').attr('data-content-on-click')
      $('.open-zen-mode').attr('data-content-on-click', Text)
      $('.open-zen-mode').text(TextToPut)

      if (typeof sessionStorage !== 'undefined') {
        if ($('.content-container').hasClass('zen-mode')) {
          if ('zenMode' in sessionStorage) {
            sessionStorage.setItem('zenMode', 'false')
          }
        } else {
          sessionStorage.setItem('zenMode', 'true')
        }
      }

      $('.content-container').toggleClass('zen-mode tab-modalize')
      $(this).blur()
      e.preventDefault()
      e.stopPropagation()
    }
    )

    $('body').on('keydown', function(e) {
      // Escape close modal
      if ($('.zen-mode').length > 0 && e.which === 27) {
        const Text = $('.open-zen-mode').text()
        const TextToPut = $('.open-zen-mode').attr('data-content-on-click')
        $('.open-zen-mode').attr('data-content-on-click', Text)
        $('.open-zen-mode').text(TextToPut)

        if (typeof sessionStorage !== 'undefined') {
          if ('zenMode' in sessionStorage) {
            sessionStorage.setItem('zenMode', 'false')
          }
        }

        $('.content-container').toggleClass('zen-mode tab-modalize')
        $(this).blur()
        e.stopPropagation()
      }
    })

    if (typeof sessionStorage !== 'undefined') {
      if ('zenMode' in sessionStorage) {
        if (sessionStorage.getItem('zenMode') === 'true') {
          $('.open-zen-mode').click()
        }
      }
    }
  }
})(jQuery)
