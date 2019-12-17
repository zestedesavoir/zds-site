/*
 * Allow the user to compare two commits
 */
(function(document, $){
  "use strict";

  function getFirstLevelSlug(isExtract, $element) {
    if (!isExtract) {
        return undefined;
    }
    console.log($element.attr("data-depth"));
    if (Number.parseInt($element.attr("data-depth"), 10) >= 2) {
        return $element.parents("[data-slug]").parents("[data-slug]").attr("data-slug");
    }
    return undefined;
  }

  function sendMoveAction(evt) {


    // sending
    const $item = $(evt.item);
    const $from = $(evt.from);
    const movingMethod = (($prev) => {
      const path = ((tree) => {
        $item.parents("[data-accept-container]:not([data-pk])").each((n, parent) => {
          tree.push($(parent).attr("data-slug"));
        });
        $item.parents("[data-accept-extracts]:not([data-pk]):not([data-accept-container])").each((n, parent) => {
          tree.push($(parent).attr("data-slug"));
        });
        tree = tree.reverse();
        if (tree.length > 0) {
          tree.push("");
        }
        if (!tree[0]) {
            tree = tree.splice(1);
        }
        return tree.join("/");
      })([]);

      if ($prev[0] && $prev.attr("data-slug")) {
        return "after:" + path + $prev.attr("data-slug");
      } else {
        return "first:" + path;
      }
    })($item.prev());


    const isExtract = ($from.attr("data-accept-extracts")) && $from.attr("data-accept-container") !== "true";

    const pk = $item.parents("[data-pk]").attr("data-pk");
    const slug = $item.attr("data-slug");
    const form = {
      // new 
      "moving_method": movingMethod,
      // old
      "container_slug": $from.attr("data-slug"),
      "first_level_slug":  getFirstLevelSlug(isExtract, $from),
      // current
      "child_slug": slug,
      "pk": pk,
      // csrf
      "csrfmiddlewaretoken": $("input[name=csrfmiddlewaretoken]").val()
    };

    $.post("/contenus/deplacer/", form, () => {
        $(".actions-title li a.simple-move-button").each((i, element) => {
            const $element = $(element);
            const slug = $element.attr("href").substring("#move-".length);
            const method = form["moving_method"].split(":", 2)[0];
            let path = "";
            if (method === "first") {
                path = `${form["moving_method"].split(":", 2)[1]}/${slug}`;
            } else {
                const neighbour = form["moving_method"].split(":", 2)[1];

                path = `${neighbour.substring(0, neighbour.lastIndexOf("/"))}/${slug}`;
            }
            if (path[0] === "/") {
                path = path.substring(1);
            }
            $.get(`/contenus/deplacement/liste/${pk}/`, {"path": path}, (($button) =>(data) => {
                $($button.attr("href") + " select").html(data);
            })($element), "html");
        });
    });

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

  function canDrop($item, $to, $from, $related) {
    // TODO : [BACK] Change slug if we have the same.
    const filter = "[data-slug=" + $item.attr("data-slug") + "]";

    if ($to.children(filter).length >= (1 + $to.is($from))) {
      return false;
    }
    if ($from.is($to) && $related && $related.is("simple-create-button")) {
        return false;
    }
    const $itemContainer = $item.children("[data-accept-container]");
    const haveChildChapter = (!!$itemContainer.children("div.article-part[data-slug]")[0]);

    // move part in part is forbidden
    if (haveChildChapter && $to.parents("[data-accept-container]")[0]) {
      return false;
    }
    return true;
  }

  $(document).ready(function() {
    $("ol[data-accept-extracts]").sortable({
      group: "extract",
      handle: "a",
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-button");
      },
      onMove: (evt) => {
        const $item = $(evt.dragged);
        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!canDrop($item, $to, $from, $(evt.related))) {
          return false;
        }


        if (!$to.is($from)) {
          // Element is dragged into the list from another list
          if ($from.parent().is(".article-containers > .article-part")) { // is: chapter > extract
            $item.find("h4 > a").unwrap().wrap("<h3></h3>");
          } else { // is: part > chapter > extract 
            $item.find("h3 > a").unwrap().wrap("<h4></h4>");
          }
        }
        if ($item.attr("data-type") === "extract") {
            $item().parent().data("data-accept-extracts", "true");
            $item().parent().data("data-accept-container", "false");
        } else {
            $item().parent().data("data-accept-extracts", "false");
            $item().parent().data("data-accept-container", "true");
            $to.children("ol[data-accept-extract=true]").remove();
        }
        if (!$from.children("li") && !($from.children(".article-part"))) {
            $item.parent().data("data-accept-extracts", "true");
            $item.parent().data("data-accept-container", "true");
            $item.parent().prepend("<ol data-accept-extracts=\"true\" style=\"border:1px solid black; width: 50px; height: 20px\"></ol>");
        }
      },
      onEnd: sendMoveAction
    });

    $("*[data-accept-container=true]").sortable({
      group: "container",
      handle: ["h2", "h3 a"],
      filter: function (pointer, dragged) {
        return $(dragged).is(".simple-create-part");
      },
      onMove: (evt) => {
        const $item = $(evt.dragged);
        const $to = $(evt.related).parent();
        const $from = $(evt.dragged).parent();

        if (!canDrop($item, $to, $from, $(evt.related))) {
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
                `<ol class="summary-part" data-accept-extracts="true" data-parent-slug="${$item.attr("data-parent-slug")}">
                  <li class="simple-create-button">
                    <a class="btn btn-grey">Ajouter une section</a>
                  </li>
                </ol>`
              );
            }
          }
        }

        if ($(evt.related).is(".simple-create-part")) {
          let $element = $(evt.related);
          $element.appendTo($element.parent());
        }
      },
      onEnd: sendMoveAction
    });
  });

  $("form.simple-create-button").submit((e) => {
     e.preventDefault();
     $.post($(e.target).attr("action").trim(), {
         "text": "",
         "title": $(e.target).children("input[name=title]").val(),
         "csrfmiddlewaretoken": $(e.target).children("input[name=csrfmiddlewaretoken]").val()
     }, (d) => {
         const $link = $("<a>").attr("href", d.url).text(d.title);
         const newOlElement = $("<li>").attr("data-slug", d.slug).attr("data-depth", 1)
                     .append($("<h4>").append($link));
         const newUlElement = $("<li>").attr("data-slug", d.slug).attr("data-depth", 1)
                     .append($link);
         // in case we are in tutorial summary part
         $(e.target).parent().children("ol.summary-part").append(newOlElement);
         // in case we are on article or chapter summary
         $(e.target).parent().children("ul").append(newUlElement);
         // reset form
         $(e.target).children("input[name=title]").val("");
         const $newEditor = $("#template_new_section").clone();
         $newEditor.insertBefore($("div.simple-create-part"));
         $newEditor.attr("id", "");
         $newEditor.attr("style", "");
         $newEditor.find(".append-slug").each((index, link) => $(link).attr("href", $(link).attr("href") + d.slug));
         $newEditor.find(".view-url").attr("href", d.url).text(d.title);
         $newEditor.find(".edit-url").attr("href", d["edit-url"]);
     }, "json");
  });
})(document, jQuery);
