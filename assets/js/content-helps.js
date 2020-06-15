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
        const currentHelpClasses = $current[0].classList

        currentHelpClasses.toggle('selected', newActivation)
        currentHelpClasses.toggle('ico-after', newActivation)
        currentHelpClasses.toggle('tick', newActivation)
        currentHelpClasses.toggle('green', newActivation)

        $current.attr('data-activated', newActivation.toString())
      }
    })
  })
})(jQuery)
