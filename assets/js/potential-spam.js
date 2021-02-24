(function() {
  'use strict'
  const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]')
  if (!csrfInput) {
    return
  }
  const csrf = csrfInput.value

  for (const potentialSpamHandle of document.getElementsByClassName('potential-spam-handle')) {
    potentialSpamHandle.addEventListener('click', function() {
      const api = potentialSpamHandle.getAttribute('data-potential-spam-api')
      const newState = potentialSpamHandle.getAttribute('data-potential-spam-new-state') === 'true'

      const message = potentialSpamHandle.closest('article')
      const messageText = message.querySelector("[data-ajax-output='mark-message-as-potential-spam']")

      fetch(api, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify({ is_potential_spam: newState })
      }).then(r => r.json())
        .then(r => {
          message.classList.toggle('potential-spam', r.is_potential_spam)
          messageText.classList.toggle('hidden', !r.is_potential_spam)
          potentialSpamHandle.setAttribute('data-potential-spam-new-state', !r.is_potential_spam)

          const oldButtonText = potentialSpamHandle.innerText
          potentialSpamHandle.innerHTML = potentialSpamHandle.getAttribute('data-content-on-click')
          potentialSpamHandle.setAttribute('data-content-on-click', oldButtonText)

          potentialSpamHandle.blur()
        })
    })
  }
})()
