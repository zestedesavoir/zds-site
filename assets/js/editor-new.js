/* globals oGrammalecteAPI, estPresentAntidoteAPI_JSConnect, activeAntidoteAPI_JSConnect */ // eslint-disable-line camelcase

(function($) {
  'use strict'

  if (localStorage.getItem('editor_choice') !== 'new') {
    return
  }

  (function() {
    /**
     * Migration easymde
     */
    const source = localStorage.getItem('savedEditorText')
    const entries = source ? JSON.parse(source) : []
    for (const n in entries) {
      localStorage.setItem('smde_' + entries[n].id, entries[n].value)
    }
    localStorage.removeItem('savedEditorText')
  })()

  /**
   * Preview the message on bottom
   */
  $(".message-bottom [data-ajax-input='preview-message'], .preview-btn").on('click', function(e) {
    e.stopPropagation()
    e.preventDefault()
    var $btn = $(this)
    var $form = $btn.parents('form:first')
    var idInstance
    if ($form.find('.preview-source').length) {
      idInstance = $btn.closest('div').prev().find('.md-editor').prop('id')
    } else {
      idInstance = $form.find('.md-editor').prop('id')
    }
    var text = window.editors[idInstance].value()

    var csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    var lastPost = $form.find('input[name=last_post]').val()

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
        text: text,
        last_post: lastPost,
        preview: 'preview'
      },
      success: function(data) {
        $('.previsualisation').remove()

        if ($form.find('.preview-source').length) { $(data).insertAfter($btn) } else { $(data).insertAfter($form) }
      }
    })
  })


  const maxRange = 99999999999
  const csrf = $('input[name=csrfmiddlewaretoken]').val()
  window.editors = {}

  function checkMatch(str, reg) {
    var found = String(str).match(reg)
    if (found) {
      return found.length > 0
    }
  }

  function getStateZmd(cm) {
    var posStart = cm.getCursor('start')
    var posEnd = cm.getCursor('end')
    var line = cm.getLine(posStart.line)
    var ret = {}
    var i

    var beforeChars = line.slice(0, posStart.ch).match(/^(\S)+/g)
    var afterChars = line.slice(posEnd.ch).match(/(\S)+$/g)


    if (beforeChars && afterChars) {
      if (checkMatch(beforeChars, /(.*)*\|\|$/) && checkMatch(afterChars, /^\|\|(.*)*/)) {
        ret.keyboard = true
      } else if (checkMatch(beforeChars, /(.*)`|$/) && checkMatch(afterChars, /^`(.*)/)) {
        ret.codeInline = true
      } else if (checkMatch(beforeChars, /(.*)~$/) && checkMatch(afterChars, /^~(.*)/)) {
        ret.subscript = true
      } else if (checkMatch(beforeChars, /(.*)\^$/) && checkMatch(afterChars, /^\^(.*)/)) {
        ret.superscript = true
      } else if (checkMatch(beforeChars, /^->($|\s)+/) && checkMatch(afterChars, /(^|\s)+->$/)) {
        ret.alignRight = true
      } else if (checkMatch(beforeChars, /^->($|\s)+/) && checkMatch(afterChars, /(^|\s)+<-$/)) {
        ret.alignCenter = true
      } else if (checkMatch(beforeChars, /^\$\$($|\s)+/) && checkMatch(afterChars, /(^|\s)+\$\$$/)) {
        ret.math = true
      }
    } else if (checkMatch(line, /^\[\[(.+)\]\]$/)) { // it's a bloc
      var isBlock = true
      for (i = (posStart.line) + 1; i <= posEnd.line; i++) {
        if ((!cm.getLine(i).startsWith('| ')) && (cm.getLine(i) !== '')) {
          isBlock = false
          break
        }
      }
      if (isBlock) {
        var reg = /^\[\[(.+)\]\]$/
        var m = reg.exec(line)
        const _titleContents = m[1].split('|')
        const _type = _titleContents[0].trim()
        if (_type === 'i' || _type === 'information') {
          ret.blocInformation = true
        } else if (_type === 'q' || _type === 'question') {
          ret.blocQuestion = true
        } else if (_type === 'e' || _type === 'erreur') {
          ret.blocError = true
        } else if (_type === 's' || _type === 'secret') {
          ret.blocSecret = true
        } else if (_type === 'n' || _type === 'neutre') {
          ret.blocNeutral = true
        }
      }
    } else {
      // find checklist
      var isCheckList = true
      if (!(posStart.line === posEnd.line && posStart.ch === posEnd.ch)) {
        for (i = posStart.line; i <= posEnd.line; i++) {
          if ((!cm.getLine(i).match(/^- \[(.{1})\](\s*)/)) && (cm.getLine(i) !== '')) {
            isCheckList = false
            break
          }
        }
        if (isCheckList) {
          ret.checklist = true
        }
      }
    }
    return ret
  }

  function shiftLines(cm, lineNumber, replText) {
    var nextText
    var currentText
    const lastLine = cm.lastLine()
    for (var i = lineNumber; i <= lastLine + 1; i++) {
      currentText = cm.getLine(i)
      if (i === lineNumber) {
        cm.replaceRange(replText, { line: i, ch: 0 }, { line: i, ch: maxRange })
      } else {
        cm.replaceRange(nextText, { line: i, ch: 0 }, { line: i, ch: maxRange })
      }
      nextText = currentText
      if (i === lastLine) {
        nextText = cm.lineSeparator() + nextText
      }
    }
  }

  function unShiftLines(cm, lineStart, lineEnd) {
    for (var i = lineStart + 1; i <= lineEnd; i++) {
      cm.replaceRange(cm.getLine(i).slice(2), { line: i, ch: 0 }, { line: i, ch: maxRange })
    }
    cm.replaceRange('', { line: lineStart, ch: 0 }, { line: lineStart + 1, ch: 0 })
  }

  function disableBlockZmd(cm, type, startChars, endChars, startPoint, endPoint) {
    let i, m, start, end

    const text = cm.getLine(startPoint.line)
    start = text.slice(0, startPoint.ch)
    end = text.slice(startPoint.ch)
    var offset = 0
    if (type === 'blocInformation' || type === 'blocQuestion' || type === 'blocError' || type === 'blocSecret' || type === 'blocNeutral') {
      unShiftLines(cm, startPoint.line, endPoint.line)
      startPoint.ch = 0
    } else if (type === 'checklist') {
      for (i = startPoint.line; i <= endPoint.line; i++) {
        cm.replaceRange(cm.getLine(i).slice(startChars.length), { line: i, ch: 0 }, { line: i, ch: maxRange })
      }
      endPoint.ch -= startChars.length
    } else {
      const regAlign = /(->)(\s*)/
      if (type === 'keyboard') {
        start = start.replace(/(\|\|)(?![\s\S]*(\|\|))/, '')
        end = end.replace(/(\|\|)/, '')
        offset = 2
      } else if (type === 'codeInline') {
        start = start.replace(/(`)(?![\s\S]*(`))/, '')
        end = end.replace(/(`)/, '')
        offset = 1
      } else if (type === 'subscript') {
        start = start.replace(/(~)(?![\s\S]*(~))/, '')
        end = end.replace(/(~)/, '')
        offset = 1
      } else if (type === 'superscript') {
        start = start.replace(/(\^)(?![\s\S]*(\^))/, '')
        end = end.replace(/(\^)/, '')
        offset = 1
      } else if (type === 'alignRight') {
        m = regAlign.exec(start)
        start = start.replace(/(->)(\s*)/, '')
        end = end.replace(/(\s*)(->)/, '')
        offset = m[0].length
      } else if (type === 'alignCenter') {
        m = regAlign.exec(start)
        start = start.replace(/(->)(\s*)/, '')
        end = end.replace(/(\s*)(<-)/, '')
        offset = m[0].length
      } else if (type === 'math') {
        start = start.replace(/(\$\$)(?![\s\S]*(\$\$))/, '')
        end = end.replace(/(\$\$)/, '')
        offset = 2
      }

      cm.replaceRange(start + end, {
        line: startPoint.line,
        ch: 0
      }, {
        line: startPoint.line,
        ch: maxRange
      })

      startPoint.ch -= offset
      if (startPoint !== endPoint) {
        endPoint.ch -= offset
      }
    }
  }

  function enableBlockZmd(cm, type, start, end, startPoint, endPoint) {
    let i, text
    if (type === 'blocInformation' || type === 'blocQuestion' || type === 'blocError' || type === 'blocSecret' || type === 'blocNeutral') {
      // blocs
      for (i = startPoint.line; i <= endPoint.line; i++) {
        text = start + cm.getLine(i)
        cm.replaceRange(text, { line: i, ch: 0 }, { line: i, ch: maxRange })
      }
      if (type === 'blocInformation') {
        shiftLines(cm, startPoint.line, '[[information]]')
      } else if (type === 'blocQuestion') {
        shiftLines(cm, startPoint.line, '[[question]]')
      } else if (type === 'blocError') {
        shiftLines(cm, startPoint.line, '[[erreur]]')
      } else if (type === 'blocSecret') {
        shiftLines(cm, startPoint.line, '[[secret]]')
      } else if (type === 'blocNeutral') {
        shiftLines(cm, startPoint.line, '[[neutre|titre]]')
      }
      startPoint.ch = 0
      endPoint.line += 1
      endPoint.ch = endPoint.line.length
    } else if (type === 'checklist') {
      // checklists
      for (i = startPoint.line; i <= endPoint.line; i++) {
        text = start + cm.getLine(i)
        cm.replaceRange(text, { line: i, ch: 0 }, { line: i, ch: maxRange })
      }
      endPoint.ch += start.length
    } else {
      // inline codes
      text = cm.getSelection()
      if (type === 'keyboard') {
        text = text.split('||').join('')
      } else if (type === 'codeInline') {
        text = text.split('`').join('')
      } else if (type === 'subscript') {
        text = text.split('~').join('')
      } else if (type === 'superscript') {
        text = text.split('^').join('')
      } else if (type === 'alignRight') {
        text = text.split('-> ').join('')
      } else if (type === 'alignCenter') {
        text = text.split('-> ').join('').split(' <-').join('')
      } else if (type === 'math') {
        text = text.split('$$').join('')
      }
      cm.replaceSelection(start + text + end)

      startPoint.ch += start.length
      endPoint.ch = startPoint.ch + text.length
    }
  }

  function _toggleBlockZmd(editor, type, startChars, endChars) {
    if (/editor-preview-active/.test(editor.codemirror.getWrapperElement().lastChild.className)) { return }
    endChars = (typeof endChars === 'undefined') ? startChars : endChars
    const cm = editor.codemirror
    const stat = getStateZmd(cm)
    const start = startChars
    const end = endChars
    const startPoint = cm.getCursor('start')
    const endPoint = cm.getCursor('end')

    if (stat[type]) {
      disableBlockZmd(cm, type, start, end, startPoint, endPoint)
    } else {
      enableBlockZmd(cm, type, start, end, startPoint, endPoint)
    }

    cm.setSelection(startPoint, endPoint)
    cm.focus()
  }

  var uploadImage = function(file, onSuccess, onError) {
    var galleryUrl = '/api/galeries/' + document.body.getAttribute('data-gallery') + '/images/'

    var formData = new FormData()
    formData.append('physical', file)
    formData.append('title', file.name)
    // WARN: if you test zds with sqlite, you can"t upload multiple files at a time
    $.ajax({
      url: galleryUrl,
      data: formData,
      type: 'POST',
      processData: false,
      contentType: false,
      headers: {
        'X-CSRFToken': csrf
      },
      dataType: 'json'
    }).done(function(result) {
      onSuccess(result.url)
    }).fail(function(resp) {
      var error = 'Erreur inconnue'
      if (resp.responseText !== undefined && resp.responseText.indexOf('RequestDataTooBig') !== -1) {
        error = 'L"image est trop lourde.'
      } else if (resp.responseJSON !== undefined) {
        error = resp.responseJSON[0]
      } else if (resp.responseText !== undefined) {
        error = 'Erreur ' + resp.status + ' ' + resp.statusText + ' : ' + "'" + resp.responseText.split('\n')[0] + "'"
      } else if (resp.readyState === 0 && resp.statusText === 'error') {
        error = 'Oups ! Impossible de se connecter au serveur.'
      }
      onError(error)
    })
  }

  $('.md-editor').each(function() {
    var textarea = this
    var formEditor = $(this).closest('form')
    const mdeUniqueKey = (window.location.pathname + window.location.search + '@' + this.getAttribute('name')).replace(/[?|&]page=(\d+)/g, '')

    const smdeUniqueContent = localStorage.getItem('smde_' + mdeUniqueKey)
    let minHeight = 500

    if ($(this).hasClass('mini-editor')) {
      minHeight = 200
    }

    var customMarkdownParser = function(plainText, preview) {
      var editor = window.editors[textarea.id]
      var request = function() {
        $.ajax({
          url: formEditor.attr('action'),
          type: 'POST',
          data: {
            csrfmiddlewaretoken: csrf,
            text: plainText,
            last_post: '',
            preview: 'preview'
          },
          success: function(data) {
            preview.innerHTML = data
          },
          async: true
        })
      }

      clearTimeout(editor.timeout)
      editor.timeout = setTimeout(request, 600)
      editor.previous_value = plainText

      return null
    }

    /* global EasyMDE */
    var easyMDE = new EasyMDE({
      autoDownloadFontAwesome: false,
      element: this,
      autosave: {
        enabled: true,
        uniqueId: mdeUniqueKey,
        submit_delay: 10000,
        delay: 1000
      },
      indentWithTabs: false,
      minHeight: minHeight + 'px',
      placeholder: 'Votre message au format Markdown',
      promptURLs: true,
      promptTexts: {
        image: 'Url de votre image',
        link: 'Url de votre lien'
      },
      uploadImage: true,
      imageUploadFunction: uploadImage,
      imageTexts: {
        sbInit: 'Joindre des images par glisser-déposer ou coller depuis le presse-papiers.',
        sbOnDragEnter: 'Déposer l"image pour l"envoyer dans votre galérie',
        sbOnDrop: 'Téléchargement d"images #images_names#',
        sbProgress: 'Téléchargement #file_name#: #progress#%',
        sbOnUploaded: 'Image téléchargée #image_name#'
      },
      spellChecker: false,
      inputStyle: 'contenteditable',
      nativeSpellcheck: true,
      promptAbbrv: true,
      theme: 'idea',
      previewRender: customMarkdownParser,
      syncSideBySidePreviewScroll: false,
      toolbar: [
        {
          name: 'bold',
          action: EasyMDE.toggleBold,
          className: 'fa fa-bold',
          title: 'Gras'
        },
        {
          name: 'italic',
          action: EasyMDE.toggleItalic,
          className: 'fa fa-italic',
          title: 'Italique'
        },
        {
          name: 'strikethrough',
          action: EasyMDE.toggleStrikethrough,
          className: 'fa fa-strikethrough',
          title: 'Barré'
        },
        {
          name: 'abbr',
          action: (e) => {
            var options = e.options
            var cm = e.codemirror
            var abbr = cm.getSelection()
            var description = ''
            var lastLine = cm.lastLine()
            var lastCh = cm.getLine(lastLine).length

            var startPoint = cm.getCursor('start')
            var endPoint = cm.getCursor('end')

            if (options.promptAbbrv) {
              if (abbr.length === 0) {
                abbr = prompt('Mot abrégé', '')
                if (abbr.length === 0) {
                  return false
                }
              }
              description = prompt('Description de l"abbréviation', '')
            }

            cm.replaceRange(cm.lineSeparator() + cm.lineSeparator() + '*[' + abbr + ']: ' + description, { line: lastLine, ch: lastCh }, { line: lastLine, ch: maxRange })
            cm.setSelection(startPoint, endPoint)
            cm.focus()
          },
          className: 'fa fa-text-width',
          title: 'Abbréviation'
        },
        {
          name: 'keyboard',
          action: (e) => {
            _toggleBlockZmd(e, 'keyboard', '||')
          },
          className: 'far fa-keyboard',
          title: 'Touche clavier'
        },
        {
          name: 'codeInline',
          action: (e) => {
            _toggleBlockZmd(e, 'codeInline', '`')
          },
          className: 'fa fa-terminal',
          title: 'Code inline'
        },
        '|',
        {
          name: 'superscript',
          action: (e) => {
            _toggleBlockZmd(e, 'superscript', '^')
          },
          className: 'fa fa-superscript',
          title: 'Exposant'
        },
        {
          name: 'subscript',
          action: (e) => {
            _toggleBlockZmd(e, 'subscript', '~')
          },
          className: 'fa fa-subscript',
          title: 'Indice'
        },
        '|',
        {
          name: 'alignCenter',
          action: (e) => {
            _toggleBlockZmd(e, 'alignCenter', '-> ', ' <-')
          },
          className: 'fa fa-align-center',
          title: 'Aligner au centre'
        },
        {
          name: 'alignRight',
          action: (e) => {
            _toggleBlockZmd(e, 'alignRight', '-> ', ' ->')
          },
          className: 'fa fa-align-right',
          title: 'Aligner a droite'
        },
        '|',
        {
          name: 'list-ul',
          action: EasyMDE.toggleUnorderedList,
          className: 'fa fa-list-ul',
          title: 'Liste à puces'
        },
        {
          name: 'ordered-list',
          action: EasyMDE.toggleOrderedList,
          className: 'fa fa-list-ol',
          title: 'Liste ordonnée'
        },
        {
          name: 'checklist',
          action: (e) => {
            _toggleBlockZmd(e, 'checklist', '- [ ] ')
          },
          className: 'far fa-check-square',
          title: 'Liste de taches'
        },
        '|',
        {
          name: 'heading',
          action: EasyMDE.toggleHeadingSmaller,
          className: 'fas fa-heading',
          title: 'Titres'
        },
        '|',
        {
          name: 'image',
          action: EasyMDE.drawImage,
          className: 'far fa-image',
          title: 'Image'
        },
        {
          name: 'link_btn',
          action: EasyMDE.drawLink,
          className: 'fa fa-link',
          title: 'Lien'
        },
        '|',
        {
          name: 'quote',
          action: EasyMDE.toggleBlockquote,
          className: 'fa fa-quote-left',
          title: 'Citation'
        },
        {
          name: 'code',
          action: EasyMDE.toggleCodeBlock,
          className: 'fa fa-code',
          title: 'Bloc de code coloré'
        },
        {
          name: 'math',
          action: (e) => {
            _toggleBlockZmd(e, 'math', '$$')
          },
          className: 'fa fa-percent',
          title: 'Formule mathématique'
        },
        {
          name: 'table',
          action: EasyMDE.drawTable,
          className: 'fa fa-table',
          title: 'Table'
        },
        '|',
        {
          name: 'blocMenu',
          action: (e) => {
            _toggleBlockZmd(e, 'blocInformation', '| ')
          },
          className: 'fa fa-info',
          title: 'Bloc information',
          children: [
            {
              name: 'blocInformation',
              action: (e) => {
                _toggleBlockZmd(e, 'blocInformation', '| ')
              },
              className: 'fa fa-info',
              title: 'Bloc information'
            },
            {
              name: 'blocQuestion',
              action: (e) => {
                _toggleBlockZmd(e, 'blocQuestion', '| ')
              },
              className: 'fa fa-question',
              title: 'Bloc question'
            },
            {
              name: 'blocError',
              action: (e) => {
                _toggleBlockZmd(e, 'blocError', '| ')
              },
              className: 'fas fa-times-circle',
              title: 'Bloc erreur'
            },
            {
              name: 'blocSecret',
              action: (e) => {
                _toggleBlockZmd(e, 'blocSecret', '| ')
              },
              className: 'fa fa-eye-slash',
              title: 'Bloc secret'
            },
            {
              name: 'blocNeutral',
              action: (e) => {
                _toggleBlockZmd(e, 'blocNeutral', '| ')
              },
              className: 'fa fa-sticky-note',
              title: 'Bloc neutre'
            }
          ]
        },
        '|',
        {
          name: 'abc-spellchecker',
          action: (evt) => {},
          className: 'fas fa-spell-check',
          title: 'Correcteur orthographique externe'
        },
        {
          name: 'abc-grammalecte',
          action: (evt) => {
            oGrammalecteAPI.openPanelForText(easyMDE.codemirror.getValue(), easyMDE.codemirror.display.lineDiv)
          },
          className: 'zdsicon zi-grammalecte',
          title: 'Correcteur orthographique externe'
        },
        {
          name: 'switch-contentAreaStyle',
          action: (evt) => {
            const wrapper = easyMDE.codemirror.getWrapperElement()
            $(wrapper.parentElement).children('.textarea-multivers').toggle()
            $(wrapper).toggle()
            easyMDE.codemirror.refresh()
          },
          className: 'fas fa-broom',
          title: 'Passe au mode compatibilité'
        },
        '|',
        {
          name: 'preview',
          action: EasyMDE.togglePreview,
          className: 'fa fa-eye no-disable',
          title: 'Aperçu'
        },
        {
          name: 'side-by-side',
          action: EasyMDE.toggleSideBySide,
          className: 'fa fa-columns no-disable no-mobile',
          title: 'Aperçu sur le coté'
        },
        {
          name: 'fullscreen',
          action: EasyMDE.toggleFullScreen,
          className: 'fa fa-arrows-alt no-disable no-mobile',
          title: 'Plein écran'
        }
      ]
    })

    if (smdeUniqueContent != null && localStorage['smde_' + mdeUniqueKey] !== textarea.value) {
      const $alertbox = $('<div class="alert-box info"></div>')

      const $hide = $("<a>Masquer l'alerte</a>")

      $hide.attr({
        href: 'javascript:void(0)',
        class: 'close-alert-box ico-after cross white',
        title: "Masquer l'alerte (raccourci clavier: Echap)"
      })

      const $undo = $('<a href="javascript:void(0)">cliquant ici</a>.').click(function() {
        window.editors[textarea.id].value(textarea.value)
        easyMDE.codemirror.off('keyHandled', onKeyHandled)
        localStorage.removeItem('smde_' + mdeUniqueKey)
        $alertbox.hide(() => $(this).remove())
      })

      $undo.attr({
        href: 'javascript:void(0)',
        title: 'Revenir à la version originale (non sauvegardée)'
      })

      const onKeyHandled = (cm, name) => {
        if (name === 'Ctrl-Z' || name === 'Esc') {
          easyMDE.codemirror.off('keyHandled', onKeyHandled)
          $alertbox.hide(() => $(this).remove())
        }

        return true
      }

      easyMDE.codemirror.on('keyHandled', onKeyHandled)

      const spanContent = [
        "La version actuelle du contenu provient d'une sauvegarde de votre navigateur. ",
        'Vous pouvez revenir à la version originale (du serveur) avec CTRL+Z ou en ',
        $undo,
        '.'
      ]

      $('<span></span>')
        .append(spanContent)
        .appendTo($alertbox)
        .after($hide)

      $alertbox.insertAfter($(this).parent().children('.editor-toolbar'))
    }

    window.editors[this.id] = easyMDE
    window.editors[this.id].timeout = 0
    window.editors[this.id].previous_value = ''

    function submit(cm) {
      if (cm.getValue() !== '') formEditor.submit()
    }

    easyMDE.codemirror.addKeyMap({
      'Ctrl-Enter': submit
    })
    easyMDE.codemirror.addKeyMap({
      'Cmd-Enter': submit
    })

    this.removeAttribute('required')

    const $twin = mirroringEasyMDE(easyMDE, textarea)

    $twin.css('minHeight', minHeight + 22 + 'px')

    spellcheckerEasyMDE(easyMDE)
  })
})(jQuery)


