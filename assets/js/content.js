/*
 * Allow the user to compare two commits
 */
(function(document, $, undefined){
  'use strict';

  function hideMoveButton() {
    /* TODO : REMOVE this and update the selectlist with js */
    /* because the list is not updated */
    $('.simple-move-button').hide();
  }

  $(document).ready(function(){
    $('ol[data-children-type=section]').sortable({
      group: 'section',
      handle: 'a',
      filter: function (pointer, dragged) {
        return $(dragged).is('.simple-create-button');
      },
      onMove: (evt) => {
        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!$to.is($from)) {
          // Element is dragged into the list from another list
          if ($from.parent().is('.article-containers > .article-part')) { // is: chapter > section
            $(evt.dragged).find('> h4 > a').unwrap().wrap('<h3></h3>');
          } else { // is: part > chapter > section 
            $(evt.dragged).find('> h3 > a').unwrap().wrap('<h4></h4>');
          }
        }

        if ($(evt.related).is('.simple-create-button')) {
          return -1;
        }
      },
      onEnd: hideMoveButton
    })
    $('*[data-children-type=container]').sortable({
      group: 'container',
      handle: ["h2", "h3 a"],
      filter: function (pointer, dragged) {
        return $(dragged).is('.simple-create-part');
      },
      onMove: (evt) => {
        if ($(evt.related).is('.simple-create-part')) {
          return false;
        }

        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!$to.is($from)) {
          // Element is dragged into the list from another list
          if ($to.is('section')) { // is: chapter > section
            $(evt.dragged).find('> h3 > a').unwrap().wrap('<h2></h2>');
            $(evt.dragged).find('ol h4 > a').unwrap().wrap('<h3></h3>');
          } else { // is: part > chapter > section 
            $(evt.dragged).find('> h2 > a').unwrap().wrap('<h3></h3>');
            $(evt.dragged).find('ol h3 > a').unwrap().wrap('<h4></h4>');
          }
        }
      },
      onEnd: hideMoveButton
    });
  })
})(document, jQuery);
