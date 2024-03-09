/* globals oGrammalecteAPI, estPresentAntidoteAPI_JSConnect, activeAntidoteAPI_JSConnect */ // eslint-disable-line camelcase
(function($) {
  'use strict'
  const $saveButton = $('.inline-save-button')
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
    const $btn = $(this)
    const $form = $btn.parents('form:first')
    let idInstance
    if ($form.find('.preview-source').length) {
      idInstance = $btn.closest('div').prev().find('.md-editor').prop('id')
    } else {
      idInstance = $form.find('.md-editor').prop('id')
    }
    const text = window.editors[idInstance].value()

    const csrfmiddlewaretoken = $form.find('input[name=csrfmiddlewaretoken]').val()
    const lastPost = $form.find('input[name=last_post]').val()

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
    const found = String(str).match(reg)
    if (found) {
      return found.length > 0
    }
  }

  function getStateZmd(cm) {
    const posStart = cm.getCursor('start')
    const posEnd = cm.getCursor('end')
    const line = cm.getLine(posStart.line)
    const ret = {}
    let i

    const beforeChars = line.slice(0, posStart.ch).match(/^(\S)+/g)
    const afterChars = line.slice(posEnd.ch).match(/(\S)+$/g)


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
      let isBlock = true
      for (i = (posStart.line) + 1; i <= posEnd.line; i++) {
        if ((!cm.getLine(i).startsWith('| ')) && (cm.getLine(i) !== '')) {
          isBlock = false
          break
        }
      }
      if (isBlock) {
        const reg = /^\[\[(.+)\]\]$/
        const m = reg.exec(line)
        const _titleContents = m[1].split('|')
        const _type = _titleContents[0].trim()
        if (_type === 'i' || _type === 'information') {
          ret.blocInformation = true
        } else if (_type === 'q' || _type === 'question') {
          ret.blocQuestion = true
        } else if (_type === 'a' || _type === 'attention') {
          ret.blocWarning = true
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
      let isCheckList = true
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
    let nextText
    let currentText
    const lastLine = cm.lastLine()
    for (let i = lineNumber; i <= lastLine + 1; i++) {
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
    for (let i = lineStart + 1; i <= lineEnd; i++) {
      cm.replaceRange(cm.getLine(i).slice(2), { line: i, ch: 0 }, { line: i, ch: maxRange })
    }
    cm.replaceRange('', { line: lineStart, ch: 0 }, { line: lineStart + 1, ch: 0 })
  }

  function disableBlockZmd(cm, type, startChars, endChars, startPoint, endPoint) {
    let i, m, start, end

    const text = cm.getLine(startPoint.line)
    start = text.slice(0, startPoint.ch)
    end = text.slice(startPoint.ch)
    let offset = 0
    if (type === 'blocInformation' || type === 'blocQuestion' || type === 'blocWarning' || type === 'blocError' || type === 'blocSecret' || type === 'blocNeutral') {
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
    if (type === 'blocInformation' || type === 'blocQuestion' || type === 'blocWarning' || type === 'blocError' || type === 'blocSecret' || type === 'blocNeutral') {
      // blocs
      for (i = startPoint.line; i <= endPoint.line; i++) {
        text = start + cm.getLine(i)
        cm.replaceRange(text, { line: i, ch: 0 }, { line: i, ch: maxRange })
      }
      if (type === 'blocInformation') {
        shiftLines(cm, startPoint.line, '[[information]]')
      } else if (type === 'blocQuestion') {
        shiftLines(cm, startPoint.line, '[[question]]')
      } else if (type === 'blocWarning') {
        shiftLines(cm, startPoint.line, '[[attention]]')
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

  function toggleEmoji(cm, str) {
    cm.replaceSelection(str + ' ')
    cm.focus()
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

  const uploadImage = function(file, onSuccess, onError) {
    const galleryUrl = '/api/galeries/' + document.body.getAttribute('data-gallery') + '/images/'

    const formData = new FormData()
    formData.append('physical', file)
    formData.append('title', file.name)
    // WARN: if you test zds with sqlite, you can't upload multiple files at a time
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
      let error = 'Erreur inconnue'
      if (resp.responseText !== undefined && resp.responseText.indexOf('RequestDataTooBig') !== -1) {
        error = 'L\'image est trop lourde.'
      } else if (resp.responseJSON !== undefined) {
        error = resp.responseJSON[0]
      } else if (resp.responseText !== undefined) {
        if (parseInt(resp.status) === 400) {
          error = 'Quelque chose s\'est mal passé lors de l\'envoi. Votre image est peut-être trop lourde.'
        } else {
          error = 'Erreur ' + resp.status + ' ' + resp.statusText + ' : ' + "'" + resp.responseText.split('\n')[0] + "'"
        }
      } else if (resp.readyState === 0 && resp.statusText === 'error') {
        error = 'Oups ! Impossible de se connecter au serveur.'
      }
      onError(error)
    })
  }

  $('.md-editor').each(function() {
    const textarea = this
    const formEditor = $(this).closest('form')
    const mdeUniqueKey = (window.location.pathname + window.location.search + '@' + this.getAttribute('name')).replace(/[?|&]page=(\d+)/g, '')

    const smdeUniqueContent = localStorage.getItem('smde_' + mdeUniqueKey)
    let minHeight = 500

    if ($(this).hasClass('mini-editor')) {
      minHeight = 200
    }

    const customMarkdownParser = function(plainText, preview) {
      const editor = window.editors[textarea.id]
      const request = function() {
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
    const easyMDE = new EasyMDE({
      autoDownloadFontAwesome: false,
      element: this,
      forceSync: true,
      autosave: {
        enabled: true,
        uniqueId: mdeUniqueKey,
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
        sbOnDragEnter: 'Déposez l\'image pour l\'envoyer dans votre galerie.',
        sbOnDrop: 'Téléchargement d\'images #images_names#',
        sbProgress: 'Téléchargement #file_name#: #progress#%',
        sbOnUploaded: 'Image téléchargée #image_name#'
      },
      spellChecker: false,
      inputStyle: 'contenteditable',
      nativeSpellcheck: true,
      sideBySideFullscreen: false,
      promptAbbrv: true,
      theme: 'zest',
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
            const options = e.options
            const cm = e.codemirror
            let abbr = cm.getSelection()
            let description = ''
            const lastLine = cm.lastLine()
            const lastCh = cm.getLine(lastLine).length

            const startPoint = cm.getCursor('start')
            const endPoint = cm.getCursor('end')

            if (options.promptAbbrv) {
              if (abbr.length === 0) {
                abbr = prompt('Mot abrégé', '')
                if (abbr.length === 0) {
                  return false
                }
              }
              description = prompt('Description de l\'abbréviation', '')
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

          },
          className: 'fa fa-smile',
          title: 'Emojis heureux',
          children: [
            {
              name: 'char1',
              action: (e) => {
                toggleEmoji(e.codemirror, ':)')
              },
              className: 'emoji smile',
              title: ':)'
            },
            {
              name: 'char2',
              action: (e) => {
                toggleEmoji(e.codemirror, ':D')
              },
              className: 'emoji heureux',
              title: ':D'
            },
            {
              name: 'char3',
              action: (e) => {
                toggleEmoji(e.codemirror, ';)')
              },
              className: 'emoji clin',
              title: ';)'
            },
            {
              name: 'char8',
              action: (e) => {
                toggleEmoji(e.codemirror, ':soleil:')
              },
              className: 'emoji soleil',
              title: ':soleil:'
            },
            {
              name: 'char4',
              action: (e) => {
                toggleEmoji(e.codemirror, ':p')
              },
              className: 'emoji langue',
              title: ':P'
            },
            {
              name: 'char5',
              action: (e) => {
                toggleEmoji(e.codemirror, ':lol:')
              },
              className: 'emoji rire',
              title: ':lol:'
            },
            {
              name: 'char6',
              action: (e) => {
                toggleEmoji(e.codemirror, '^^')
              },
              className: 'emoji hihi',
              title: '^^'
            },
            {
              name: 'char7',
              action: (e) => {
                toggleEmoji(e.codemirror, ':ange:')
              },
              className: 'emoji ange',
              title: ':ange:'
            },
            {
              name: 'char9',
              action: (e) => {
                toggleEmoji(e.codemirror, ':popcorn:')
              },
              className: 'emoji popcorn',
              title: ':popcorn:'
            },
            {
              name: 'char10',
              action: (e) => {
                toggleEmoji(e.codemirror, ':bounce:')
              },
              className: 'emoji bounce',
              title: ':bounce:'
            }
          ]
        },
        {
          name: 'blocMenu',
          action: (e) => {

          },
          className: 'fa fa-frown',
          title: 'Emojis mécontents',
          children: [
            {
              name: 'char1',
              action: (e) => {
                toggleEmoji(e.codemirror, ':(')
              },
              className: 'emoji triste',
              title: ':('
            },
            {
              name: 'char2',
              action: (e) => {
                toggleEmoji(e.codemirror, ':colere:')
              },
              className: 'emoji angry',
              title: ':colere:'
            },
            {
              name: 'char3',
              action: (e) => {
                toggleEmoji(e.codemirror, ':colere2:')
              },
              className: 'emoji mechant',
              title: ':colere2:'
            },
            {
              name: 'char4',
              action: (e) => {
                toggleEmoji(e.codemirror, ':diable:')
              },
              className: 'emoji diable',
              title: ':diable:'
            },
            {
              name: 'char5',
              action: (e) => {
                toggleEmoji(e.codemirror, ':\'(')
              },
              className: 'emoji pleure',
              title: ':\'('
            },
            {
              name: 'char6',
              action: (e) => {
                toggleEmoji(e.codemirror, '>_<')
              },
              className: 'emoji pinch',
              title: '>_<'
            }
          ]
        },
        {
          name: 'blocMenu',
          action: (e) => {

          },
          className: 'fa fa-meh',
          title: 'Emojis autres',
          children: [
            {
              name: 'char1',
              action: (e) => {
                toggleEmoji(e.codemirror, ':euh:')
              },
              className: 'emoji unsure',
              title: ':euh:'
            },
            {
              name: 'char2',
              action: (e) => {
                toggleEmoji(e.codemirror, ':o')
              },
              className: 'emoji huh',
              title: ':o'
            },
            {
              name: 'char3',
              action: (e) => {
                toggleEmoji(e.codemirror, ':B')
              },
              className: 'emoji b',
              title: ':B'
            },
            {
              name: 'char4',
              action: (e) => {
                toggleEmoji(e.codemirror, 'o_O')
              },
              className: 'emoji blink',
              title: 'o_O'
            },
            {
              name: 'char5',
              action: (e) => {
                toggleEmoji(e.codemirror, ':-°')
              },
              className: 'emoji siffle',
              title: ':-°'
            },
            {
              name: 'char6',
              action: (e) => {
                toggleEmoji(e.codemirror, ':magicien:')
              },
              className: 'emoji magicien',
              title: ':magicien:'
            },
            {
              name: 'char8',
              action: (e) => {
                toggleEmoji(e.codemirror, ':pirate:')
              },
              className: 'emoji pirate',
              title: ':pirate:'
            },
            {
              name: 'char9',
              action: (e) => {
                toggleEmoji(e.codemirror, ':honte:')
              },
              className: 'emoji rouge',
              title: ':honte:'
            },
            {
              name: 'char10',
              action: (e) => {
                toggleEmoji(e.codemirror, ':waw:')
              },
              className: 'emoji waw',
              title: ':waw:'
            },
            {
              name: 'char11',
              action: (e) => {
                toggleEmoji(e.codemirror, ':zorro:')
              },
              className: 'emoji zorro',
              title: ':zorro:'
            },
            {
              name: 'char7',
              action: (e) => {
                toggleEmoji(e.codemirror, ':ninja:')
              },
              className: 'emoji ninja',
              title: ':ninja:'
            }
          ]
        },
        '|',
        {
          name: 'blocMenu',
          action: (e) => {
            _toggleBlockZmd(e, 'blocInformation', '| ')
          },
          className: 'fa fa-info',
          title: 'Bloc spéciaux',
          children: [
            {
              name: 'blocInformation',
              action: (e) => {
                _toggleBlockZmd(e, 'blocInformation', '| ')
              },
              className: 'fa fa-info bloc_information',
              title: 'Bloc information'
            },
            {
              name: 'blocQuestion',
              action: (e) => {
                _toggleBlockZmd(e, 'blocQuestion', '| ')
              },
              className: 'fa fa-question bloc_question',
              title: 'Bloc question'
            },
            {
              name: 'blocWarning',
              action: (e) => {
                _toggleBlockZmd(e, 'blocWarning', '| ')
              },
              className: 'fas fa-exclamation-triangle bloc_warning',
              title: 'Bloc attention'
            },
            {
              name: 'blocError',
              action: (e) => {
                _toggleBlockZmd(e, 'blocError', '| ')
              },
              className: 'fas fa-times-circle bloc_error',
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
          className: 'fa zdsicon zi-grammalecte',
          title: 'Correcteur orthographique externe'
        },
        {
          name: 'switch-contentAreaStyle',
          action: (evt) => {
            if (easyMDE.isFullscreenActive()) {
              easyMDE.toggleFullScreen()
            }
            const wrapper = easyMDE.codemirror.getWrapperElement()
            $(wrapper.parentElement).children('.textarea-multivers').toggle()
            $(wrapper).toggle()
            // deactivating buttons incompatible with the textarea mode
            const $toolbar = $(easyMDE.element.parentElement).children('.editor-toolbar')
            if ($toolbar.hasClass('disabled-for-textarea-mode')) {
              $toolbar.removeClass('disabled-for-textarea-mode')
            } else {
              $toolbar.addClass('disabled-for-textarea-mode')
            }
            easyMDE.codemirror.refresh()
          },
          className: 'fas fa-remove-format',
          title: 'Zone de texte sans mise en forme'
        },
        '|',
        {
          name: 'preview',
          action: EasyMDE.togglePreview,
          className: 'fa fa-eye no-disable disable-for-textarea-mode',
          title: 'Aperçu'
        },
        {
          name: 'side-by-side',
          action: EasyMDE.toggleSideBySide,
          className: 'fa fa-columns no-disable no-mobile disable-for-textarea-mode',
          title: 'Aperçu sur le coté'
        },
        {
          name: 'fullscreen',
          action: EasyMDE.toggleFullScreen,
          className: 'fa fa-arrows-alt no-disable no-mobile disable-for-textarea-mode',
          title: 'Plein écran'
        }
      ]
    })

    if (smdeUniqueContent != null && localStorage['smde_' + mdeUniqueKey] !== textarea.defaultValue) {
      const $alertbox = $('<div class="alert-box info"></div>')

      const $hide = $("<a>Masquer l'alerte</a>")

      $hide.attr({
        href: 'javascript:void(0)',
        class: 'close-alert-box ico-after cross white',
        title: 'Masquer l\'alerte (raccourci clavier: Echap)'
      })

      const $undo = $('<a href="javascript:void(0)">cliquant ici</a>.').click(function() {
        window.editors[textarea.id].value(textarea.defaultValue)
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
        'La version actuelle du contenu provient d\'une sauvegarde de votre navigateur. ',
        'Vous pouvez revenir à la version originale (du serveur) en ',
        $undo,
        '.'
      ]

      $('<span></span>')
        .append(spanContent)
        .appendTo($alertbox)
        .after($hide)

      formEditor.find('.editor-toolbar').before($alertbox)
    }

    window.editors[this.id] = easyMDE
    window.editors[this.id].timeout = 0
    window.editors[this.id].previous_value = ''

    function submit(cm) {
      if (cm.getValue() !== '') {
        localStorage.removeItem('smde_' + mdeUniqueKey)
        formEditor.submit()
      }
    }

    easyMDE.codemirror.addKeyMap({
      'Ctrl-Enter': submit
    })
    easyMDE.codemirror.addKeyMap({
      'Cmd-Enter': submit
    })
    // Does not handle Ctrl + s
    easyMDE.codemirror.addKeyMap({
      'Ctrl-S': () => {
        if ($saveButton.length) {
          window.saveFormNoRedirect($($saveButton[0].form), $saveButton)
        }
      }
    })
    easyMDE.codemirror.addKeyMap({
      'Cmd-S': () => {
        if ($saveButton.length) {
          window.saveFormNoRedirect($($saveButton[0].form), $saveButton)
        }
      }
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

  $(easyMDE.element.parentElement).find('.editor-statusbar').before($twin)

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
