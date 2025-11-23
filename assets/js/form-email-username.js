/**
 * Used by recovering password and send again validation email functionality.
 */
(function($) {
  'use strict'

  if ($('body').hasClass('form-email-username')) {
    const $emailInput = $('#id_email')
    const $emailForm = $('#form-email')
    const $emailButton = $('[data-form-email-username-button=email]')

    const $usernameInput = $('#id_username')
    const $usernameForm = $('#form-username')
    const $usernameButton = $('[data-form-email-username-button=username]')

    if ($emailInput.val() === '') {
      $emailForm.addClass('hidden')
    } else {
      $emailForm.removeClass('hidden')
    }

    $emailButton.on('click', function(e) {
      $emailForm.toggleClass('hidden')
      $usernameForm.addClass('hidden')

      $usernameInput.val('')

      e.preventDefault()
    })

    if ($usernameInput.val() === '') {
      $usernameForm.addClass('hidden')
    } else {
      $usernameForm.removeClass('hidden')
    }

    $usernameButton.on('click', function(e) {
      $usernameForm.toggleClass('hidden')
      $emailForm.addClass('hidden')

      $emailInput.val('')

      e.preventDefault()
    })
  }
})(jQuery)
