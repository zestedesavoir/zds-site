/* ===== Zeste de Savoir ====================================================
   Toggle message content for staff
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  function hidemsg() {
    let $msg = $(this).next()
    do {
      $msg.toggleClass('hidden')
      $msg = $msg.next()
    } while ($msg[0] && $msg.hasClass('hidden-by-someone'))
  }

  $('div.msg-are-hidden.hidden').each(function() {
    const $div = $(this)
    $div.removeClass('hidden')
    hidemsg.apply(this)
    $div.children('a').click(function() {
      hidemsg.apply(this.parentNode)
      return false
    })
  })
})(jQuery)
