(function(ajax) {
  function changeHelpButtonState(helpButton, state) {
    const helpButtonClasses = helpButton.classList

    helpButtonClasses.toggle('selected', state)
    helpButtonClasses.toggle('ico-after', state)
    helpButtonClasses.toggle('tick', state)
    helpButtonClasses.toggle('green', state)

    helpButton.setAttribute('data-activated', state.toString())

    helpButton.parentNode.querySelector('input[name="activated"]')
      .setAttribute('value', (!state).toString())
  }

  document.querySelectorAll('.help-toggle')
    .forEach((element) => element.addEventListener('click', e => {
      const current = e.target

      const form = current.parentElement
      const data = new FormData(form)
      const newActivation = current.getAttribute('data-activated') !== 'true'
      // Change status before request for instant feeling.
      // Will be changed back on error.
      changeHelpButtonState(current, newActivation)
      e.preventDefault()
      e.stopPropagation()

      ajax.post(form.getAttribute('action'), data,
        (result) => changeHelpButtonState(current, result.help_wanted),
        () => changeHelpButtonState(current, !newActivation)
      )
    }))
})(window.ajax)
