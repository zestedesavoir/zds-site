(function() {
  'use strict'

  document.querySelectorAll('.topic-message').forEach(function(topicMessage) {
    topicMessage.addEventListener('click', function(e) {
      const target = e.target.closest('[data-copy-permalink]')
      if (!target) return
      e.stopPropagation()
      e.preventDefault()
      navigator.clipboard.writeText(target.getAttribute('data-copy-permalink'))
      const dropdown = target.closest('.dropdown')
      dropdown.removeAttribute('open')
    })
  })
})()
