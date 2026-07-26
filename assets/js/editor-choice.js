(function($) {
  'use strict'

  let choice = localStorage.getItem('editor_choice')
  if (!choice || (choice !== 'old' && choice !== 'new')) {
    localStorage.setItem('editor_choice', 'old')
    choice = 'old'
  }

  $('.md-editor').each(function() {
    let message, linkMessage, alternativeChoice
    if (choice === 'old') {
      message = [
        'Vous utilisez actuellement notre éditeur historique. Nous sommes en train de développer un nouvel éditeur',
        ' encore au stade expérimental.'
      ]
      linkMessage = 'Essayer le nouvel éditeur.'
      alternativeChoice = 'new'
    } else {
      message = 'Vous utilisez actuellement notre nouvel éditeur. Attention, il est au stade expérimental !'
      linkMessage = "Revenir à l'éditeur historique."
      alternativeChoice = 'old'
    }

    const box = $('<div class="markdown-help">' + message + ' <a href="#" class="editor-toggle" data-choice="' + alternativeChoice + '">' + linkMessage + '</a></div>')
    box.insertBefore(this)
    box.find('.editor-toggle').on('click', function(e) {
      e.preventDefault()
      localStorage.setItem('editor_choice', $(this).data('choice'))
      document.location.reload(true)
    })
  })
})(jQuery)
