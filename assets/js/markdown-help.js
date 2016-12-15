/* ===== Zeste de Savoir ====================================================
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document ,$, undefined){
    "use strict";

    var tips = [
        "Les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne !",
        "Pour écrire en italique encadrez votre texte par une astérisque, deux pour le gras.",
        "Pour écrire un lien utilisez la syntaxe <code>[texte de lien](url du lien)</code>",
        "Les blocs de code sont délimités par trois accents graves <code>```</code>.",
        "Pour les listes à puces, passez deux lignes et utilisez le moins <code>-</code>, le <code>+</code> ou l'astérisque <code>*</code>.",
        "Pour citer quelqu'un utilisez le symbole <code>></code>.",
        "Pour tracer une ligne utilisez <code>---</code>, ou <code>+++</code>, ou encore <code>***</code>."
        ];    
    
    function addDocMD($elem){
        $elem.each(function(){
            var $help = $("<div/>", {
                "class": "markdown-help",
                "html": "<strong>Conseil :</strong> " + tips[Math.floor(Math.random() * tips.length)] + " <a href=\"//zestedesavoir.com/tutoriels/221/rediger-sur-zds/\">En savoir plus.</a>"
            });
            $(this).after($help);
        });
    }
    

    $(document).ready(function(){
        addDocMD($(".md-editor"));
        $("#content").on("DOMNodeInserted", ".md-editor", function(e){
            var $editor = $(e.target);
            if($editor.next().hasClass("markdown-help") === false) {
                addDocMD($editor);
            }
        });
    });
})(document, jQuery);
