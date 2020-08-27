/* ===== Zeste de Savoir ====================================================
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

window.markdown_tips_tutorial_link = '//zestedesavoir.com/tutoriels/221/rediger-sur-zds/'

const linkToMathsTutorial = '//zestedesavoir.com/tutoriels/244/comment-rediger-des-maths-sur-zeste-de-savoir/'
const linkToSupportedLanguages = 'https://github.com/highlightjs/highlight.js/blob/master/SUPPORTED_LANGUAGES.md'

window.markdown_tips = [
  'les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne</em> !',
  'encadrez votre texte par une astérisque pour écrire en italique ou deux pour du gras.',
  'pour écrire un lien, utilisez la syntaxe <code>[texte de lien](url du lien)</code>',
  'les blocs de code sont délimités par trois accents graves <code>```</code>.',
  'pour créer une liste à puces, sautez une ligne et commencez chaque élément de la liste par <code>+</code>, <code>-</code> ou <code>*</code>.',
  "pour citer quelqu'un, utilisez le symbole <code>></code>.",
  'pour tracer une ligne, utilisez <code>---</code>, <code>+++</code> ou <code>***</code>.',
  'pour aller à la ligne sans changer de paragraphe, finissez votre première ligne par deux espaces.',
  'pour écrire un bout de code au milieu d’une phrase, utilisez la syntaxe <code>`un bout de code`</code>.',
  'le langage d’un bloc de code peut être spécifié après les <code>```</code> ouvrants. <a href="' + linkToSupportedLanguages + '">La liste des langages supportés est disponible ici.</a>',
  'vous pouvez <a href="' + linkToMathsTutorial + '">écrire des formules mathématiques</a> en encadrant ces dernières du signe dollar <code>$</code>.',
  'pour ajouter une image, vous pouvez simplement la glisser-déposer depuis votre explorateur.',
  'vous pouvez préciser à quel numéro commencent les lignes avec cette syntaxe : <code>```python linenostart=42</code> au début d\'un bloc de code. Pratique pour faire coïncider les numéros de ligne à une erreur, par exemple.',
  'vous pouvez surligner des lignes avec cette syntaxe : <code>```rust hl_lines=2,4-7</code> au début d\'un bloc de code.',
  'vous pouvez à la fois choisir à quel numéro démarrent les lignes et en surligner avec <code>```lisp linenostart=244 hl_lines=247,252</code> au début d\'un bloc de code.'
]; // required semicolon

(function($) {
  'use strict'

  function addDocMD($elem) {
    $elem.each(function() {
      var $help = $('<div/>', {
        class: 'markdown-help',
        html: '<strong>Astuce :</strong> ' + window.markdown_tips[Math.floor(Math.random() * window.markdown_tips.length)] + ' <a href="' + window.markdown_tips_tutorial_link + "\">Envie d'en savoir plus ?</a><a href='#close-alert-box' class='close-alert-box ico-after cross'>Masquer</a>"
      })

      $(this).after($help)
    })
  }


  $(document).ready(function() {
    if ($('body').data('show-markdown-help') && localStorage.getItem('editor_choice') === 'old') {
      addDocMD($('.md-editor'))

      $('#content').on('DOMNodeInserted', '.md-editor', function(e) {
        var $editor = $(e.target)
        if ($editor.next().hasClass('markdown-help') === false) {
          addDocMD($editor)
        }
      })
    }
  })
})(jQuery)
