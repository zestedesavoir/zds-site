/* ===== Zeste de Savoir ====================================================
   Prevent from double clic on submit buttons
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  const buttonsSelector = '[type=submit], [type=reset]'
  let $lastButtonClicked = null

  $('body').on('submit', 'form', function() {
    $(buttonsSelector)
      .addClass('disabled')

    if ($lastButtonClicked === null) { $lastButtonClicked = $(buttonsSelector, $(this)) }

    $lastButtonClicked
      .addClass('submitted')
      .append($('<span/>', { class: 'line-loading' }))
  })
  $('form').on('click', buttonsSelector, function(e) {
    $lastButtonClicked = $(this)

    if ($(this).hasClass('disabled')) { e.preventDefault() }
  })
})(jQuery)
