/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function($) {
  'use strict'

  /**
   * Toggle the text of the element by the text of an attribute
   *
   * @param {string} dataAttribute
   */
  $.fn.toggleText = function(dataAttribute) {
    let textContainer = this.find('.a11y')
    if (textContainer.length === 0) {
      textContainer = this
    } else {
      textContainer = $(textContainer[0])
    }

    const text = textContainer.text()
    const textToPut = this.data(dataAttribute)

    textContainer.text(textToPut)
    this.data(dataAttribute, text)
  }

  function synchText() {
    $('#mobile-menu [data-ajax-input]').each(function() {
      const dataAjaxInput = $(this).data('ajax-input')
      $(this).text($('.sidebar').find("button[data-ajax-input='" + dataAjaxInput + "']").text())
    })
  }

  /**
   * Follow a topic
   */
  $('.sidebar, .flexpage-title-tool .actions').on('click', "[data-ajax-input='follow-topic']", function(e) {
    const $act = $(this)
    const $form = $(this).parents('form:first')
    let $email = $(this).parents('li:first').next().find("[data-ajax-input='follow-topic-by-email']")
    const $followText = $act.find('span#follow_text')
    const $count = $form.find('span#subscriber_count')
    const $plural = $act.find('span#subscriber_plural')
    const $otherSubscriberCount = $($act.attr('data-raw-subscriber-count'))

    if ($email.length === 0) {
      $email = $(this).parents('.buttons-combined').find("[data-ajax-input='follow-topic-by-email']")
    }

    $email.prop('disabled', true)

    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    const topic = $form.find('input[name=topic]').val()
    const follow = $form.find('input[name=follow]').val()
    const page = $form.find('input[name=page]').val()

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      dataType: 'json',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
        topic: topic,
        follow: follow,
        page: page
      },
      success: function(data) {
        if (data.follow) {
          $form.find('input[name=follow]').val(1)
        } else {
          if ($email.hasClass('blue') === false || $email.hasClass('is-following') === true) {
            $email.toggleText('content-on-click')
            $email.addClass('blue').removeClass('is-following')

            $email.parents('form:first').find('input[name=email]').val(0)
          }

          $form.find('input[name=follow]').val(0)
        }

        $followText.toggleText('content-on-click')
        $count.text(data.subscriberCount)
        $plural.text(data.subscriberCount > 1 ? 's' : '')

        if ($otherSubscriberCount) {
          $otherSubscriberCount.text(data.subscriberCount)
        }

        $act.toggleClass('blue yellow is-following')
        $act.blur()

        synchText()
      },
      complete: function() {
        $email.prop('disabled', false)
      }
    })

    e.stopPropagation()
    e.preventDefault()
  })

  /**
   * Be notified by email
   */
  $('.sidebar, .flexpage-title-tool .actions').on('click', "[data-ajax-input='follow-topic-by-email']", function(e) {
    const $act = $(this)
    let $follow = $(this).parents('li:first').prev().find("[data-ajax-input='follow-topic']")
    const $form = $(this).parents('form:first')

    if ($follow.length === 0) {
      $follow = $(this).parents('.buttons-combined').find("[data-ajax-input='follow-topic']")
    }

    $follow.prop('disabled', true)

    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    const topic = $form.find('input[name=topic]').val()
    const email = $form.find('input[name=email]').val()
    const page = $form.find('input[name=page]').val()

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      dataType: 'json',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
        topic: topic,
        email: email,
        page: page
      },
      success: function(data) {
        if (data.email) {
          if ($follow.hasClass('yellow') === false || $follow.hasClass('is-following') === false) {
            $follow.toggleText('content-on-click')
            $follow.removeClass('blue')
            $follow.addClass('yellow is-following')

            $follow.parents('form:first').find('input[name=follow]').val(1)
          }

          $form.find('input[name=email]').val(1)
        } else {
          $form.find('input[name=email]').val(0)
        }

        $act.toggleText('content-on-click')
        $act.toggleClass('blue, is-following')
        $act.blur()

        synchText()
      },
      complete: function() {
        $follow.prop('disabled', false)
      }
    })
    e.stopPropagation()
    e.preventDefault()
  })

  /**
   * Featured request
   */
  $('.sidebar').on('click', "[data-ajax-input='request-featured']", function(e) {
    const $act = $(this)
    const $form = $(this).parents('form:first')
    const $requestText = $act.find('#request_text')
    const $count = $form.find('#featured_request_count')
    const $plural = $act.find('#featured_request_plural')

    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    const requestFeatured = $form.find('input[name=request_featured]').val()

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      dataType: 'json',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
        request_featured: requestFeatured
      },
      success: function(data) {
        $requestText.toggleText('content-on-click')
        $count.text(data.newCount)
        $plural.text(data.newCount > 1 ? 's' : '')
        $act.toggleClass('blue yellow')

        synchText()
      }
    })

    e.stopPropagation()
    e.preventDefault()
  })

  /**
   * Mark a topic solved
   */
  $('.sidebar').on('click', "[data-ajax-input='solve-topic']", function(e) {
    const $act = $(this)
    const $form = $(this).parents('form:first')

    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    const topic = $form.find('input[name=topic]').val()
    const solved = $form.find('input[name=solved]').val()
    const page = $form.find('input[name=page]').val()

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      dataType: 'json',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
        topic: topic,
        solved: solved,
        page: page
      },
      success: function(data) {
        if (data.solved) {
          $form.find('input[name=solved]').val(1)
        } else {
          $form.find('input[name=solved]').val(0)
        }

        $act.toggleText('content-on-click')
        $act.toggleClass('green blue')
        $("[data-ajax-output='solve-topic']").html('Vous venez de marquer ce sujet comme résolu.')
        $("[data-ajax-output='solve-topic']").toggleClass('empty')

        synchText()
      }
    })
    e.stopPropagation()
    e.preventDefault()
  })

  /**
   * Mobile action
   */
  $('#mobile-menu').on('click', '[data-ajax-input]', function(e) {
    const dataAjaxInput = $(this).data('ajax-input')
    const $button = $('.sidebar').find("button[data-ajax-input='" + dataAjaxInput + "']")

    if ($button[0]) {
      $(this).toggleText('content-on-click')
      $button.click()

      e.stopPropagation()
      e.preventDefault()
    }
  })

  function getLineAt(string, index) {
    const before = string.slice(0, index).split('\n').slice(-1)[0] || ''
    const after = string.slice(index).split('\n')[0] || ''
    return before + after
  }

  function insertCitationOld(editor, citation) {
    if (editor.value === '') {
      editor.value = citation + '\n\n'
      return
    }
    if (editor.selectionStart !== editor.selectionEnd ||
            getLineAt(editor.value, editor.selectionStart).trim()) {
      editor.value = editor.value + '\n\n' + citation
      return
    }

    const before = editor.value.slice(0, editor.selectionStart)
    const after = editor.value.slice(editor.selectionEnd)
    editor.value = before + '\n' + citation + '\n' + after
  }

  function insertCitationNew(editor, citation) {
    const cm = window.editors[editor.id].codemirror
    const doc = cm.getDoc()
    const cursor = doc.getCursor()

    if (cm.getValue() === '') {
      cm.setValue(citation + '\n\n')
      cm.setCursor(cm.lineCount(), 0)
    } else if (cm.somethingSelected()) {
      doc.replaceSelection('\n\n' + citation + '\n\n')
    } else {
      doc.replaceRange('\n\n' + citation + '\n\n', cursor)
    }

    cm.focus()
  }

  /**
   * Cite a message
   */
  $('.message-actions').on('click', "[data-ajax-input='cite-message']", function(e) {
    e.stopPropagation()
    e.preventDefault()

    const $act = $(this)
    const editor = document.querySelector('.md-editor')

    $.ajax({
      url: $act.attr('href'),
      dataType: 'json',
      success: function(data) {
        if (localStorage.getItem('editor_choice') === 'new') {
          insertCitationNew(editor, data.text)
        } else {
          insertCitationOld(editor, data.text)
        }
      }
    })

    // scroll to the textarea
    if (localStorage.getItem('editor_choice') === 'new') {
      $('html, body').animate({ scrollTop: $(editor).siblings('.CodeMirror').top }, 500)
    } else {
      $('html, body').animate({ scrollTop: $(editor).top }, 500)
      editor.focus()
    }
  })

  /*
     * Mark a message useful
     */
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
