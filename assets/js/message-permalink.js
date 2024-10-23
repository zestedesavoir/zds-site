(function() {
  'use strict'

  $('.topic-message').on('click', '[data-copy-permalink]', function(e) {
    e.stopPropagation()
    e.preventDefault()
    navigator.clipboard.writeText($(this).attr('data-copy-permalink'))
    const dropdown = e.target.closest('.dropdown')
    dropdown.removeAttribute('open')
  })
})(jQuery)
