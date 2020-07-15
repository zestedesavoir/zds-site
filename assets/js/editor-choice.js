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
        'Vous utilisez actuellement notre éditeur historique. Nous développons un nouvel éditeur',
        ' encore expérimental.'
      ]
      linkMessage = 'Essayer le nouvel éditeur'
      alternativeChoice = 'new'
    } else {
      message = 'Vous utilisez actuellement notre nouvel éditeur. Attention, il est au stade expérimental !'
      linkMessage = "Revenir à l'éditeur historique"
      alternativeChoice = 'old'
    }

    const link = "javascript:localStorage.setItem('editor_choice', '" + alternativeChoice + "');document.location.reload(true);"
    const box = $('<div class="alert-box"><p>' + message + '</p><a href="' + link + '" class="btn">' + linkMessage + '</a></div>')
    box.insertBefore(this)
  })
})(jQuery)
