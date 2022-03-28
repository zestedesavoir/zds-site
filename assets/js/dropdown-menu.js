/* ===== Zeste de Savoir ====================================================
   Dropdown menu open/close
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  let mouseDown = false
  let shiftHeld = false

  function hoveringModeEnabled() {
    return $('.header-menu').is('[data-hovering-mode]')
  }

  const handlers = $('.header-dropdown')
    .map(function(_, dropdown) {
      return setupDropdown($(dropdown))
    })

  function closeAll() {
    handlers.each(function(_, handler) {
      handler.close()
    })
  }

  function isDropdownContainer(element) {
    for (let i = 0; i < handlers.length; i++) {
      if (handlers[i].$container[0] === element) {
        return true
      }
    }
    return false
  }

  function areSomeDropdownsFocused() {
    return $(document.activeElement)
      .parents()
      .filter(function(_, element) {
        return isDropdownContainer(element)
      })
      .length
  }

  $('body')
    .on('click', closeAll)
    .on('keydown', function(event) {
      if (event.key === 'Tab') {
        setTimeout(function() {
          if (!areSomeDropdownsFocused()) {
            closeAll()
          }
        }, 5)
      }
    })

  $(document).on('keydown keyup', function(event) {
    shiftHeld = event.shiftKey
  })

  function getTabIndex(element) {
    const tabbables = $(':tabbable')
    for (let i = 0; i < tabbables.length; i++) {
      if (tabbables[i] === element) {
        return i
      }
    }
    return -1
  }

  function moveFocus(element, container, direction) {
    const index = getTabIndex(element)
    if (index === -1) {
      return
    }

    const tabbables = $(':tabbable')
    for (let i = index + direction; i < tabbables.length; i += direction) {
      if (!container.contains(tabbables[i])) {
        closeAll()
        tabbables[i].focus()
        return
      }
    }
  }



  // Returns a dropdown handler
  function setupDropdown($dropdown) {
    const $container = $dropdown.parent()
    const $toggleLink = $container.find('> a')
    let closingTimer

    $dropdown.on('click', function(event) {
      // Don't close
      event.stopPropagation()
    })

    function open() {
      cancelClosingTimer()

      // Close any other dropdown
      $('body').trigger('click')

      $toggleLink.addClass('active')
      $dropdown.find('.dropdown-list').scrollTop(0)
    }

    function cancelClosingTimer() {
      if (closingTimer) {
        clearTimeout(closingTimer)
        closingTimer = null
      }
    }

    function close() {
      cancelClosingTimer()
      $toggleLink.removeClass('active')
    }

    function closeLater() {
      if (closingTimer) {
        return
      }
      closingTimer = setTimeout(close, 200)
    }

    $container
      .on('mouseenter', function() {
        if (hoveringModeEnabled()) {
          open()
        }
      })

      .on('mouseleave', function() {
        if (hoveringModeEnabled()) {
          closeLater()
        }
      })

      .on('keydown', function(event) {
        if (event.key === 'ArrowRight') {
          event.preventDefault()
          moveFocus($toggleLink[0], $container[0], 1)
        }

        if (event.key === 'ArrowLeft') {
          event.preventDefault()
          moveFocus($toggleLink[0], $container[0], -1)
        }
      })

    $toggleLink

    // Mutates global state but there is only one mouse
      .on('mousedown', function() {
        mouseDown = true
      })
      .on('mouseup', function() {
        mouseDown = false
      })

      .on('click', function(event) {
        if (hoveringModeEnabled()) {
          return
        }

        event.preventDefault()
        event.stopPropagation()

        if ($toggleLink.hasClass('active')) {
          close()
        } else {
          open()
        }
      })

      .on('focus', function(event) {
        event.preventDefault()

        if (mouseDown || $toggleLink.hasClass('active')) {
          return
        }

        open()

        if (!shiftHeld) {
          $dropdown.find(':tabbable:first').focus()
        }
      })

    return {
      open: open,
      close: close,
      $container: $container
    }
  }
})(jQuery)
