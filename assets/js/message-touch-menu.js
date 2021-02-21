(function() {
  'use strict'

  const messagesActionsHandles = document.querySelectorAll('article.topic-message header aside.message-actions ul li')

  // On touch-sensitive devices, we force the menu to be opened at the first
  // touch, to prevent the first item from being triggered.
  for (const handleElement of messagesActionsHandles) {
    const messageActionsElement = handleElement.parentElement

    // We open the menu if we touch one of its item and it is not already open.

    handleElement.addEventListener('touchend', e => {
      if (!messageActionsElement.classList.contains('is-active')) {
        e.preventDefault()
        messageActionsElement.classList.add('is-active')
      }
    })

    // We close the menu if one touch outside of it.

    document.addEventListener('touchend', e => {
      if (messageActionsElement.classList.contains('is-active') && e.target.closest('article.topic-message header aside.message-actions ul') === null) {
        e.preventDefault()
        messageActionsElement.classList.remove('is-active')

        // We also remove focus from the first element, if any, and from the
        // menu itself, so it closes.
        handleElement.querySelector(':first-child').blur()
        handleElement.blur()
        messageActionsElement.blur()
      }
    })
  }
})()
