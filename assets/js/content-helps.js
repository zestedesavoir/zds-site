(function($) {
  $('.help-toggle').click((e) => {
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
        let current_el_classes = $current[0].classList

        current_el_classes.toggle('selected', newActivation)
        current_el_classes.toggle('ico-after', newActivation)
        current_el_classes.toggle('tick', newActivation)
        current_el_classes.toggle('green', newActivation)

        $current.attr('data-activated', newActivation.toString())
      }
    })
  })
})(jQuery)
