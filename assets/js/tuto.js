/*
 * Allow the user to compare two commits
 */
(function(document, $, undefined){
  "use strict"

  $(document).ready(function(){
    $("ol[data-children-type=section]").sortable({
      group: 'section',
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-button")
      },
      animation: 150,
      onMove: (evt) => {
        const $to = $(evt.related).parent()
        const $from = $(evt.dragged).parent()
        if (!$to.is($from)) {
          // Element is dragged into the list from another list

          if ($to.parent().is("div.article-part")) { // is: (CHAPTER) > section
            $(evt.dragged).find("> h4 > a").unwrap().wrap("<h3></h3>")
          } else { // is: (PART) > chapter > section 
            $(evt.dragged).find("> h3 > a").unwrap().wrap("<h4></h4>")
          }
        }

        if ($(evt.related).is(".simple-create-button"))
          return false
      },
      onEnd: (evt) => {
        $(evt.dragged).data("tmp-sortable-switch", false)
      }
    })
    $("*[data-children-type=container]").sortable({
      group: 'container'
    });
  })
})(document, jQuery)
