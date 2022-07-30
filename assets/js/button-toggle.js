(function(ajax) {
  function changeToggleButtonState(toggleButton, state) {
    const toggleButtonClasses = toggleButton.classList

    toggleButtonClasses.toggle('selected', state)
    toggleButtonClasses.toggle('ico-after', state)
    toggleButtonClasses.toggle('tick', state)
    toggleButtonClasses.toggle('green', state)

    toggleButton.setAttribute('data-activated', state.toString())

    toggleButton.parentNode.querySelector('input[name="activated"]')
      .setAttribute('value', (!state).toString())
  }

  document.querySelectorAll('.button-toggle')
    .forEach((element) => element.addEventListener('click', e => {
      const current = e.target

      const form = current.parentElement
      const data = new FormData(form)
      const newActivation = current.getAttribute('data-activated') !== 'true'
      // Change status before request for instant feeling.
      // Will be changed back on error.
      changeToggleButtonState(current, newActivation)
      e.preventDefault()
      e.stopPropagation()

      ajax.post(form.getAttribute('action'), data,
        (result) => changeToggleButtonState(current, result.help_wanted),
        () => changeToggleButtonState(current, !newActivation)
      )
    }))
})(window.ajax)
