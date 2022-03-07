(function($) {
  const $opinions = $('.opinion')
  const $opinionCount = $('#opinion-count')
  $opinions.on('click', '.unpick-action', function() {
    const $button = $(this)
    const $row = $button.parent().parent()
    const csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val()
    const data = {
      csrfmiddlewaretoken: csrfmiddlewaretoken
    }
    if ($button.data('operation')) {
      data.operation = $button.data('operation')
    }
    $.post($button.attr('data-url'), data).done(function() {
      if (data.operation) {
        $row.remove()
      } else {
        $button.prop('disabled', true)
        const $stateCol = $row.find('.state')
        $stateCol.text($stateCol.data('toggle'))
      }
      $opinionCount.text(parseInt($opinionCount.text(), 10) - 1)
    })
  })
  $('.unpublish-opinion').on('click', function() {
    const $button = $(this)
    const csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val()
    const data = {
      csrfmiddlewaretoken: csrfmiddlewaretoken,
      operation: 'REMOVE_PUB'
    }
    if (confirm($button.data('confirm'))) {
      $.post($button.data('url'), data).done(function() {
        alert($button.data('done'))
        if (typeof $button.data('redirect-url') !== 'undefined' && $button.data('redirect-url')) {
          window.location.href = $button.data('redirect-url')
        }
      })
    }
  })
})(jQuery)
