(function($) {
  function changeHelpButtonState($help_button, state) {
    const helpButtonClasses = $help_button[0].classList

    helpButtonClasses.toggle('selected', state)
    helpButtonClasses.toggle('ico-after', state)
    helpButtonClasses.toggle('tick', state)
    helpButtonClasses.toggle('green', state)

    $help_button.attr('data-activated', state.toString())
    $help_button.blur()

    $help_button.parent().find('input[name="activated"]').val((!state).toString())
  }

  $('.help-toggle').click((e) => {
    e.preventDefault()

    const $current = $(e.target)
    const $form = $current.parent()
    const data = $form.serialize()

    const newActivation = $current.attr('data-activated') !== 'true'

    // Change status before request for instant feeling.
    // Will be changed back on error.
    // This update the form so serialize must be called before/
    changeHelpButtonState($current, newActivation)

    $.ajax($form.attr('action'), {
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
