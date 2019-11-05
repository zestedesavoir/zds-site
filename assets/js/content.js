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

  function sendMoveAction(evt) {
    hideMoveButton();

    // sending
    const $item = $(evt.item);
    const $from = $(evt.from);
    const movingMethod = (($prev) => {
      const path = ((tree) => {
        $item.parents("[data-children-type]:not([data-pk])").each((n, parent) => {
          tree.push($(parent).attr("data-slug"));
        });
        tree = tree.reverse();
        if (tree.length > 0) {
          tree.push("");
        }
        return tree.join("/");
      })([]);

      if ($prev[0]) {
        return "after:" + path + $prev.attr("data-slug");
      } else {
        return "first:" + path;
      }
    })($item.prev());

    const isExtract = ($from.attr("data-children-type") === "extract");

    const pk = $item.parents("[data-pk]").attr("data-pk");
    const slug = $item.attr("data-slug");

    const form = {
      // new 
      "moving_method": movingMethod,
      // old
      "container_slug": $from.attr("data-slug"),
      "first_level_slug": (isExtract) ? $from.parents("[data-children-type]").attr("data-slug") : undefined,
      // current
      "child_slug": slug,
      "pk": pk,
      // csrf
      "csrfmiddlewaretoken": $("input[name=csrfmiddlewaretoken]").val()
    };

    $.post("/contenus/deplacer/", form);

    // modifie les URLs
    const path = ((tree) => {
      $item.parents("[data-children-type]").each((n, parent) => {
        tree.push($(parent).attr("data-slug"));
      });
      tree = tree.reverse();
      tree.push(slug);
      return tree.join("/");
    })([]);

    $item.find("> .actions-title a.edit").attr("href", `/contenus/editer-conteneur/${pk}/${path}/`);
    $("form#delete-" + slug).attr("action", `/contenus/supprimer/${pk}/${path}/`);
    $item.find("[data-children-type] > [data-slug] a").each(function () {
      const $parent = $(this).parents("[data-slug]").eq(0);
      const mySlug = $parent.attr("data-slug");
      if (slug !== $(this).attr("data-slug")) {
        $(this).attr("href", `/contenus/${pk}/${path}/#${$parent.index()+1}-${mySlug}`);
      } else {
        $(this).attr("href", `/contenus/${pk}/${path}/`);
      }
    });
    $item.find(".simple-create-button")
      .attr("href", `/contenus/nouvelle-section/${pk}/${path}/`);
  }

  function canDrop($item, $to, $from) {
    // TODO : [BACK] Change slug if we have the same.
    const filter = "[data-slug=" + $item.attr("data-slug") + "]";
    if ($to.children(filter).length >= (1 + $to.is($from))) {
      return false;
    }
    const $itemContainer = $item.children("[data-children-type=container]");
    const haveChildChapter = (!!$itemContainer.children("div.article-part[data-slug]")[0]);

    // move part in part is forbidden
    if (haveChildChapter && $to.parents("[data-children-type=container]")[0]) {
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
          return false;
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
            $item.find("> ol h4 > a").unwrap().wrap("<h3></h3>");

            if ($item.find(".simple-create-part")[0]) {
              $item.children(".article-containers").show();
              $item.children("ol.summary-part").hide();
            }
          } else { // is: part > chapter > extract 
            $item.find("> h2 > a").unwrap().wrap("<h3></h3>");
            $item.find("> ol h3 > a").unwrap().wrap("<h4></h4>");

            if ($item.find(".simple-create-part")[0]) {
              $item.children(".article-containers").hide();
              $item.append(
                `<ol class="summary-part" data-children-type="extract">
                  <li class="simple-create-button">
                    <a class="btn btn-grey">Ajouter une section</a>
                  </li>
                </ol>`
              );
            }
          }
        }

        if ($(evt.related).is(".simple-create-part")) {
          return false;
        }
      },
      onEnd: sendMoveAction
    });
  });
})(document, jQuery);
