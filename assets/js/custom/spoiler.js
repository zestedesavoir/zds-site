/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Toggle spoiler content
   ========================================================================== */

$('.spoiler').each(function(){
    $(this).before($('<a/>', {
        'text': "Afficher/Masquer le contenu masqué",
        'class': 'spoiler-title ico-after view',
        'href': 'javascript:void(null);',
        'click': function(){
            $(this).next('.spoiler').toggle();
        }
    }));
});