/* ===== Zeste de Savoir ====================================================
   Author: Alex-D / Alexandre Demode
   ---------------------------------
   Keyboard navigation in navigables lists, with j/k keys
   ========================================================================== */

(function($){
    var $list = $('.navigable-list');

    if($list.length === 1){
        var $navigableElems = $list.find('.navigable-elem');
        $('body').on('keydown', function(e){
            if(e.keyCode === 74 || e.keyCode === 75){
                var $current = $list.find('.navigable-elem.active'),
                    nextIndex = null;

                if($current.length === 1){
                    var currentIndex = $navigableElems.index($current);
                    if(e.keyCode === 75){ // J
                        if(currentIndex > 0)
                            nextIndex = currentIndex - 1;
                    } else { // K
                        if(currentIndex + 1 < $navigableElems.length)
                            nextIndex = currentIndex + 1;
                    }
                } else {
                    nextIndex = 0;
                }

                if(nextIndex !== null){
                    $current.removeClass('active');
                    activeNavigableElem($navigableElems.eq(nextIndex));
                }
            }
        });

        $list.find('.navigable-link').on('focus', function(){
            if(!$(this).parents('.navigable-elem:first').hasClass('active')){
                $list.find('.navigable-elem.active').removeClass('active');
                activeNavigableElem($(this).parents('.navigable-elem'));
            }
        });
        $list.find('.navigable-link').on('blur', function(){
            $(this).parents('.navigable-elem:first').removeClass('active');
        });
    } else if($list.length > 1){
        console.error("There is more than one .navigable-list element in this page !");
    }

    function activeNavigableElem($elem){
        $elem
            .addClass('active')
            .find('.navigable-link')
                .focus();
    }
})(jQuery);