(function(ajax) {
  function setButtonState(button, state) {
    const buttonClasses = button.classList

    buttonClasses.toggle('selected', state)
    buttonClasses.toggle('ico-after', state)
    buttonClasses.toggle('tick', state)
    buttonClasses.toggle('green', state)

    button.setAttribute('data-activated', state.toString())

    button.parentNode.querySelector('input[name="activated"]')
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
      setButtonState(current, newActivation)
      e.preventDefault()
      e.stopPropagation()

      ajax.post(form.getAttribute('action'), data,
        (result) => setButtonState(current, result.state),
        () => setButtonState(current, !newActivation)
      )
    }))
})(window.ajax)
