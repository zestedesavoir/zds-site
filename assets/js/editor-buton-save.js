'use strict'
function changeSubmitButtonState() {
  $('button[type="submit"]').each((_, b) => {
    if ($(b).prop('disabled')) {
      $(b).prop('disabled', false)
    } else {
      $(b).prop('disabled', true)
    }
  })
}
function saveFormNoRedirect($form, $saveButton) {
  const data = $form.serialize()
  data.preview = undefined
  console.log(data)
  changeSubmitButtonState()
  $saveButton.removeClass('btn-cancel')
  $.ajax($form.attr('action'), {
    method: 'POST',
    data,
    success: (resultData) => {
      changeSubmitButtonState()
      $('input[name="last_hash"]').val(resultData.last_hash)
      $saveButton.addClass('btn-submit')
      setTimeout(() => $saveButton.removeClass('btn-submit'), 5000)
    },
    error: () => {
      changeSubmitButtonState()
      $saveButton.addClass('btn-cancel')
    }
  })
}

(function($) {
  $('.inline-save-button').click(e => {
    const $form = $(e.target.form)
    e.preventDefault()
    e.stopPropagation()
    saveFormNoRedirect($form, $(e.target))
    return true
  })
})(jQuery)
