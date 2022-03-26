(function($) {
  $('.readiness').on('click', function(e) {
    const url = $(e.target).data('url')
    const readiness = $(e.target).data('is-ready').toString() === 'true'
    const csrf = $('input[name=csrfmiddlewaretoken]').val()
    const toggledReadiness = !readiness
    $.ajax(url, {
      method: 'PUT',
      data: {
        ready_to_publish: toggledReadiness,
        container_slug: $(e.target).data('container-slug'),
        parent_container_slug: $(e.target).data('parent-container-slug') || ''
      },
      success: function() {
        const readinessAsString = String(toggledReadiness)
        const newDisplayedText = $(e.target).data('is-ready-' + readinessAsString)
        $(e.target).attr('data-is-ready', readinessAsString)
          .text(newDisplayedText)
      },
      headers: {
        'X-CSRFToken': csrf
      }
    })
  })
})(jQuery)
