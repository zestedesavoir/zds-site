/* ===== Zeste de Savoir ====================================================
   Manage Karma buttons
   ========================================================================== */

(function($) {
  'use strict'

  /**
   * Manages the karma of a message
   * @class
   */
  const Karma = function(message) {
    this.message = message
    if (!this.message.is('.topic-message')) throw new Error('Target is not a .topic-message')
    this.init()
    this.message.data('karma', this)
  }

  Karma.prototype = {
    /**
     * @var {number} - The interval between regular updates in ms
     */
    updateInterval: 30 * 1000,

    /**
     * Initialize the karma
     */
    init: function() {
      this.karmaElem = this.message.find('.message-karma')

      /**
       * @member {string} - Endpoint to vote & fetch karma update
       */
      this.karmaURI = this.karmaElem.data('karma-uri')

      /**
       * @member {string} - Token to pass when doing a put request
       */
      this.csrf = $('input[name=csrfmiddlewaretoken]').val()

      this.like = {}
      this.dislike = {}

      this.like.button = this.karmaElem.find('.upvote')
      this.dislike.button = this.karmaElem.find('.downvote')

      this.like.tooltip = this.like.button.tooltip(this.like.button.hasClass('has-vote') ? 'Chargement...' : '')
      this.dislike.tooltip = this.dislike.button.tooltip(this.dislike.button.hasClass('has-vote') ? 'Chargement...' : '')

      $(this.like.tooltip.elem).add(this.dislike.tooltip.elem).on('click', this.showDetails.bind(this))

      this.like.listElem = $('<ul>', { class: 'vote-list like' })
      this.dislike.listElem = $('<ul>', { class: 'vote-list dislike' })

      /**
       * @member {boolean} - True if the message can be voted
       */
      this.canVote = this.karmaElem.hasClass('can-vote')
      this.updateInterval = 30 * 1000
      if (this.canVote) {
        this.like.button.on('click', this.vote.bind(this, 'like'))
        this.dislike.button.on('click', this.vote.bind(this, 'dislike'))
      }

      this.like.button.on('mouseover', this.regularUpdate.bind(this))
      this.dislike.button.on('mouseover', this.regularUpdate.bind(this))

      if (this.like.button.hasClass('voted')) {
        this.currentVote = 'like'
      } else if (this.dislike.button.hasClass('voted')) {
        this.currentVote = 'dislike'
      } else {
        this.currentVote = 'neutral'
      }
    },

    /**
     * Send a vote request and update with the result
     *
     * @param {string} vote - "like" or "dislike"
     * @param {jQuery.Event} [event] - Event that triggered the vote. Will be prevented
     */
    vote: function(vote, event) {
      if (vote === this.currentVote) vote = 'neutral'
      $.ajax({
        method: 'PUT',
        url: this.karmaURI,
        data: { vote: vote },
        headers: {
          'X-CSRFToken': this.csrf
        }
      }).done(this.update.bind(this))

      if (event) {
        event.preventDefault()
        event.stopPropagation()
      }
    },

    /**
     * Fetch the message's karma
     */
    fetchUpdate: function() {
      const self = this
      if (this.updating) return
      this.updating = true
      $.getJSON(this.karmaURI).done(this.update.bind(this)).always(function() {
        self.updating = false
      })
    },

    /**
     * Triggers this.update() if it was not updated withing this.updateInterval
     */
    regularUpdate: function() {
      if (!this.lastUpdate || this.lastUpdate + this.updateInterval < Date.now()) {
        this.fetchUpdate()
        this.lastUpdate = Date.now()
      }
    },

    /**
     * Update message's karma
     *
     * @param {Object} data
     * @param {Object} data.like - Data related to likes
     * @param {Object} data.like.users - List of the non-anonymous likers
     * @param {string} data.like.users[].username - Username of a liker
     * @param {number} data.like.count - Like total count
     * @param {Object} data.dislike - Data related to dislikes
     * @param {Object} data.dislike.users - List of the non-anonymous dislikers
     * @param {string} data.dislike.users[].username - Username of a disliker
     * @param {number} data.dislike.count - Dislike total count
     * @param {string} data.user - User vote, "like", "dislike" or "neutral"
     */
    update: function(data) {
      this.updateOne(data, 'like', 'dislike')
      this.updateOne(data, 'dislike', 'like')
      this.currentVote = data.user
    },

    /**
     * Update one karma button
     *
     * Updates the button's classes, the tooltip, the title and the text
     *
     * @param {Object} data - See Karma.update data parameter
     * @param {string} sign - The sign of the button ("like" or "dislike")
     * @param {string} otherSign - The sign of the other button ("like" or "dislike")
     */
    updateOne: function(data, sign, otherSign) {
      if (data[sign].count > 0) {
        this[sign].button.addClass('has-vote')
      } else {
        this[sign].button.removeClass('has-vote')
      }

      if (data[sign].count > data[otherSign].count) {
        this[sign].button.addClass('more-voted')
      } else {
        this[sign].button.removeClass('more-voted')
      }

      if (data.user === sign) {
        this[sign].button.addClass('voted')
      } else {
        this[sign].button.removeClass('voted')
      }

      // Updating the title
      let likeTitleCount = data[sign].count + ' personne'
      if (data[sign].count === 1 && sign === 'like') {
        likeTitleCount += ' a'
      } else if (data[sign].count === 1 && sign === 'dislike') {
        likeTitleCount += " n'a pas"
      } else if (sign === 'like') {
        likeTitleCount += 's ont'
      } else {
        likeTitleCount += "s n'ont pas"
      }
      likeTitleCount += ' trouvé ce message utile'

      let likeTitle
      if (this.canVote) {
        likeTitle = 'Ce message ' + (sign === 'like' ? 'est' : "n'est pas") + ' utile'
        if (data[sign].count !== 0) {
          likeTitle += ' (' + likeTitleCount + ')'
        }
      } else {
        likeTitle = likeTitleCount
      }

      this[sign].button.attr('title', likeTitle)
      // Updating the text
      this[sign].button.text((sign === 'like' ? '+' : '-') + data[sign].count)

      // Updating the tooltip
      if (Object.hasOwnProperty.call(data[sign], 'users')) {
        const likers = data[sign].users.slice(0, 9)
        const otherLikeCount = data[sign].count - likers.length

        const currentUser = $('#my-account .username').text()
        const likes = likers.map(function(e) { return e.username === currentUser ? 'Vous (' + e.username + ')' : e.username })
        if (otherLikeCount > 0) {
          let otherLikeStr = likes.length > 0 ? 'et ' + otherLikeCount + ' autre' : otherLikeCount + ' vote'
          if (otherLikeCount !== 1) otherLikeStr += 's'
          likes.push(otherLikeStr)
        }

        this[sign].tooltip.setContent(likes.map(function(l) { return $('<div>', { text: l }) }))

        // Build list in modal
        this[sign].listElem.empty()

        if (data[sign].count === 0) {
          $('<li>', { class: 'muted', text: 'Pas de votes ' + (sign === 'like' ? 'positifs' : 'négatifs') }).appendTo(this[sign].listElem)
        } else {
          this[sign].listElem.append(data[sign].users.map(function(user) {
            /* jshint -W069 */
            return $('<li>').append($('<a>', { href: user.html_url, text: user.username }).prepend($('<img />', { src: user.avatar_url })))
            /* jshint +W069 */
          }))

          const anonymous = data[sign].count - data[sign].users.length
          if (anonymous) {
            $('<li>', { text: anonymous + ' anonyme' + (anonymous === 1 ? '' : 's'), class: 'muted' }).appendTo(this[sign].listElem)
          }
        }
      }
    },

    /**
     * Show the details of the votes in a modal
     */
    showDetails: function() {
      if (!this.detailsModal) {
        const body = $('<div>', { class: 'vote-details' })
          .append($('<div>', { class: 'vote-col' }).append($('<h3>', { text: 'Votes positifs' })).append(this.like.listElem))
          .append($('<div>', { class: 'vote-col' }).append($('<h3>', { text: 'Votes négatifs' })).append(this.dislike.listElem))

        this.detailsModal = new window.Modal({
          title: 'Détail des votants',
          titleIcon: 'hide light',
          body: body,
          closeText: 'Fermer'
        })
      }

      this.detailsModal.open()
    }
  }

  /**
   * Create new Karma object for each jQuery element
   *
   * @example
   * $(".topic-message #p42").karma().vote("like");
   * @returns {Karma}
   */
  $.fn.karma = function() {
    if (this.length !== 1) {
      return $(this).map(function(index, elem) {
        return $(elem).karma()
      })
    } else {
      let message
      if ($(this).is('.topic-message')) {
        message = $(this)
      } else {
        message = $(this).parents('.topic-message')
      }

      const instance = message.data('karma')
      if (instance) return instance

      return new Karma(message)
    }
  }

  $(document).ready(function() {
    $('.topic-message').has('.message-karma').karma()
  })
})(jQuery)
