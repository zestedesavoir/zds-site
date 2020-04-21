(function($) {
  'use strict'

  /**
   * Create a tooltip for a target
   *
   * @param {Object} options
   * @param {DOMNode} options.target - Tooltip target
   * @param {string} options.content - Tooltip content
   * @class
   */
  var Tooltip = function(options) {
    this.options = $.extend({ target: null, content: null }, options)
    if (!Tooltip._initialized) {
      this.firstRun()
    }

    this.init()
  }

  Tooltip.prototype = {
    /**
     * Creates the containers for the all the tooltips
     *
     * @access private
     */
    firstRun: function() {
      Tooltip.container = $('<div>', { class: 'tooltips-container' })
      Tooltip.list = []
      Tooltip.nextID = 0

      $('body').append(Tooltip.container)
      Tooltip._initialized = true
    },

    /**
     * Initialize a tooltip
     *
     * @access private
     */
    init: function() {
      /**
       * @member {jQuery} - The tooltip wrapper
       */
      this.wrapper = $('<div>', { class: 'tooltip-wrapper' })

      /**
       * @member {jQuery} - The tooltip itself
       */
      this.elem = $('<div>', {
        class: 'tooltip',
        id: 'tooltip-' + Tooltip.nextID,
        role: 'tooltip',
        'aria-hidden': true
      })

      /**
       * @member {jQuery} - The target element
       */
      this.target = $(this.options.target)

      this.hasContent = false
      this.setOrientation('top')
      this.setContent(this.options.content)
      this.hide()

      /**
       * Builds a DOM like:
       *  <div class="tooltips-container">
       *    <div class="tooltip-wrapper {{ orientation }}">
       *      <div class="tooltip" role="tooltip" id="tooltip-N" aria-hidden="true">{{ content }}</div>
       *    </div>
       *    <div class="tooltip-wrapper">...</div>
       *    ...
       *  </div>
       */
      this.wrapper.append(this.elem).appendTo(Tooltip.container)

      this.target.on('mouseover', this.mouseover.bind(this))
      this.wrapper.on('mouseover', this.mouseover.bind(this))
      this.target.on('mouseout', this.mouseout.bind(this))
      this.wrapper.on('mouseout', this.mouseout.bind(this))

      this.target.attr('aria-describedby', 'tooltip-' + Tooltip.nextID)

      this.hideTimeout = null

      this.mouseon = false

      Tooltip.list.push(this)
      Tooltip.nextID++
    },

    /**
     * Show the tooltip on mouseover
     *
     * @access private
     */
    mouseover: function() {
      if (!this.mouseon) this.show()
      this.mouseon = true
      clearTimeout(this.hideTimeout)
    },

    /**
     * Hide the tooltip on mouseout after a short delay
     *
     * @access private
     */
    mouseout: function() {
      this.hideTimeout = setTimeout(this.hide.bind(this), 50)
      this.mouseon = false
    },

    /**
     * Set the content of the tooltip
     * WARNING: passing HTMLElement(s) will insert them directly into the DOM
     * without sanitization, beware of XSS. As they are inserted as text,
     * passing strings is always safe.
     *
     * @param {string|HTMLElement|Array<string|HTMLElement>} content - content of the tooltip
     */
    setContent: function(content) {
      if (!Array.isArray(content)) content = [content]
      this.elem.empty()
      this.hasContent = false

      for (var i = 0; i < content.length; i++) {
        if (!content[i]) continue
        this.hasContent = true

        if (typeof content[i] === 'string') {
          this.elem.append(document.createTextNode($.trim(content[i])))
        } else {
          this.elem.append(content[i])
        }
      }

      if (!this.hasContent) this.hide()
      else if (this.mouseon) this.show() // Recalculate tooltip position
    },

    /**
     * Hide the tooltip
     */
    hide: function() {
      this.wrapper.hide()
      this.elem.attr('aria-hidden', true)
    },

    /**
     * Show the tooltip if the content is not empty
     */
    show: function() {
      if (this.hasContent) {
        this.wrapper.show()
        this.elem.attr('aria-hidden', false)
        this.recalc() // Need to recalc on this tick & on next
        setTimeout(this.recalc.bind(this))
      }
    },

    /**
     * Guess the tooltip position depending on the tooltip's size and the viewport scroll
     *
     * @access private
     */
    guessOrientation: function() {
      if (this.target.offset().top - $(window).scrollTop() < this.wrapper.height()) {
        this.setOrientation('bottom')
      } else {
        this.setOrientation('top')
      }
    },

    /**
     * Recalculate the position of the tooltip
     *
     * @access private
     */
    recalc: function() {
      var css = {
        top: null,
        bottom: null,
        left: this.target.offset().left + (this.target.outerWidth() / 2) - (this.wrapper.width() / 2)
      }

      this.guessOrientation()
      if (this.orientation === 'top') {
        css.top = this.target.offset().top - this.wrapper.outerHeight()
      } else if (this.orientation === 'bottom') {
        css.top = this.target.offset().top + this.target.outerHeight()
      } else {
        css.bottom = this.target.offset().top - this.wrapper.outerHeight() + 8
      }

      this.wrapper.css(css)
    },

    /**
     * Set the orientation of the tooltip
     *
     * @access private
     */
    setOrientation: function(orientation) {
      if ((orientation !== 'top' && orientation !== 'bottom') || orientation === this.orientation) return

      this.wrapper.addClass(orientation)
      this.wrapper.removeClass(this.orientation)
      this.orientation = orientation
    }
  }

  /**
   * Create a tooltip on a jQuery element
   * Set the content of a tooltip if the tooltip already exists
   *
   * @example
   * $(".topic-message .message-karma .upvote").tooltip("42 votes");
   * @param {string} content
   * @return {Tooltip}
   */
  $.fn.tooltip = function(content) {
    var tooltip = $(this).data('tooltip')
    if (tooltip) {
      if (content) tooltip.setContent(content)
    } else {
      tooltip = new Tooltip({ target: this, content: content })
      $(this).data('tooltip', tooltip)
    }

    return tooltip
  }
})(jQuery)
