/* ===== Zeste de Savoir ====================================================
   Manage Poll Markdown
   ========================================================================== */
(function($, undefined) {
    "use strict";

    /**
     * Manages the poll
     * @class
     */
    var Poll = function(poll) {
        this.poll = poll;
        if(!this.poll.is(".reaction-poll")) throw new Error("Target is not a .reaction-poll");
        this.init();
        this.poll.data("poll", this);
    };

    var poll_uri = "/api/sondages/";

    Poll.prototype = {

        /**
         * Initialize the poll
         */
        init: function() {
            this.URI = this.poll.data("pk");
            this.fetchUpdate();
        },

        /**
         * Fetch the poll
         */
        fetchUpdate: function() {
            $.getJSON(poll_uri+this.URI).done(function(response){
                console.log(response)
            });
        }
    };

    /**
     * Create new Poll object for each jQuery element
     * @returns {Poll}
     */
    $.fn.poll = function() {
        return new Poll($(this));
    };

    $(document).ready(function() {
        $(".reaction-poll").poll();

    });
})(jQuery);
