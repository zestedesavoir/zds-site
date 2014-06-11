/* ===== Zeste de Savoir ====================================================
   Author: Sandhose / Quentin Gliech
   ---------------------------------
   Add autocompletion for members names
   ========================================================================== */

(function($) {
    "use strict";

    function AutoComplete(input, options) {
        this.$wrapper = buildDom($(input));
        this.$input = this.$wrapper.find(".autocomplete-input");
        this.$dropdown = this.$wrapper.find(".autocomplete-dropdown");

        this.$input.on("keyup", this.handleInput.bind(this));
        this.$input.on("keydown", this.handleKeydown.bind(this));
        this.$input.on("blur", this.hideDropdown.bind(this));

        this.selected = -1;

        this._lastInput = "";

        this.options = options;
    }

    AutoComplete.prototype = {
        cache: {},

        handleKeydown: function(e){
            var $tmp;
            switch(e.which){
                case 38: // Up
                    e.preventDefault();
                    e.stopPropagation();

                    if(this.selected === -1){
                        this.select(this.$dropdown.find("ul li").last().attr("data-autocompletion-id"));
                    } else {
                        $tmp = this.$dropdown.find("ul li[data-autocompletion-id=" + this.selected + "]").prev("li");
                        this.select(
                            $tmp.length === 1 
                                ? $tmp.attr("data-autocompletion-id") 
                                : -1
                        );
                    }
                    break;
                case 40: // Down
                    e.preventDefault();
                    e.stopPropagation();

                    if(this.selected === -1){
                        this.select(this.$dropdown.find("ul li").first().attr("data-autocompletion-id"));
                    } else {
                        $tmp = this.$dropdown.find("ul li[data-autocompletion-id=" + this.selected + "]").next("li");
                        this.select(
                            $tmp.length === 1
                                ? $tmp.attr("data-autocompletion-id")
                                : -1
                        );
                    }
                    break;
                case 13: // Enter
                    e.preventDefault();
                    e.stopPropagation();
                    this.enter();
                    break;
            }
        },

        handleInput: function(e){
            if(e && (e.which === 38 || e.which === 40 || e.which === 13)){ 
                e.preventDefault();
                e.stopPropagation();
            }

            var input = this.$input.val();

            if(this._lastInput === input)
                return;

            this._lastInput = input;

            var search = this.parseInput(input),
                self = this;

            if(!search){
                this.hideDropdown();
            } else {
                this.fetchUsers(search)
                    .done(function(data){
                        self.updateCache(data);
                        self.updateDropdown(data);
                    })
                    .fail(function(){
                        console.log("something went wrong...");
                    })
                ;
                this.updateDropdown(this.searchCache(search));
                this.showDropdown();
            }
        },

        showDropdown: function(){
            this.$dropdown.show();
        },

        hideDropdown: function(){
            this.$dropdown.hide();
        },

        select: function(id){
            this.selected = id;
            this.$dropdown.find("ul li.active").removeClass("active");
            this.$dropdown.find("ul li[data-autocompletion-id=" + this.selected + "]").addClass("active");
        },

        enter: function(selected){
            selected = selected || this.selected;
            var input = this.$input.val();
            var lastChar = input.substr(-1);
            if(lastChar === "," || lastChar === " " || selected === -1)
                return false; // At the next pseudo

            var completion = this.getFromCache(selected);
            if(!completion)
                return false;
            var lastSpace = input.replace(",", " ").lastIndexOf(" ");
            if(lastSpace){
                input = input.substr(0, lastSpace + 1) + completion.value + ", ";
                this.$input.val(input);
            } else {
                this.$input.val(completion.value + ", ");
            }
        },

        updateCache: function(data){
            for(var i = 0; i < data.length; i++){
                this.cache[data[i].value] = data[i];
            }
        },

        extractWords: function(input){
            input = input.replace(/ /g, ","); // Replace space with comas
            var words = $.grep(
                input.split(","),  // Remove empty
                function(e){
                    return e === "" || e === undefined;
                },
                true
            );

            return words;
        },

        parseInput: function(input){
            var lastChar = input.substr(-1);
            if(lastChar === "," || lastChar === " ")
                return false; // At the next pseudo

            var words = this.extractWords(input);
            if(words.length === 0) return false;

            return words[words.length - 1]; // last word in list
        },

        searchCache: function(input){
            var regexp = new RegExp(input, "ig");
            return $.grep(
                this.cache,
                function(e){
                    return e.value.match(regexp);
                }
            );
        },

        getFromCache: function(id){
            for(var i in this.cache){
                if(parseInt(this.cache[i].id) === parseInt(id))
                    return this.cache[i];
            }
            return false;
        },

        updateDropdown: function(list){
            var self = this;
            var onClick = function(e){
                e.preventDefault();
                e.stopPropagation();
                self.enter($(this).attr("data-autocompletion-id"));
                self.$input.focus();
                self.handleInput();
            };

            var $list = $("<ul>"), $el, selected = false;
            for(var i in list){
                $el = $("<li>").text(list[i].value);
                $el.attr("data-autocompletion-id", list[i].id);
                if(list[i].id === this.selected){
                    $el.addClass("active");
                    selected = true;
                }

                $el.mousedown(onClick);
                $list.append($el);
            }
            this.$dropdown.children().remove();
            this.$dropdown.append($list);

            if(!selected)
                this.select($list.find("li").first().attr("data-autocompletion-id"));
        },

        fetchUsers: function(input) {
            return $.getJSON(this.options.url.replace("%s", input));
        }
    };

    function buildDom(input) {
        var $input = $(input),
            $wrapper = $("<span>", { class: "autocomplete-wrapper" }),
            $dropdown = $("<div>", { class: "autocomplete-dropdown" });

        return $input.addClass("autocomplete-input")
            .wrap($wrapper)
            .parent()
            .append($dropdown)
        ;
    }

    $.fn.autocomplete = function(options) {
        var defaults = {
            type: "mp",
            url: "/membres/?q=%s"
        };

        return new AutoComplete(this, $.extend(defaults, options));
    };

    $(document).ready(function() {
        $("#id_participants").autocomplete();
    });
})(jQuery);