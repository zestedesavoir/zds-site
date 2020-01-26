/* ===== Zeste de Savoir ====================================================
   Manage modals boxes
   ========================================================================== */

(function($) {
  'use strict'

  /**
   * Create a new Modal
   *
   * @constructor
   * @param {Object} options
   * @param {string} options.title
   * @param {(Node|jQuery)} options.body
   * @param {(Node|jQuery)} options.footer
   * @param {string} [options.titleIcon=""] - Icon to add to the title
   * @param {string} [options.closeText="Annuler"] - The text of the close button
   * @param {(Node|jQuery)} [options.modal] - The modal element to wrap the content
   */
  var Modal = function(options) {
    this.options = $.extend({
      titleIcon: '',
      closeText: 'Annuler'
    }, options)
    if (!Modal._initialized) this.firstRun()
    this.init()
  }

  /**
   * Close the current modal
   *
   * @static
   */
  Modal.closeCurrent = function() {
    Modal.current.modal.removeClass('open')
    Modal.container.removeClass('open')
    $('html').removeClass('dropdown-active')
    Modal.current = null
  }

  /**
   * Open a modal
   *
   * @static
   * @param {string} id - The id of the modal to open
   */
  Modal.openModal = function(id) {
    if (Modal.list[id]) {
      Modal.list[id].open()
    }
  }

  Modal.prototype = {
    /**
     * To be run on first modal creation
     *
     * @access private
     */
    firstRun: function() {
      /**
       * The Node that contains all the modals and the overlay
       * @type {jQuery}
       */
      Modal.container = $('<div>', { class: 'modals-container' })
      /**
       * The Node that wrap all the modals
       * @type {jQuery}
       */
      Modal.wrapper = $('<div>', { class: 'modals-wrapper' })
      /**
       * The overlay
       * @type {jQuery}
       */
      Modal.overlay = $('<div>', { class: 'modals-overlay' })
      Modal.container.append(Modal.wrapper).append(Modal.overlay).appendTo($('body'))
      /**
       * The list of all the modals
       * @type {Modal[]}
       */
      Modal.list = []
      Modal._initialized = true
      Modal.nextId = 0

      Modal.overlay.on('click', Modal.closeCurrent)

      $('body').on('click', '.open-modal', function(e) {
        Modal.openModal($(this).attr('href').substring(1))

        e.preventDefault()
        e.stopPropagation()
      }).on('keydown', function(e) {
        // Escape close modal
        if (Modal.current && e.which === 27) {
          Modal.closeCurrent()
          e.stopPropagation()
        } else if (Modal.current && e.which === 13) {
          if (document.activeElement.tagName !== 'TEXTAREA' || e.ctrlKey) {
            var elem = Modal.current.footer.find('.btn-submit').get(0)
            if (elem) elem.click()
          }
        }
      })
    },

    /**
     * Initialize a Modal
     *
     * @access private
     */
    init: function() {
      /**
       * The modal DOM Node
       * @member {jQuery}
       */
      this.modal = this.options.modal || $('<div>', { class: 'modal modal-flex' })
      /**
       * The ID of the modal
       * @member {string}
       */
      this.id = this.modal.attr('id') || 'noid-' + (Modal.nextId++)
      /**
       * The title of the modal
       * @member {jQuery}
       */
      this.title = $('<div>', {
        class: 'modal-title',
        text: this.options.title
      })

      if (this.options.titleIcon) {
        this.title.addClass(this.options.titleIcon + ' ico-after')
      }

      /**
       * The body of the modal
       * @member {jQuery}
       */
      this.body = $('<div>', {
        class: 'modal-body'
      }).append(this.options.body)

      /**
       * The footer of the modal (contains the buttons)
       * @member {jQuery}
       */
      this.footer = $('<div>', {
        class: 'modal-footer'
      }).append(this.options.footer).append($('<a>', {
        class: 'btn btn-cancel',
        href: '#close-modal',
        text: this.options.closeText,
        click: function(e) {
          Modal.closeCurrent()
          e.preventDefault()
          e.stopPropagation()
        }
      }))

      this.modal.addClass('tab-modalize').append(this.title, this.body, this.footer).appendTo(Modal.wrapper)

      Modal.list[this.id] = this
    },

    /**
     * Open the Modal
     */
    open: function() {
      if (Modal.current) Modal.closeCurrent()
      this.modal.addClass('open')
      Modal.container.addClass('open')

      Modal.current = this

      this.body.find('input:visible, select, textarea').first().focus()
      if (!$('html').hasClass('enable-mobile-menu')) { $('html').addClass('dropdown-active') }
    },

    /**
     * Close the Modal
     */
    close: function() {
      Modal.closeCurrent()
    }
  }

  /**
   * Build the modal from the given elements
   *
   * @param {jQuery} $elems
   */
  function buildModals($elems) {
    $elems.each(function() {
      var $link = $("[href='#" + $(this).attr('id') + "']:first")

      var linkIco = ''
      if ($link.hasClass('ico-after')) {
        linkIco = $link.attr('class').split(' ').concat(['light']).filter(function(c) {
          return ['', 'ico-after', 'open-modal', 'blue'].indexOf(c) === -1 && c.indexOf('btn-') === -1
        }).join(' ')
      }

      // eslint-disable-next-line no-new
      new Modal({
        title: $(this).is('[data-modal-title]') ? $(this).attr('data-modal-title') : $link.text(),
        footer: $(this).find('.btn, [type=submit]').filter(':not(.modal-inner)').detach(),
        body: $(this).children(),
        modal: $(this),
        closeText: $(this).is('[data-modal-close]') ? $(this).attr('data-modal-close') : 'Annuler',
        titleIcon: linkIco
      })
    })
  }

  window.Modal = Modal

  $(document).ready(function() {
    buildModals($('.modal'))
    $('#content').on('DOMNodeInserted', '.modal', function(e) {
      buildModals($(e.target))
    })
  })
})(jQuery)
