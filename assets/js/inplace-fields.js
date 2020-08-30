/* ===== Zeste de Savoir ==================================================== */
/*  Show and hide in-place forms                                              */
/* ========================================================================== */

(function($) {
  'use strict'

  /* Edit title */
  function toggleDisplayTitle(e) {
    $('#title-show').toggleClass('hidden')
    $('#title-edit').toggleClass('hidden')
    e.preventDefault()
  }

  $('#show-title-edit').on('click', toggleDisplayTitle)
  $('#hide-title-edit').on('click', toggleDisplayTitle)

  /* Edit subtitle */
  function toggleDisplaySubtitle(e) {
    $('#subtitle-show').toggleClass('hidden')
    $('#subtitle-edit').toggleClass('hidden')
    e.preventDefault()
  }

  $('#show-subtitle-edit').on('click', toggleDisplaySubtitle)
  $('#hide-subtitle-edit').on('click', toggleDisplaySubtitle)
})(jQuery)
