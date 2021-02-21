/* ===== Zeste de Savoir ====================================================
   Toggle message content for staff
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  function hidemsg() {
    let $msg = $(this).next()
    let count = 0

    do {
      $msg.toggleClass('hidden')
      $msg = $msg.next()
      count++
    } while ($msg[0] && $msg.hasClass('hidden-by-someone'))

    return count
  }

  $('div.msg-are-hidden.hidden').each(function() {
    const $div = $(this)
    const $link = $div.children('a')
    const hiddenMessagesCount = hidemsg.apply(this)

    $div.removeClass('hidden')

    if (hiddenMessagesCount === 1) {
      $link.text($link.data('message-singular'))
    } else {
      $link.text($link.data('message-plural').replace('{n}', hiddenMessagesCount))
    }

    $div.children('a').click(function() {
      hidemsg.apply(this.parentNode)
      return false
    })
  })
})(jQuery)
