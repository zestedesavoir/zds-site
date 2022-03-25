(function($) {
  $('.featured-request').on('click', '.unpick-action', function() {
    const $button = $(this)
    const $row = $button.parent().parent()
    const $table = $row.parent()
    const csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val()
    const operation = $button.data('operation')
    const data = {
      csrfmiddlewaretoken: csrfmiddlewaretoken
    }
    if (operation) {
      data.operation = $button.data('operation')
    }
    $.post($button.attr('data-url'), data).done(function(result) {
      if (result.result === 'OK') {
        if (operation === 'REJECT' || operation === 'REJECT_FOR_GOOD') {
          $row.remove()
          if ($table.find('tr').length === 0) {
            $table.append('<tr><td colspan="4"><i>Plus rien à afficher pour le moment !</i></td></tr>')
          }
        } else {
          $button.toggleClass('cross hide')
          $button.text('Ignorer')
          $button.data('operation', 'REJECT')
        }
      } else {
        $button.prop('disabled', true)
      }
    })
  })
})(jQuery)
