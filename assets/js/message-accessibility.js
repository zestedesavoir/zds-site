(function() {
  'use strict'

  function hasAnyOfTheChildrenGotTheFocus(element, relatedTarget) {
    return Array.prototype.some.call(element.getElementsByTagName('*'), child => (relatedTarget || document.activeElement) === child)
  }

  window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('article.topic-message .message header aside.message-actions ul').forEach(element => {
      let prevFocusOnLink = false

      const handleBlurInContainer = (container, event) => {
        if (!hasAnyOfTheChildrenGotTheFocus(container, event.relatedTarget)) {
          container.classList.remove('is-active')
        }
      }

      element.addEventListener('focus', e => {
        element.classList.add('is-active')

        if (!prevFocusOnLink) {
          const firstMenuItem = element.querySelector('li:first-child a')
          if (firstMenuItem) {
            firstMenuItem.focus()
          }
        }
      })

      element.addEventListener('blur', e => {
        handleBlurInContainer(element, e)
        prevFocusOnLink = false
      })

      Array.prototype.forEach.call(element.getElementsByTagName('*'), child => {
        child.addEventListener('blur', e => {
          handleBlurInContainer(element, e)
          prevFocusOnLink = true
        })
      })
    })
  })
})()
