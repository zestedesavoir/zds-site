/* ===== Zeste de Savoir ====================================================
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document ,$, undefined){
    "use strict";

    function addDocMD($elem){
        $elem.each(function(){
            var $help = $("<div/>", {
                "class": "markdown-help",
                "html": "<div class=\"markdown-help-more\">" +
                        "<p>Les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne</em> !</p>" +
                        "<pre><code>**gras** \n*italique* \n[texte de lien](url du lien) \n> citation \n+ liste à puces </code></pre>" +
                        "<a href=\"//zestedesavoir.com/tutoriels/221/rediger-sur-zds/\">Voir la documentation complète du markdown</a>" +
                        "<p>Vous pouvez également <a href=\"//zestedesavoir.com/tutoriels/202/comment-rediger-des-maths-sur-zeste-de-savoir/\">écrire des formules mathématiques</a> en encadrant ces dernières du signe dollar ($) !</p></div>"+
                        "<a href=\"#open-markdown-help\" class=\"open-markdown-help btn btn-grey ico-after help\">"+
                            "<span class=\"close-markdown-help-text\">Masquer</span>" +
                            "<span class=\"open-markdown-help-text\">Afficher</span> l'aide Markdown" +
                        "</a>"
            });
            $(this).after($help);
            $(".open-markdown-help, .close-markdown-help", $help).click(function(e){
                $(".markdown-help-more", $help).toggleClass("show-markdown-help");
                e.preventDefault();
                e.stopPropagation();
            });
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