function mirroringEasyMDE(easyMDE, textarea) {
  const $twin = $('<textarea></textarea>')

  $twin.attr({
    'data-antidoteapi_jsconnect_groupe_id': '01',
    placeholder: textarea.placeholder,
    class: 'textarea-multivers',
    style: 'display: none;'
  })

  $twin.val(easyMDE.codemirror.getValue())

  $twin.on('change input', function() {
    easyMDE.codemirror.setValue($twin.val())
  })
  easyMDE.codemirror.on('change', function(cm) {
    $twin.val(cm.getValue())
  })
  $twin.on('mousedown select keyup blur', function() {
    setTimeout(() => {
      const cm = easyMDE.codemirror
      const start = convertAbsolute2CmPosition(cm, $twin[0].selectionStart)
      const end = convertAbsolute2CmPosition(cm, $twin[0].selectionEnd)
      cm.setSelection(start, end)
    }, 12) // <-- after default trigger (I mean after browser trigger)
  })

  $(easyMDE.element.parentElement).children('.CodeMirror').before($twin)

  return $twin
}

function getPositionConverterArray(text) {
  const lines = text.split('\n')
  const linesLength = lines.map((line, i) => line.length)

  return ((arr) => {
    for (let i = 0, length = 0; i < lines.length; i++, length += linesLength[i - 1] + 1) {
      arr.push(length)
    }
    return arr
  })([])
}

