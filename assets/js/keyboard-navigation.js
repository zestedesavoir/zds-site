/* ===== Zeste de Savoir ====================================================
   Keyboard navigation in navigables lists, with j/k keys
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  $(document).ready(function() {
    let $lists = $('#content .navigable-list')

    if ($lists.length > 0) {
      const $navigableElems = $lists.find('.navigable-elem')

      $('body').on('keydown', function(e) {
        if (!$(document.activeElement).is(':input') && (e.which === 74 || e.which === 75)) {
          const $current = $lists.find('.navigable-elem.active')
          let nextIndex = null

          if ($current.length === 1) {
            const currentIndex = $navigableElems.index($current)
            if (e.which === 75) { // J
              if (currentIndex > 0) { nextIndex = currentIndex - 1 }
            } else { // K
              if (currentIndex + 1 < $navigableElems.length) { nextIndex = currentIndex + 1 }
            }
          } else {
            nextIndex = 0
          }

          if (nextIndex !== null) {
            $current.removeClass('active')
            activeNavigableElem($navigableElems.eq(nextIndex))
          }
        }
      })

      $('#content .navigable-list')
        .on('focus', '.navigable-link', function() {
          if (!$(this).parents('.navigable-elem:first').hasClass('active')) {
            $lists.find('.navigable-elem.active').removeClass('active')
            activeNavigableElem($(this).parents('.navigable-elem'))
          }
        })
        .on('blur', '.navigable-link', function() {
          $(this).parents('.navigable-elem:first').removeClass('active')
        })
    }

    function activeNavigableElem($elem) {
      $elem
        .addClass('active')
        .find('.navigable-link')
        .focus()
    }

    $('#content').on('DOMNodeInserted', '.navigable-list, .navigable-elem', function() {
      $lists = $('#content .navigable-list')
    })
  })
})(jQuery)
