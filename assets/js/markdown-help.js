/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ========================================================================== */

(function($){
    "use strict";
    
    $(".md-editor").each(function(){
        var $help = $("<div/>", {
            "class": "markdown-help",
            "html": "<div class=\"markdown-help-more\">" +
                    "<pre><code>**gras** \n*italique* \n![texte de lien](url du lien) \n> citation \n+ liste a puces </code></pre>" +
                    "<p>Les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne</em> !</p>" +
                    "<a href=\"http://zestedesavoir.com/articles/1/rediger-sur-zds/\">Voir la documentation complète</a></div>" +
                    "<a href=\"#open-markdown-help\" class=\"open-markdown-help btn btn-grey ico-after view\">"+
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
})(jQuery);