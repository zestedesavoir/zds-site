/* ===== Zeste de Savoir ====================================================
   Manage Karma buttons
   ========================================================================== */

(function($, undefined) {
    "use strict";

    /**
     * Manages the karma of a message
     * @class
     */
    var Karma = function(message) {
        this.message = message;
        if(!this.message.is(".topic-message")) throw new Error("Target is not a .topic-message");
        this.init();
        this.message.data("karma", this);
    };

    Karma.prototype = {
        /**
         * @var {number} - The interval between regular updates in ms
         */
        updateInterval: 30 * 1000,

        /**
         * Initialize the karma
         */
        init: function() {
            this.karmaElem = this.message.find(".message-karma");

            /**
             * @member {jQuery} - The like button
             */
            this.upvoteButton = this.karmaElem.find(".upvote");

            /**
             * @member {jQuery} - The dislike button
             */
            this.downvoteButton = this.karmaElem.find(".downvote");

            /**
             * @member {string} - Endpoint to vote & fetch karma update
             */
            this.karmaURI = this.karmaElem.data("karma-uri");

            /**
             * @member {string} - Token to pass when doing a post request
             */
            this.csrf = $("input[name=csrfmiddlewaretoken]").val();

            this.upvoteButton.tooltip(this.upvoteButton.hasClass("has-vote") ? "Chargement..." : "");
            this.downvoteButton.tooltip(this.downvoteButton.hasClass("has-vote") ? "Chargement..." : "");

            /**
             * @member {boolean} - True if the message can be voted
             */
            this.canVote = this.karmaElem.hasClass("can-vote");
            this.updateInterval = 30 * 1000;
            if(this.canVote) {
                this.upvoteButton.on("click", this.vote.bind(this, "like"));
                this.downvoteButton.on("click", this.vote.bind(this, "dislike"));
            }

            this.upvoteButton.on("mouseover", this.regularUpdate.bind(this));
            this.downvoteButton.on("mouseover", this.regularUpdate.bind(this));

            if(this.upvoteButton.hasClass("voted")) {
                this.currentVote = "like";
            } else if(this.downvoteButton.hasClass("voted")) {
                this.currentVote = "dislike";
            } else {
                this.currentVote = "neutral";
            }
        },

        /**
         * Send a vote request and update with the result
         *
         * @param {string} vote - "like" or "dislike"
         * @param {jQuery.Event} [event] - Event that triggered the vote. Will be prevented
         */
        vote: function(vote, event) {
            if(vote === this.currentVote) vote = "neutral";
            $.post(this.karmaURI, { "vote": vote, "csrfmiddlewaretoken": this.csrf }).done(this.update.bind(this));

            if(event) {
                event.preventDefault();
                event.stopPropagation();
            }
        },

        /**
         * Fetch the message's karma
         */
        fetchUpdate: function() {
            var self = this;
            if(this.updating) return;
            this.updating = true;
            $.getJSON(this.karmaURI).done(this.update.bind(this)).always(function() {
                 self.updating = false;
            });
        },

        /**
         * Triggers this.update() if it was not updated withing this.updateInterval
         */
        regularUpdate: function() {
            if(!this.lastUpdate || this.lastUpdate + this.updateInterval < Date.now()) {
                this.fetchUpdate();
                this.lastUpdate = Date.now();
            }
        },

        /**
         * Update message's karma
         *
         * @param {Object} data
         * @param {Object} data.like - Data related to likes
         * @param {Object} data.like.list - List of the non-anonymous likers
         * @param {string} data.like.list[].username - Username of a liker
         * @param {number} data.like.count - Like total count
         * @param {Object} data.dislike - Data related to dislikes
         * @param {Object} data.dislike.list - List of the non-anonymous dislikers
         * @param {string} data.dislike.list[].username - Username of a disliker
         * @param {number} data.dislike.count - Dislike total count
         * @param {string} data.user - User vote, "like", "dislike" or "neutral"
         */
        update: function(data) {
            this.updateOne(data, "like", "dislike", this.upvoteButton);
            this.updateOne(data, "dislike", "like", this.downvoteButton);
            this.currentVote = data.user;
        },

        /**
         * Update one karma button
         *
         * Updates the button's classes, the tooltip, the title and the text
         *
         * @param {Object} data - See Karma.update data parameter
         * @param {string} sign - The sign of the button ("like" or "dislike")
         * @param {string} otherSign - The sign of the other button ("like" or "dislike")
         * @param {jQuery} button - The button to update
         */
        updateOne: function(data, sign, otherSign, button) {
            if(data[sign].count > 0) {
                button.addClass("has-vote");
            } else {
                button.removeClass("has-vote");
            }

            if(data[sign].count > data[otherSign].count) {
                button.addClass("more-voted");
            } else {
                button.removeClass("more-voted");
            }

            if(data.user === sign) {
                button.addClass("voted");
            } else {
                button.removeClass("voted");
            }

            // Updating the title
            var likeTitleCount = data[sign].count + " personne";
            if(data[sign].count === 1 && sign === "like") {
                likeTitleCount += " a";
            } else if(data[sign].count === 1 && sign === "dislike") {
                likeTitleCount += " n'a pas";
            } else if(sign === "like") {
                likeTitleCount += "s ont";
            } else {
                likeTitleCount += "s n'ont pas";
            }
            likeTitleCount += " trouvé ce message utile";

            var likeTitle;
            if(this.canVote) {
                likeTitle = "Ce message " + (sign === "like" ? "est" : "n'est pas") + " utile";
                if(data[sign].count !== 0) {
                    likeTitle += " (" +  likeTitleCount + ")";
                }
            } else {
                likeTitle = likeTitleCount;
            }

            button.attr("title", likeTitle);
            // Updating the text
            button.text((sign === "like" ? "+" : "-") + data[sign].count);

            // Updating the tooltip
            if(data[sign].hasOwnProperty("list")) {
                var likers = data[sign].list.slice(0, 9);
                var otherLikeCount = data[sign].count - likers.length;

                var currentUser = $("#my-account .username").text();
                var likeStr = likers.map(function(e) { return e.username === currentUser ? "Vous (" + e.username + ")" : e.username; }).join("<br>");
                if(otherLikeCount > 0) {
                    if(likeStr !== "") likeStr += "<br> et " + otherLikeCount + " autre";
                    else likeStr = otherLikeCount + " vote";

                    if(otherLikeCount !== 1) likeStr += "s";
                }

                button.tooltip(likeStr);
            }
        }
    };

    /**
     * Create new Karma object for each jQuery element
     *
     * @example
     * $(".topic-message #p42").karma().vote("like");
     * @returns {Karma}
     */
    $.fn.karma = function() {
        if(this.length > 1) {
            return $(this).map(function(index, elem) {
                $(elem).karma();
            });
        } else {
            var message;
            if($(this).is(".topic-message")) {
                message = $(this);
            } else {
                message = $(this).parents(".topic-message");
            }

            var instance = message.data("karma");
            if(instance) return instance;

            return new Karma(message);
        }
    };

    $(document).ready(function() {
        $(".topic-message").has(".message-karma").karma();
    });
})(jQuery);
