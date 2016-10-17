(function($, undefined){
    var VerbCast = function(cast){
        this.cast = cast;
        if(!this.message.is(".verb-cast")) throw new Error("Target is not a .verb-cast");
        this.init();

    };
    VerbCast.prototype = {

        /**
         * Initialize the karma
         */
        init: function() {
            this.elements = this.message.children(".verb");
            this.activeElement = this.elements[0];
            this.uiFeelBack();
        },
        uiFeelBack: function () {
            this.elements.each(function () {
               $(this).removeClass("active");
            });
            this.activeElement.addClass("active");
        },
        castVote: function(){

        },
        switchVote: function (e) {
            this.activeElement = $(e.target);
            this.uiFeelBack();
        }
    };
    $.fn.verbCast = function() {
        if(this.length !== 1) {
            return $(this).map(function(index, elem) {
                $(elem).karma();
            });
        } else {
            var message;
            if($(this).is(".verb-cast")) {
                message = $(this);
            } else {
                message = $(this).parents(".verb-cast");
            }
            return new VerbCast(message);
        }
    };

    $(document).ready(function() {
        $(".topic-message").has(".verb-cast").verbCast();
    });
})(jQuery);
