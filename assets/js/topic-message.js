(function() {
  'use strict'

  $('.topic-message').on('click', "[data-ajax-input='copy-hyperlink']", function(e) {
    e.stopPropagation()
    e.preventDefault()
    navigator.clipboard.writeText($(this).attr("data-message-url"));
    const dropdown = e.target.closest(".dropdown")
    dropdown.removeAttribute('open')
  })

  $('.topic-message').on('click', "[data-ajax-input='mark-message-as-useful']", function(e) {
    const $button = $(this)
    const $form = $button.parents('form:first')
    const $message = $form.parents('article')
    const $usefulText = $message.find("[data-ajax-output='mark-message-as-useful']")
    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()

    const $desktopText = $button.find('.desktop')
    const $mobileText = $button.find('.until-desktop')

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken
      },
      success: function() {
        $message.toggleClass('helpful')
        $usefulText.toggleClass('hidden')
        $button.blur()

        // Toggle both mobile and desktop texts
        if ($desktopText.length !== 0 && $mobileText.length !== 0) {
          const currentDesktopText = $desktopText.text()
          const currentMobileText = $mobileText.text()

          $desktopText.text($button.data('content-on-click'))
          $mobileText.text($button.data('content-on-click-mobile'))

          $button.data('content-on-click', currentDesktopText)
          $button.data('content-on-click-mobile', currentMobileText)
        } else {
          $button.toggleText('content-on-click')
        }
      }
    })

    e.stopPropagation()
    e.preventDefault()
  })
})(jQuery)
