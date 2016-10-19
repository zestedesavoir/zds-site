/* ===== Zeste de Savoir ====================================================
   jQuery :tabbable and :focusable selectors plugin
   ========================================================================== */

(function($){
  "use strict";

  $.extend($.expr[ ":" ], {
    data: $.expr.createPseudo ?
      $.expr.createPseudo(function(dataName){
        return function(elem){
          return !!$.data(elem, dataName);
        };
      }) :
      // support: jQuery <1.8
      function(elem, i, match){
        return !!$.data(elem, match[ 3 ]);
      },

    focusable: function(element){
      return focusable(element, !isNaN($.attr(element, "tabindex")));
    },

    tabbable: function(element){
      var tabIndex = $.attr(element, "tabindex"),
        isTabIndexNaN = isNaN(tabIndex);
      return ( isTabIndexNaN || tabIndex >= 0 ) && focusable(element, !isTabIndexNaN);
    }
  });

  /**
   * focussable function, taken from jQuery UI Core
   * @param element
   * @returns {*}
   */
  function focusable(element){
    var map, mapName, img,
      nodeName = element.nodeName.toLowerCase(),
      isTabIndexNotNaN = !isNaN($.attr(element, "tabindex"));
    if("area" === nodeName){
      map = element.parentNode;
      mapName = map.name;
      if(!element.href || !mapName || map.nodeName.toLowerCase() !== "map"){
        return false;
      }
      img = $("img[usemap='#" + mapName + "']")[0];
      return !!img && visible(img);
    }
    return ( /input|select|textarea|button|object/.test(nodeName) ?
      !element.disabled :
      "a" === nodeName ?
        element.href || isTabIndexNotNaN :
        isTabIndexNotNaN) &&
      // the element and all of its ancestors must be visible
      visible(element);

    function visible(element){
      return $.expr.filters.visible(element) && !$(element).parents().addBack().filter(function(){
        return $.css(this, "visibility") === "hidden";
      }).length;
    }
  }
})(jQuery);
