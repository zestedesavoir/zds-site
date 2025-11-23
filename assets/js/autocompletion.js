/* ===== Zeste de Savoir ====================================================
   Add autocomplete for members names
   ---------------------------------
   Author: Sandhose / Quentin Gliech
   ========================================================================== */

(function($) {
  'use strict'

  function AutoComplete(input, options) {
    this.$wrapper = buildDom($(input))
    this.$input = this.$wrapper.find('.autocomplete-input')
    this.$dropdown = this.$wrapper.find('.autocomplete-dropdown')


    this.$input.on('keyup', this.handleInput.bind(this))
    this.$input.on('keydown', this.handleKeydown.bind(this))
    this.$input.on('blur', this.hideDropdown.bind(this))

    this.options = options

    if (this.options.type === 'multiple' || this.options.type === 'multiple_checkbox') {
      this.$form = this.$wrapper.parents('form:first')
      this.$form.on('submit', this.handleSubmit.bind(this))
      if (this.options.type === 'multiple_checkbox') {
        this.$excluded = this.$form.find('.excluded_field')
      }
    }



    if (this.options.clickable) {
      this.$dropdown.css('font-weight', 'bold')
    }

    this.selected = -1

    this._lastInput = ''
  }

  AutoComplete.prototype = {
    cache: {},

    handleKeydown: function(e) {
      let $tmp
      switch (e.which) {
        case 38: // Up
          e.preventDefault()
          e.stopPropagation()

          if (this.selected === -1) {
            this.select(this.$dropdown.find('ul li').last().attr('data-autocomplete-id'))
          } else {
            $tmp = this.$dropdown.find('ul li[data-autocomplete-id=' + this.selected + ']').prev('li')
            this.select($tmp.length === 1 ? $tmp.attr('data-autocomplete-id') : -1)
          }
          break
        case 40: // Down
          e.preventDefault()
          e.stopPropagation()

          if (this.selected === -1) {
            this.select(this.$dropdown.find('ul li').first().attr('data-autocomplete-id'))
          } else {
            $tmp = this.$dropdown.find('ul li[data-autocomplete-id=' + this.selected + ']').next('li')
            this.select($tmp.length === 1 ? $tmp.attr('data-autocomplete-id') : -1)
          }
          break
        case 13: // Enter
          if (!e.ctrlKey) { // Do not capture Ctrl + Enter, as it is used to validate modals
            e.preventDefault()
            e.stopPropagation()
            this.enter()
          }
          break
      }
    },

    handleInput: function(e) {
      if (e && (e.which === 38 || e.which === 40 || e.which === 13)) {
        e.preventDefault()
        e.stopPropagation()
      }

      const input = this.$input.val()

      if (this._lastInput === input) { return }

      this._lastInput = input

      const search = this.parseInput(input)
      const self = this

      if (!search || search === this._lastAutocomplete) {
        this.hideDropdown()
      } else {
        if (!this.options.minLength || search.length >= this.options.minLength) {
          let jsonData
          if (this.options.type === 'multiple_checkbox') {
            jsonData = this.fetchData(search, this.$excluded.val())
          } else {
            jsonData = this.fetchData(search, '')
          }
          jsonData
            .done(function(data) {
              self.updateCache(data.results)
              self.updateDropdown(data.results)
            })
            .fail(function() {
              console.error('[Autocompletion] Something went wrong...')
            })
          this.updateDropdown(this.searchCache(search))
          this.showDropdown()
        }
      }
    },

    handleSubmit: function() {
      const content = this.$input.val()
      if (content.slice(-2) === ', ') {
        this.$input.val(content.slice(0, -2))
      }
    },

    showDropdown: function() {
      if (this.$input.is('input')) { this.$dropdown.css('width', this.$input.outerWidth()) }
      this.$dropdown.show()
    },

    hideDropdown: function() {
      this.$dropdown.hide()
    },

    select: function(id) {
      this.selected = id
      this.$dropdown.find('ul li.active').removeClass('active')
      this.$dropdown.find('ul li[data-autocomplete-id=' + this.selected + ']').addClass('active')
    },

    enter: function(selected) {
      selected = selected || this.selected
      let input = this.$input.val()
      const lastChar = input.substr(-1)
      if ((lastChar === ',' || selected === -1) && this.options.type === 'multiple') { return false }

      const completion = this.getFromCache(selected)
      if (!completion) { return false }

      if (this.options.type === 'multiple') {
        const lastComma = input.lastIndexOf(',')
        if (lastComma !== -1) {
          input = input.substr(0, lastComma) + ', ' + completion[this.options.fieldname] + ', '
          this.$input.val(input)
        } else {
          this.$input.val(completion[this.options.fieldname] + ', ')
        }
      } else if (this.options.type === 'single') {
        this.$input.val(completion[this.options.fieldname])
      } else if (this.options.type === 'multiple_checkbox') {
        this.$input.before("<label class='checkbox' for='id_options_" + completion.id + "'> <input type='checkbox' checked='checked' name='options' id='id_options_" + completion.id + "' value='" + completion.id + "'>" + completion[this.options.fieldname] + '</label>')
        this.$excluded.val(this.$excluded.val() + ',' + completion.id)
        this.$input.val('')
      }

      this._lastAutocomplete = completion[this.options.fieldname]
      this.selected = -1 // Deselect properly
      this.$input.trigger('input')

      if (this.options.clickable) {
        window.open(completion.url, '_blank')
      }
    },

    updateCache: function(data) {
      for (let i = 0; i < data.length; i++) {
        this.cache[data[i][this.options.fieldname]] = data[i]
      }
    },

    extractWords: function(input) {
      const words = $.grep(
        $.map(input.split(','), $.trim), // Remove empty
        function(e) {
          return e === '' || e === undefined
        },
        true
      )

      return words
    },

    parseInput: function(input) {
      if (this.options.type === 'multiple') {
        if (input.substr(-1) === ',' || input.substr(-2) === ', ') { return false }

        const words = this.extractWords(input)
        if (words.length === 0) return false

        return words[words.length - 1] // last word in list
      } else {
        return input
      }
    },

    searchCache: function(input) {
      const regexp = new RegExp(input, 'ig')
      return $.grep(
        this.cache,
        function(e) {
          return e.this.options.fieldname.match(regexp)
        }
      )
    },

    getFromCache: function(id) {
      for (const i in this.cache) {
        if (parseInt(this.cache[i].id) === parseInt(id)) { return this.cache[i] }
      }
      return false
    },

    filterData: function(data, exclude) {
      const fieldname = this.options.fieldname
      return data.filter(function(e) {
        return exclude.indexOf(e[fieldname]) === -1
      })
    },

    updateDropdown: function(list) {
      const self = this
      const onClick = function(e) {
        e.preventDefault()
        e.stopPropagation()
        self.enter($(this).attr('data-autocomplete-id'))
        self.$input.focus()
        self.handleInput()
      }

      // Exclude already selected items but the last one (it's the prefix of the item we are looking for)
      const alreadyChosenWords = self.extractWords(this.$input.val()).slice(0, -1)
      list = self.filterData(list, alreadyChosenWords)

      if (list.length > this.options.limit) list = list.slice(0, this.options.limit)

      const $list = $('<ul>')
      let $el; let selected = false
      for (const i in list) {
        if ($('#my-account .username').text() === list[i][this.options.fieldname]) { continue }
        $el = $('<li>').text(list[i][this.options.fieldname])
        $el.attr('data-autocomplete-id', list[i].id)
        if (list[i].id === this.selected) {
          $el.addClass('active')
          selected = true
        }

        $el.mousedown(onClick)
        $list.append($el)
      }
      this.$dropdown.children().remove()
      if (this.options.header && $list[0].childElementCount) {
        this.$dropdown.append('<div class="autocomplete-dropdown-header">' + this.options.header + '</div>')
      }
      this.$dropdown.append($list)

      if (!selected) { this.select($list.find('li').first().attr('data-autocomplete-id')) }
    },

    fetchData: function(input, excludeTerms) {
      let data = this.options.url.replace('%s', input)
      data = data.replace('%e', excludeTerms)
      return $.getJSON(data)
    }
  }

  function buildDom(input) {
    const $input = $(input)
    const $wrapper = $('<div/>', {
      class: 'autocomplete-wrapper'
    })
    const $dropdown = $('<div/>', {
      class: 'autocomplete-dropdown'
    })

    return $input.addClass('autocomplete-input')
      .attr('autocomplete', 'off')
      .wrap($wrapper)
      .parent()
      .append($dropdown)
  }

  $.fn.autocomplete = function(options) {
    const defaults = { // defaults are set for pm member autocomplete
      type: 'single', // single|multiple|mentions
      url: '/api/membres/?search=%s',
      limit: 4,
      fieldname: 'username'
    }

    if (!options) {
      options = $(this).data('autocomplete')
    }

    return new AutoComplete(this, $.extend(defaults, options))
  }

  $(document).ready(function() {
    $('[data-autocomplete]').each(function() {
      if ($(this).data) { $(this).autocomplete() }
    })
  })
})(jQuery)
