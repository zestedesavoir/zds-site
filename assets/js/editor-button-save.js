'use strict'
function toggleSubmitButtonsState() {
  $('button[type=submit]').each((_, b) => {
    $(b).prop('disabled', !$(b).prop('disabled'))
  })
}
function saveFormNoRedirect($form, $saveButton) {
  const data = $form.serialize()
  data.preview = undefined
  toggleSubmitButtonsState()
  $saveButton.removeClass('btn-cancel')
  $.ajax($form.attr('action'), {
    method: 'POST',
    data,
    success: (resultData) => {
      toggleSubmitButtonsState()
      $('input[name=last_hash]').val(resultData.last_hash)
      $saveButton.addClass('btn-submit')
      $form.attr('action', resultData.new_url)
      setTimeout(() => $saveButton.removeClass('btn-submit'), 5000)
    },
    error: () => {
      toggleSubmitButtonsState()
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
