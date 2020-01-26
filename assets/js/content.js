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
      } else if ($item.next()[0] && !$item.next().is(".simple-create-button, .simple-create-part")) {
        return "before:" + path + $item.next().attr("data-slug");
      } else {
        return "first:" + path;
      }
    })($item.prev());

    // const isExtract = ($from.attr("data-children-type") === "extract");
    const isPart = (!!$item.children("[data-children-type=container]")[0]);

    const pk = $item.parents("[data-pk]").attr("data-pk");
    const slug = $item.attr("data-slug");

    const form = {
      // new 
      "moving_method": movingMethod,
      // old
      "container_slug": $from.attr("data-slug"),
      "first_level_slug": ($from.parents("[data-children-type]").length > 1) ? $from.parents("[data-children-type]").attr("data-slug") : '',
      // current
      "child_slug": slug,
      "pk": pk,
      // csrf
      "csrfmiddlewaretoken": $("input[name=csrfmiddlewaretoken]").val()
    };

    $.post("/contenus/deplacer/", form);

    if ($item.is("div") && $item.parent().is("ol, ul")) {
      const newWrapper = $("<li></li>").attr({
        "class": $item.attr("class"),
        "data-slug": $item.attr("data-slug")
      })
      $item.wrap(newWrapper).children().unwrap();
    } else if ($item.is("li") && $item.parent().is(":not(ol, ul)")) {
      const newWrapper = $("<div></div>").attr({
        "class": $item.attr("class"),
        "data-slug": $item.attr("data-slug")
      })
      $item.wrap(newWrapper).children().unwrap();
    }

    // modifie les URLs
    const path = ((tree) => {
      $item.parents("[data-children-type]").each((n, parent) => {
        tree.push($(parent).attr("data-slug"));
      });
      tree = tree.reverse();
      return tree.join("/");
    })([]);

    $item.find("> .actions-title a.edit").attr("href", `/contenus/editer-conteneur/${pk}/${path}/${slug}/`);
    $("form#delete-" + slug).attr("action", `/contenus/supprimer/${pk}/${path}/${slug}/`);
    $item.find("> *:first-child > a, [data-children-type] > [data-slug] a").each(function () {
      const $parents = $(this).parents("[data-slug]");
      const type = $(this).parents("[data-children-type]").attr("data-children-type");
      const mySlug = $parents.attr("data-slug");

      let fullpath = (slug !== mySlug) ? `${path}/${slug}` : path; 

      if (type === "extract") {
        fullpath += (isPart) ? "/" + $parents.eq(1).attr("data-slug") : "";
        $(this).attr("href", `/contenus/${pk}/${fullpath}/#${$parents.eq(0).index()+1}-${mySlug}`);
      } else if (type === "container") {
        $(this).attr("href", `/contenus/${pk}/${fullpath}/${mySlug}`);
      } else {
        console.warn("type inattendu.", type);
      }
    });
    $item.find(".simple-create-button")
      .attr("href", `/contenus/nouvelle-section/${pk}/${path}/${slug}/`);
  }

  function canDrop($item, $to, $from) {
    // TODO : [BACK] Change slug if we have the same.
    const filter = "[data-slug=" + $item.attr("data-slug") + "]";
    if ($to.children(filter).length >= (1 + $to.is($from))) {
      return false;
    }
    const $itemContainer = $item.children("[data-children-type=container]");
    const haveChildChapter = (!!$itemContainer.children(".article-part[data-slug]")[0]);
    const childrenType = $item.parents("[data-children-type]").attr("data-children-type");

    // move part in part is forbidden
    if (haveChildChapter && $to.parents("[data-children-type=container]")[0]) {
      return false;
    }

    // move container in extract is forbidden
    if (childrenType === "container" && $to.attr("data-children-type") === "extract") {
      return false;
    }

    // move extract in tuto (root) or chapter in (part) is forbidden
    if (childrenType === "extract" && $to.children(".article-part[data-slug]")[0]) {
      return false;
    }

    return true;
  }

  $(document).ready(function() {
    $("section.article-content.parts")
      .attr("data-children-type", "container");

    $("section.article-content.parts .article-containers").each(function() {
      const hasChildren = $(this).children(".article-part[data-slug]")[0];
      $(this).attr("data-children-type", hasChildren ? "container" : "both");
    });

    const filter = function () {
      // forbid drop into button
      return !($(this).parents(".simple-create-button, .simple-create-part")[0]);
    };

    $("section.article-content.parts ol.summary-part").filter(filter)
      .attr("data-children-type", "extract");

    const makeSortable = ($elements) => $elements.sortable({
      group: "element",
      handle: ["h2", "h3 a", "h4 a"],
      filter: function(pointer, dragged) {
        // forbid button dragging
        return $(dragged).is(".simple-create-button, .simple-create-part");
      },
      onStart: function (evt) {
        console.log(evt);
        console.log($(evt.from).is("[data-children-type=extract]"));
        if ($(evt.from).is("[data-children-type=extract]")) {
          $("*[data-children-type=both]").each(function() {
            $(this).html(`<li class="simple-create-button">
                            <a class="btn btn-grey" href="#">Ajouter une section</a>
                          </li>`);
            $(this).attr("class", "summary-part both");
            $(this).attr("data-children-type", "extract");
            //makeSortable($(this).find("> *[data-children-type]"));
          });
        } else {
          $("*[data-children-type=both]").each(function() {
            $(this).html(`<li class="article-part simple-create-part">
                            <h3>
                              <a class="force-blue" href=#>Ajouter un chapitre</a>
                            </h3>
                            <ol class="summary-part">
                              <li><h4><a class="disabled">Section A</a></h4></li>
                              <li><h4><a class="disabled">Section B</a></h4></li>
                            </ol>
                          </li>`);
            $(this).attr("class", "article-containers both");
            $(this).attr("data-children-type", "container");
            makeSortable($(this));
          });
        }
      },
      onMove: function(evt) {
        const $item = $(evt.dragged);
        const $to = $(evt.related).parent();
        const $from = $item.parent();

        const childrenType = $item.parents("[data-children-type]").attr("data-children-type");

        if (!canDrop($item, $to, $from)) {
          return false;
        }

        // Parent changed
        if (!$to.is($from)) {
          // Parent is: Chapter
          if (childrenType === "extract") {
            const path_chap = ($obj) => $obj.is(".article-containers > .article-part");
            const path_partchap = ($obj) => $obj.is(".article-content > .article-part");
            // 1) path_chap: from: [chapter] > extract
            // 2) path_partchap: from: part > [chapter] > extract 

            // Element is dragged into the list from another list (with different level)
            if (path_chap($from.parent()) && path_partchap($to)) {
              console.log("B2");
              $item.find("> h4 > a").unwrap().wrap("<h3></h3>");
            } else if (path_partchap($from.parent()) && path_chap($to)) { 
              console.log("B2", $from.parent(), $to);
              $item.find("> h3 > a").unwrap().wrap("<h4></h4>");
            }
            console.log("end")
          // Parent is: Tuto (root) or Part
          } else if (childrenType === "container") {
            // Element is dragged into the list from another list
            if ($from.is(".article-containers")) { // to: [chapter] > extract
              console.log("A1");
              $item.find("> h3 > a").unwrap().wrap("<h2></h2>");
              $item.find("> ol h4 > a").unwrap().wrap("<h3></h3>");

              if ($item.find(".simple-create-part")[0]) {
                $item.children(".article-containers").show();
                $item.children("ol.summary-part").hide();
              }
            } else if ($from.is(".article-content")) { // to: part > [chapter] > extract
              console.log("A2");
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
        }

        if ($(evt.related).is(".simple-create-button") || $(evt.related).is(".simple-create-part")) {
          return -1;
        }
      },
      onEnd: sendMoveAction
    });

    makeSortable($("*[data-children-type]"));
  });
})(document, jQuery);
