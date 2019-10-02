/*
 * Allow the user to compare two commits
 */
(function(document, $, undefined){
  "use strict";

  function hideMoveButton() {
    /* TODO : REMOVE this and update the selectlist with js */
    /* because the list is not updated */
    $(".simple-move-button").hide();
  }

  function canDrop($item, $to, $from) {
    // TODO : [BACK] Change slug if we have the same.
    const filter = "[data-slug=" + $item.attr("data-slug") + "]";
    if ($to.children(filter).length >= (1 + $to.is($from))) {
      console.log("ooo")
      return false;
    }

    // TODO : [BACK] Add "beginning" moving_method
    if (!$to.children(":not(.simple-create-button):not(.simple-create-part)")[0]) {
      return false;
    }

    return true;
  }

  $(document).ready(function() {
    $("ol[data-children-type=section]").sortable({
      group: "section",
      handle: "a",
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-button");
      },
      onMove: (evt) => {
        const $item = $(evt.dragged);
        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!canDrop($item, $to, $from)) {
          return false;
        }

        if (!$to.is($from)) {
          // Element is dragged into the list from another list
          if ($from.parent().is(".article-containers > .article-part")) { // is: chapter > section
            $item.find("> h4 > a").unwrap().wrap("<h3></h3>");
          } else { // is: part > chapter > section 
            $item.find("> h3 > a").unwrap().wrap("<h4></h4>");
          }
        }

        if ($(evt.related).is(".simple-create-button")) {
          return -1;
        }
      },
      onEnd: hideMoveButton
    })
    $("*[data-children-type=container]").sortable({
      group: "container",
      handle: ["h2", "h3 a"],
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-part");
      },
      onMove: (evt) => {
        if ($(evt.related).is(".simple-create-part")) {
          return false;
        }

        const $item = $(evt.dragged);
        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!canDrop($item, $to, $from)) {
          return false;
        }

        if (!$to.is($from)) {
          // Element is dragged into the list from another list
          if ($to.is("section")) { // is: chapter > section
            $item.find("> h3 > a").unwrap().wrap("<h2></h2>");
            $item.find("ol h4 > a").unwrap().wrap("<h3></h3>");
          } else { // is: part > chapter > section 
            $item.find("> h2 > a").unwrap().wrap("<h3></h3>");
            $item.find("ol h3 > a").unwrap().wrap("<h4></h4>");
          }
        }
      },
      onEnd: hideMoveButton
    });
  })
})(document, jQuery);
