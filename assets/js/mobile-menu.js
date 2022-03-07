/* ===== Zeste de Savoir ====================================================
   Mobile sidebar menu, swipe open/close
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($) {
  'use strict'

  /**
   * Add class for mobile navigator does not support fixed position
   */
  const navU = navigator.userAgent

  // Android Mobile
  const isAndroidMobile = navU.indexOf('Android') > -1 && navU.indexOf('Mozilla/5.0') > -1 && navU.indexOf('AppleWebKit') > -1

  // Android Browser (not Chrome)
  const regExAppleWebKit = /AppleWebKit\/([\d.]+)/
  const resultAppleWebKitRegEx = regExAppleWebKit.exec(navU)
  const appleWebKitVersion = (resultAppleWebKitRegEx === null ? null : parseFloat(regExAppleWebKit.exec(navU)[1]))
  const disableMobileMenu = isAndroidMobile && appleWebKitVersion !== null && appleWebKitVersion < 537

  if (disableMobileMenu) { $('html').removeClass('enable-mobile-menu') }



  /**
   * Get prefix to support CSS transform
   */
  let transform = ''
  const prefixedPropertyNames = ['transform', 'msTransform', 'MozTransform', 'WebkitTransform', 'OTransform']
  const prefixes = ['', '-ms-', '-moz-', '-webkit-', '-o-']
  const tempDiv = document.createElement('div')
  for (let i = 0; i < prefixedPropertyNames.length; ++i) {
    if (typeof tempDiv.style[prefixedPropertyNames[i]] !== 'undefined') {
      transform = prefixes[i]
      break
    }
  }
  transform = transform + 'transform'



  /**
   * Manage mobile sidebar on resize
   */
  $(window).on('resize', function() {
    if (parseInt($('html').css('width')) < 1024 && !disableMobileMenu) {
      $('.page-container').css('width', $('html').css('width'))

      if (!$('#mobile-menu').hasClass('initialized')) {
        $('#mobile-menu').addClass('initialized')


        /**
         * Manage menu button
         */
        $('.mobile-menu-btn').on('click', function(e) {
          if (!$('html').hasClass('show-mobile-menu')) {
            toggleMobileMenu(true)

            e.preventDefault()
            e.stopPropagation()
          }
        })


        /**
         * Build sidebar menu from page
         */

        appendToSidebar($('#search'), true)

        const $myaccount = appendToSidebar($('#my-account'), true)
        $myaccount.addClass('mobile-menu-link mobile-menu-bloc')

        appendToSidebar($('.header-menu'))

        $('.page-container .mobile-menu-bloc .mobile-menu-bloc').each(function() {
          appendToSidebar($(this))
        })
        $('.page-container .mobile-menu-bloc:not(.my-account-dropdown)').each(function() {
          appendToSidebar($(this))
        })

        appendToSidebar($('.my-account-dropdown'))
      }


      /**
       * Manage touch events for mobile sidebar
       */
      if (!$('#mobile-menu').hasClass('initialized-events')) {
        let beginTouchDown = 0
        const borderWidth = 50
        let swipping = false

        $('body')
          .on('touchstart', function(e) {
            beginTouchDown = parseInt(e.originalEvent.touches[0].pageX, 10) - $('.page-container').offset().left
          })

        $('.page-container')
          .on('touchmove', function(e) {
            if (swipping || parseInt(e.originalEvent.touches[0].pageX, 10) - $(this).offset().left < borderWidth) {
              e.preventDefault()
              $('body:not(.swipping)').addClass('swipping')

              swipping = true

              let toMove = parseInt(e.originalEvent.touches[0].pageX, 10) - beginTouchDown
              toMove = (toMove * 100) / parseInt($('html').width())

              if (toMove > 0 && toMove < 90) {
                const props = {}
                props[transform] = 'translate3d(' + toMove + '%, 0, 0)'
                $(this).css(props)

                toMove = ((toMove * 20) / 90) - 20
                props[transform] = 'translate3d(' + toMove + '%, 0, 0)'
                $('#mobile-menu').css(props)
              }
            }
          })
          .on('touchend touchleave touchcancel', function() {
            if (swipping) {
              const offset = parseInt($(this).offset().left)
              const width = parseInt($('html').width())
              const visible = (offset > width / 3 && !$('html').hasClass('show-mobile-menu')) || (offset > width - width / 3 && $('html').hasClass('show-mobile-menu'))
              toggleMobileMenu(visible)

              swipping = false
              $('body').removeClass('swipping')

              const props = {}
              props[transform] = ''
              $('.page-container, #mobile-menu').css(props)
            }
          })


        $('.page-container').on('click', function(e) {
          if ($('html').hasClass('show-mobile-menu')) {
            toggleMobileMenu(false)

            e.preventDefault()
            e.stopPropagation()
          }
        })


        $('#mobile-menu').addClass('initialized-events')
      }
    } else {
      $('html').removeClass('show-mobile-menu')
      $('#mobile-menu').removeClass('initialized-events')
      $('.page-container').removeAttr('style')
      $('.page-container').off('click touchstart touchmove touchend')
    }
  })
  $(window).trigger('resize')



  function appendToSidebar($elem, onlyCloneThisElement) {
    if ($elem.hasClass('mobile-menu-imported')) { return false }

    if (onlyCloneThisElement) {
      $elem.addClass('mobile-menu-imported')
      $elem = $elem.clone().removeAttr('id').appendTo('#mobile-menu')
      return $elem
    }

    const $div = $('<div/>')
    $div.addClass('mobile-menu-bloc')
    $div.attr('data-title', $elem.attr('data-title'))

    if ($elem.hasClass('mobile-show-ico')) { $div.addClass('mobile-show-ico') }

    const addAllLinks = $elem.hasClass('mobile-all-links')

    let $links = $elem.find((addAllLinks) ? 'a, button, span.disabled' : '.mobile-menu-link')

    if (addAllLinks) { $links = $links.not('.action-hover') }

    $links.each(function() {
      if ($(this).parents('.mobile-menu-imported, .modal').length === 0) {
        const $elem = $(this).clone().addClass('light')
        let formId

        if ($(this).is('button')) {
          const $form = $(this).parents('form:first')
          if (!$form.attr('id')) {
            formId = 'form' + $('.identified-form').length
            $form.attr('id', formId).addClass('identified-form')
          } else {
            formId = $form.attr('id')
          }
          $elem.attr('form', formId)
        }

        $div.append($elem)
      }
    })

    if (addAllLinks) { $div.find('a, button, span.disabled').addClass('mobile-menu-link') }

    $elem.addClass('mobile-menu-imported')

    $div.appendTo($('#mobile-menu'))

    return $div
  }





  /**
   * Toggle sidebar for mobiles
   */
  function toggleMobileMenu(visible) {
    let scrollTop
    if (visible === null) { visible = !$('html').hasClass('show-mobile-menu') }

    $('body').removeClass('swipping')

    const viewportmeta = document.querySelector('meta[name="viewport"]')

    if (visible) {
      if (!$('html').hasClass('show-mobile-menu')) {
        scrollTop = $(document).scrollTop()
        $('.page-container').css({
          'margin-top': '-' + scrollTop + 'px',
          'padding-bottom': scrollTop + 'px'
        })
        $('html').addClass('show-mobile-menu')

        viewportmeta.content = 'width=device-width, minimum-scale=1.0, maximum-scale=1.0, initial-scale=1.0'
      }

      // Manage back button to close sidebar
      /*
            if(history && history.pushState){
                history.pushState(null, document.title, this.href);

                $(window).off("popstate").one("popstate", function(e){
                    if($("html").hasClass("show-mobile-menu"))
                        toggleMobileMenu(false);
                    else
                        window.history.back();
                });
            }
            */
    } else {
      $('html').removeClass('show-mobile-menu')

      // Reset CSS modifications for restore scroll
      scrollTop = parseInt($('.page-container').css('padding-bottom'))
      $('.page-container').css({
        'margin-top': '',
        'padding-bottom': ''
      })
      if (scrollTop > 0) { $(document).scrollTop(scrollTop) }

      // Stop swipping
      $('body').removeClass('swipping')

      setTimeout(function() {
        // Reinit mobile menu at top
        $('#mobile-menu').scrollTop(0)

        // Restore zoom
        viewportmeta.content = 'width=device-width, minimum-scale=1.0, initial-scale=1.0'

        // Bugfix <html> element
        $('html').css({
          position: 'absolute',
          left: '0'
        })
        setTimeout(function() {
          $('html').removeAttr('style')
        }, 500)
      }, 200)
    }
  }




  /**
   * Manage actions buttons, move them at the top af core of page
   */
  $(window).on('resize', function() {
    if (parseInt($('html').css('width')) < 960 && !disableMobileMenu) {
      const $newBtns = $('.sidebar .new-btn:not(.mobile-btn-imported)')
      if ($newBtns.length > 0) {
        let $prevElem = $('#content')
          .find('> .content-wrapper, > .full-content-wrapper, > .content-col-2')
          .first()
          .find('h1, h2')
          .first()
        if ($prevElem.next('.license').length > 0) { $prevElem = $prevElem.next('.license') }
        if ($prevElem.next('.subtitle').length > 0) { $prevElem = $prevElem.next('.subtitle') }
        if ($prevElem.next('.taglist').length > 0) { $prevElem = $prevElem.next('.taglist') }

        const $newBtnContainer = $('<div/>', {
          class: 'new-btn-container'
        })
        $newBtns.each(function() {
          $newBtnContainer.append($(this).clone().removeAttr('id').removeClass('blue'))
          $(this).addClass('mobile-btn-imported')
        })
        $prevElem.after($newBtnContainer)
      }
    }
  })
  $(window).trigger('resize')
})(jQuery)
