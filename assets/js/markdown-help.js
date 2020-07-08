/* ===== Zeste de Savoir ====================================================
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  var linkToMathsTutorial = '//zestedesavoir.com/tutoriels/244/comment-rediger-des-maths-sur-zeste-de-savoir/'
  var linkToMarkdownHelp = '//zestedesavoir.com/tutoriels/221/rediger-sur-zds/'
  var linkToPygments = 'http://pygments.org/languages'

  var tips = [
    'Les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne</em> !',
    'Encadrez votre texte par une astérisque pour écrire en italique ou deux pour du gras.',
    'Pour écrire un lien, utilisez la syntaxe <code>[texte de lien](url du lien)</code>',
    'Les blocs de code sont délimités par trois accents graves <code>```</code>.',
    'Pour créer une liste à puces, sautez une ligne et commencez chaque élément de la liste par <code>+</code>, <code>-</code> ou <code>*</code>.',
    "Pour citer quelqu'un, utilisez le symbole <code>></code>.",
    'Pour tracer une ligne, utilisez <code>---</code>, <code>+++</code> ou <code>***</code>.',
    'Pour aller à la ligne sans changer de paragraphe, finissez votre première ligne par deux espaces.',
    'Pour écrire un bout de code au milieu d’une phrase, utilisez la syntaxe <code>`un bout de code`</code>.',
    'Le langage d’un bloc de code peut être spécifié après les <code>```</code> ouvrants. La liste des langages supportés <a href="' + linkToPygments + '">est disponible ici</a>.',
    'Vous pouvez <a href="' + linkToMathsTutorial + '">écrire des formules mathématiques</a> en encadrant ces dernières du signe dollar <code>$</code>.',
    'Pour ajouter une image, vous pouvez simplement la glisser-déposer depuis votre explorateur.',
    'Vous pouvez préciser à quel numéro commencent les lignes avec cette syntaxe : <code>```python linenostart=42</code> au début d\'un bloc de code. Pratique pour faire coïncider les numéros de ligne à une erreur, par exemple.',
    'Vous pouvez surligner des lignes avec cette syntaxe : <code>```rust hl_lines=2,4-7</code> au début d\'un bloc de code.',
    'Vous pouvez à la fois choisir à quel numéro démarrent les lignes et en surligner avec <code>```lisp linenostart=244 hl_lines=247,252</code> au début d\'un bloc de code.'
  ]

  function addDocMD($elem) {
    $elem.each(function() {
      var $help = $('<div/>', {
        class: 'markdown-help',
        html: '<strong>Astuce :</strong> ' + tips[Math.floor(Math.random() * tips.length)] + ' <a href="' + linkToMarkdownHelp + "\">Envie d'en savoir plus ?</a><a href='#close-alert-box' class='close-alert-box ico-after cross'>Masquer</a>"
      })
      $(this).after($help)
    })
  }


  $(document).ready(function() {
    if ($('body').data('show-markdown-help')) {
      if (localStorage.getItem('editor_choice') === 'new') {
        addDocMD($('.editor-statusbar'))
      } else {
        addDocMD($('.md-editor'))
      }
      $('#content').on('DOMNodeInserted', '.md-editor', function(e) {
        var $editor = $(e.target)
        if ($editor.next().hasClass('markdown-help') === false) {
          addDocMD($editor)
        }
      })
    }
  })
})(jQuery)
