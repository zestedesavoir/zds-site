/* ===== Zeste de Savoir ====================================================
   Manage Karma buttons
   ========================================================================== */

(function($, undefined) {
    "use strict";

    var Karma = function(message) {
        this.message = $(message);
        this.init();
    };

    Karma.prototype = {
        init: function() {
            this.karmaElem = this.message.find(".message-karma");
            this.upvoteButton = this.karmaElem.find(".upvote");
            this.downvoteButton = this.karmaElem.find(".downvote");
            this.karmaURI = this.karmaElem.data("karma-uri");
            this.csrf = $("input[name=csrfmiddlewaretoken]").val();
            this.upvoteButton.tooltip(this.upvoteButton.hasClass("has-vote") ? "Chargement..." : "");
            this.downvoteButton.tooltip(this.downvoteButton.hasClass("has-vote") ? "Chargement..." : "");
            this.updateInterval = 30 * 1000;

            this.canVote = this.karmaElem.hasClass("can-vote");
            if(this.canVote) {
                this.upvoteButton.on("click", this.vote.bind(this, "like"));
                this.downvoteButton.on("click", this.vote.bind(this, "dislike"));
            }

            this.upvoteButton.on("mouseover", this.regularUpdate.bind(this));
            this.downvoteButton.on("mouseover", this.regularUpdate.bind(this));
        },

        vote: function(vote, e) {
            $.post(this.karmaURI, { "vote": vote, "csrfmiddlewaretoken": this.csrf }).done(this.update.bind(this));

            if(e) {
                e.preventDefault();
                e.stopPropagation();
            }
        },

        fetchUpdate: function() {
            var self = this;
            if(this.updating) return;
            this.updating = true;
            $.getJSON(this.karmaURI).done(this.update.bind(this)).always(function() {
                 self.updating = false;
            });
        },

        regularUpdate: function() {
            if(!this.lastUpdate || this.lastUpdate + this.updateInterval < Date.now()) {
                this.fetchUpdate();
                this.lastUpdate = Date.now();
            }
        },

        update: function(data) {
            this.updateOne(data, "like", "dislike", this.upvoteButton);
            this.updateOne(data, "dislike", "like", this.downvoteButton);
        },

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

            if(data[sign].user) {
                button.addClass("voted");
            } else {
                button.removeClass("voted");
            }

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
            button.text((sign === "like" ? "+" : "-") + data[sign].count);
        }
    };

    $.fn.karma = function() {
        if(this.length > 1) {
            return $(this).map(function(index, elem) {
                $(elem).karma();
            });
        } else {
            var instance = this.data("karma");
            if(instance) return instance;

            return new Karma(this);
        }
    };

    $(document).ready(function() {
        $(".topic-message").has(".message-karma").karma();
    });
})(jQuery);
