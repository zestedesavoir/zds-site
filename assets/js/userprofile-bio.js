/* ===== Zeste de Savoir ====================================================
   Truncates too long biographies on profile pages, with a link to see the
   whole bio.
   ---------------------------------
   Author: Amaury Carrade
   ========================================================================== */

(function($) {
  'use strict'

  const $bioContainer = $('body.userprofilepage .bio-container')
  if (!$bioContainer[0]) return // We are not on a profile page

  const $bioTextContainer = $bioContainer.find('.message-content')
  const $bioOverflowToggleHandle = $bioContainer.find('.biography-overflow')
  const $bioOverflowToggleLabel = $bioOverflowToggleHandle.find('p')

  if ($bioTextContainer[0].scrollHeight - $bioTextContainer.innerHeight() > 10) {
    // We detect overflow by comparing the scroll height (equal to the whole
    // size, without max-width) to the inner height (equal to the visible size).
    // But we must accept a margin as non-overflowing blocks may have a slightly
    // bigger scroll height (e.g. 148 vs 147.6).
    $bioContainer.addClass('too-long-biography')
  } else {
    // If overflow was not detected, we ensure that the whole biography is
    // shown, as for edge cases, the end of the biography may be slightly
    // cut without link to show it full. Also, if there are spoilers in the
    // biography, we don't want them to be cut by the max-width while open.
    $bioContainer.addClass('full-biography')
  }

  $bioOverflowToggleHandle.on('click', function() {
    $bioContainer.toggleClass('full-biography')

    const oldLabel = $bioOverflowToggleLabel.text()

    $bioOverflowToggleLabel.text($bioOverflowToggleLabel.attr('data-other-label'))
    $bioOverflowToggleLabel.attr('data-other-label', oldLabel)
  })
})(jQuery)
