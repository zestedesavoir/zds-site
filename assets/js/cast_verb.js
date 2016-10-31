(function($, undefined){
    var VerbCast = function(cast){
        this.$cast = cast;
        if(!this.$cast.is(".verb-cast")) throw new Error("Target is not a .verb-cast");
        this.init();

    };
    VerbCast.prototype = {

        /**
         * Initialize the verbs
         */
        init: function() {
            this.$sender = this.$cast.find(".submitbutton");
            this.feedVerbs();
            this.$sender.on("click", this.castVote.bind(this));
            this.$cast.on("click", "li button", this.switchVote.bind(this));
        },
        feedVerbs: function(){
            this.elements = [];
            var $list = this.$cast.find("ul");
            $.ajax("/api/contenus/verbs/", {method: "GET", dataType: "JSON"}).done(function(data){
                data.results.forEach(function(verb){
                    var sentenceLabel = "sentence_label";
                    var element = $("<li/>").append(
                        $("<button/>").attr("type", "button")
                            .attr("data-verb-label", verb.label)
                            .addClass("verb")
                            .text(verb[sentenceLabel]));
                    $list.append(element);
                    this.elements.push(element);
                }.bind(this));
                this.$activeElement = this.elements[0];
                this.uiFeelBack();
            }.bind(this));

        },
        uiFeelBack: function () {
            this.elements.forEach(function (element) {
               element.removeClass("active");
            });
            this.$activeElement.addClass("active");
        },
        castVote: function(){
            var dataToSend = {
                content__pk: this.$cast.attr("data-content-pk"),
                verb: this.$activeElement.attr("data-verb-label"),
            };
            var currentCast = this;
            $.ajax("/api/contenus/casting/", {method:"POST",
                headers:{"X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()},
                data:JSON.stringify(dataToSend),
                dataType:"JSON",
                contentType:"application/json"
            }).done(function () {
               currentCast.$cast.style("display", "none"); // quick and dirty
            });
        },
        switchVote: function (e) {
            this.$activeElement = $(e.target);
            this.uiFeelBack();
        }
    };
    $.fn.verbCast = function() {
        if(this.length !== 1) {
            return $(this).map(function(index, elem) {
                $(elem).verbCast();
            });
        } else {
            var $cast;
            if($(this).is(".verb-cast")) {
                $cast = $(this);
            } else {
                $cast = $(this).parents(".verb-cast");
            }
            return new VerbCast($cast);
        }
    };

    $(document).ready(function() {
        $(".verb-cast").verbCast();
    });
})(jQuery);