function convertCm2AbsolutePosition(cm, pos) { // eslint-disable-line no-unused-vars
  const text = cm.getValue()
  const sumLinesLength = getPositionConverterArray(text)

  return sumLinesLength[pos.line] + pos.ch
}

function convertAbsolute2CmPosition(cm, pos) {
  const text = cm.getValue()
  const sumLinesLength = getPositionConverterArray(text)

  const index = sumLinesLength.findIndex((num) => num > pos)
  const line = ((index > -1) ? index : sumLinesLength.length) - 1

  return {
    line: line,
    ch: pos - sumLinesLength[line]
  }
}

function spellcheckerEasyMDE(easyMDE) {
  $(easyMDE.toolbarElements['abc-spellchecker']).attr({
    'data-antidoteapi_jsconnect_groupe_id': '01',
    'data-antidoteapi_jsconnect_lanceoutil': 'C'
  })

  const contenteditable = easyMDE.codemirror.display.lineDiv
  $(contenteditable).attr({
    'data-grammalecte_button': false,
    'data-grammalecte_result_via_event': true
  })

  contenteditable.addEventListener('GrammalecteResult', function(event) {
    const detail = (typeof event.detail === 'string') && JSON.parse(event.detail)

    if (detail && detail.sType === 'text') {
      easyMDE.codemirror.setValue(detail.sText)
    }
  })

  if (typeof oGrammalecteAPI !== 'object' || oGrammalecteAPI === null) {
    $(easyMDE.toolbarElements['abc-grammalecte']).hide()

    document.addEventListener('GrammalecteLoaded', function(event) {
      $(easyMDE.toolbarElements['abc-grammalecte']).show()
    })
  }

  if (typeof estPresentAntidoteAPI_JSConnect === 'function' && estPresentAntidoteAPI_JSConnect()) { // eslint-disable-line camelcase
    activeAntidoteAPI_JSConnect()
  } else {
    $(easyMDE.toolbarElements['abc-spellchecker']).hide()
  }

  if (!window.thereIsAlreadyAStalkerOnThisPage) {
    window.thereIsAlreadyAStalkerOnThisPage = true
    const stalker = new MutationObserver(function(events) {
      events.forEach((ev) => {
        if (ev.type === 'attributes' && ev.attributeName === 'data-antidoteapi_jsconnect_initlistener') {
          $(easyMDE.toolbarElements['abc-spellchecker']).show()
          stalker.disconnect()
        }
      })
    })
    setTimeout(() => stalker.disconnect(), 30000)
    stalker.observe(easyMDE.toolbarElements['abc-spellchecker'], { attributes: true })
  }
}
