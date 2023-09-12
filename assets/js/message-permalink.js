(function() {
  'use strict'

  $('.topic-message').on('click', "[data-ajax-input='copy-hyperlink']", function(e) {
    e.stopPropagation()
    e.preventDefault()
    navigator.clipboard.writeText($(this).attr("data-message-url"));
    const dropdown = e.target.closest(".dropdown")
    dropdown.removeAttribute('open')
  })
})(jQuery)
