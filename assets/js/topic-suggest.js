/* ===== Zeste de Savoir ====================================================
   Suggest Topic when user makes topic
   ---------------------------------
   Author: A-312, AmarOk
   ========================================================================== */

(function($) {
  'use strict'

  if (!$('#topic-suggest')[0]) { return }

  let timeoutCall = 0
  let timeoutHidden = 0

  const myHandler = function() {
    const titleURI = encodeURIComponent($(this).val())
    if (titleURI.length < 3) return
    const $container = $('#topic-result-container')
    const suggestTopicsUrl = $('#topic-suggest').attr('url')

    if ($container.data('ajax-load') !== true) {
      $.getJSON(suggestTopicsUrl + '?q=' + titleURI, function(json) {
        const $ul = $('<ul></ul>')
        let $title = null
        let count = 0

        // clearTimeout
        clearTimeout(timeoutHidden)
        clearTimeout(timeoutCall)

        $.each(json.results, function(index, topic) {
          $title = $('<a></a>').attr('target', '_blank')
          $title.text(topic.title).attr('href', topic.url).attr('title', topic.subtitle)
          const $topicDate = new Date(topic.pubdate).toLocaleDateString()
          const $forumLink = $('<a></a>').text(topic.forumTitle).attr('href', topic.forumUrl).attr('target', '_blank')
          $('<li></li>').text(' dans le forum ').append($forumLink).append(' le ' + $topicDate).prepend($title).appendTo($ul)
          count++
          if (count === 5) return // eslint-disable-line no-useless-return
        })

        if (!count) {
          $('<li></li>').addClass('neither').text($container.data('neither')).appendTo($ul)
          timeoutHidden = setTimeout(function() {
            $('#topic-suggest').hide(800)
          }, 6000)
        }
        $container.html('').append($ul)

        $container.data('ajax-load', false)
        $('#topic-suggest').show(800)
      })

      $container.data('ajax-load', true)
    }
  }

  $('#id_title').on('blur', myHandler)

  $('#id_title').on('keypress', function() {
    const that = this
    const length = $(this).val().length

    clearTimeout(timeoutCall)
    timeoutCall = setTimeout(function() {
      myHandler.call(that)
    }, (length < 5) ? (12 - length * 2) * 200 : 2000) // ANTI-FLOOD
  })
})(jQuery)
