/* ===== Zeste de Savoir ====================================================
   jQuery :tabbable and :focusable selectors plugin
   ========================================================================== */

(function($) {
  'use strict'

  $.extend($.expr[':'], {
    data: $.expr.createPseudo
      ? $.expr.createPseudo(function(dataName) {
        return function(elem) {
          return !!$.data(elem, dataName)
        }
      })
      // support: jQuery <1.8
      : function(elem, i, match) {
        return !!$.data(elem, match[3])
      },

    focusable: function(element) {
      return focusable(element, !isNaN($.attr(element, 'tabindex')))
    },

    tabbable: function(element) {
      const tabIndex = $.attr(element, 'tabindex')
      const isTabIndexNaN = isNaN(tabIndex)
      return (isTabIndexNaN || tabIndex >= 0) && focusable(element, !isTabIndexNaN)
    }
  })

  /**
   * focussable function, taken from jQuery UI Core
   * @param element
   * @returns {*}
   */
  function focusable(element) {
    let map; let mapName; let img
    const nodeName = element.nodeName.toLowerCase()
    const isTabIndexNotNaN = !isNaN($.attr(element, 'tabindex'))
    if (nodeName === 'area') {
      map = element.parentNode
      mapName = map.name
      if (!element.href || !mapName || map.nodeName.toLowerCase() !== 'map') {
        return false
      }
      img = $("img[usemap='#" + mapName + "']")[0]
      return !!img && visible(img)
    }
    return (/input|select|textarea|button|object/.test(nodeName)
      ? !element.disabled
      : nodeName === 'a'
        ? element.href || isTabIndexNotNaN
        : isTabIndexNotNaN) &&
      // the element and all of its ancestors must be visible
      visible(element)

    function visible(element) {
      return $.expr.filters.visible(element) && !$(element).parents().addBack().filter(function() {
        return $.css(this, 'visibility') === 'hidden'
      }).length
    }
  }
})(jQuery)
