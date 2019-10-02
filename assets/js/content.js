/*
 * Allow the user to compare two commits
 */
(function(document, $, undefined){
  "use strict";

  function hideMoveButton(evt) {
    /* TODO : REMOVE this and update the selectlist with js */
    /* because the list is not updated */
    $(".simple-move-button").hide();

    /* TODO : REMOVE this and update URL/form of delete and edit button */
    /* because the list is not updated */
    $(evt.item).find(".actions-title").hide();
  }

  function sendMoveAction(evt) {
    hideMoveButton(evt);

    // sending
    const $item = $(evt.item);
    const $to = $(evt.to);
    const $from = $(evt.from);
    const moving_method = (($prev) => {
      const path = ((tree) => {
        $item.parents("[data-children-type]:not([data-pk])").each((n, parent) => {
          tree.push($(parent).attr("data-slug"));
        });
        tree = tree.reverse();
        if (tree.length > 0) {
          tree.push("")
        }
        return tree.join("/");
      })([]);

      if ($prev[0]) {
        return "after:" + path + $prev.attr("data-slug");
      } else {
        return "before:" + path + $item.next().attr("data-slug");
        // TODO : [BACK] Add support of beginning
        // return "beginning:" + path;
      }
    })($item.prev());

    const is_extract = ($from.attr("data-children-type") === "extract")

    const form = {
      // new 
      moving_method: moving_method,
      // old
      container_slug: $from.attr("data-slug"),
      first_level_slug: (is_extract) ? $from.parents("[data-children-type]").attr("data-slug") : undefined,

      child_slug: $item.attr("data-slug"),
      pk: $item.parents("[data-pk]").attr("data-pk"),
      csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
    };

    $.post("/contenus/deplacer/", form);
  }

  function canDrop($item, $to, $from) {
    // TODO : [BACK] Change slug if we have the same.
    const filter = "[data-slug=" + $item.attr("data-slug") + "]";
    if ($to.children(filter).length >= (1 + $to.is($from))) {
      return false;
    }

    // TODO : [BACK] Add "beginning" moving_method
    if (!$to.children(":not(.simple-create-button):not(.simple-create-part)")[0]) {
      return false;
    }

    return true;
  }

  $(document).ready(function() {
    $("ol[data-children-type=extract]").sortable({
      group: "extract",
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
          if ($from.parent().is(".article-containers > .article-part")) { // is: chapter > extract
            $item.find("> h4 > a").unwrap().wrap("<h3></h3>");
          } else { // is: part > chapter > extract 
            $item.find("> h3 > a").unwrap().wrap("<h4></h4>");
          }
        }

        if ($(evt.related).is(".simple-create-button")) {
          return -1;
        }
      },
      onEnd: sendMoveAction
    });

    $("*[data-children-type=container]").sortable({
      group: "container",
      handle: ["h2", "h3 a"],
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-part");
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
          if ($to.is("section")) { // is: chapter > extract
            $item.find("> h3 > a").unwrap().wrap("<h2></h2>");
            $item.find("ol h4 > a").unwrap().wrap("<h3></h3>");
          } else { // is: part > chapter > extract 
            $item.find("> h2 > a").unwrap().wrap("<h3></h3>");
            $item.find("ol h3 > a").unwrap().wrap("<h4></h4>");
          }
        }

        if ($(evt.related).is(".simple-create-part")) {
          return -1;
        }
      },
      onEnd: sendMoveAction
    });
  })
})(document, jQuery);
