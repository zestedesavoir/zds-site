(function($) {
  $('.help-toogle').click((e) => {
    const $current = $(e.target)
    e.preventDefault()
    const newActivation = $current.attr('data-activated') !== 'true'
    $.ajax($current.attr('href'), {
      headers: {
        'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
      },
      method: 'POST',
      data: {
        activated: newActivation ? 'true' : 'false',
        help_wanted: $current.text()
      },
      success: () => {
        if (newActivation) {
          $current.addClass('help-activated')
          $current.attr('data-activated', 'true')
        } else {
          $current.removeClass('help-activated')
          $current.attr('data-activated', 'false')
        }
      }
    })
  })
})(jQuery)
