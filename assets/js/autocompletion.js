/* ===== Zeste de Savoir ====================================================
   Author: Sandhose / Quentin Gliech
   ---------------------------------
   Add autocomplete for members names
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
                        this.select(this.$dropdown.find("ul li").last().attr("data-autocomplete-id"));
                    } else {
                        $tmp = this.$dropdown.find("ul li[data-autocomplete-id=" + this.selected + "]").prev("li");
                        this.select($tmp.length === 1 ? $tmp.attr("data-autocomplete-id") : -1);
                    }
                    break;
                case 40: // Down
                    e.preventDefault();
                    e.stopPropagation();

                    if(this.selected === -1){
                        this.select(this.$dropdown.find("ul li").first().attr("data-autocomplete-id"));
                    } else {
                        $tmp = this.$dropdown.find("ul li[data-autocomplete-id=" + this.selected + "]").next("li");
                        this.select($tmp.length === 1 ? $tmp.attr("data-autocomplete-id") : -1);
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

            if(!search || search === this._lastAutocomplete){
                this.hideDropdown();
            } else {
                this.fetchUsers(search)
                    .done(function(data){
                        self.updateCache(data);
                        self.updateDropdown(self.sortList(data, search));
                    })
                    .fail(function(){
                        console.log("something went wrong...");
                    })
                ;
                this.updateDropdown(this.sortList(this.searchCache(search), search));
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
            this.$dropdown.find("ul li[data-autocomplete-id=" + this.selected + "]").addClass("active");
        },

        enter: function(selected){
            selected = selected || this.selected;
            var input = this.$input.val();
            var lastChar = input.substr(-1);
            if((lastChar === "," || lastChar === " " || selected === -1) && this.options.type === "multiple")
                return false;

            var completion = this.getFromCache(selected);
            if(!completion)
                return false;

            if(this.options.type === "multiple") {
                var lastSpace = input.replace(",", " ").lastIndexOf(" ");
                if(lastSpace){
                    input = input.substr(0, lastSpace + 1) + completion.value + ", ";
                    this.$input.val(input);
                } else {
                    this.$input.val(completion.value + ", ");
                }
            }
            else {
                this.$input.val(completion.value);
            }

            this._lastAutocomplete = completion.value;
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
            if(this.options.type === "multiple") {
                var lastChar = input.substr(-1);
                if(lastChar === "," || lastChar === " ")
                    return false;

                var words = this.extractWords(input);
                if(words.length === 0) return false;

                return words[words.length - 1]; // last word in list
            }
            else {
                return input;
            }
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
                self.enter($(this).attr("data-autocomplete-id"));
                self.$input.focus();
                self.handleInput();
            };

            if(list.length > this.options.limit) list = list.slice(0, this.options.limit);

            var $list = $("<ul>"), $el, selected = false;
            for(var i in list){
                $el = $("<li>").text(list[i].value);
                $el.attr("data-autocomplete-id", list[i].id);
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
                this.select($list.find("li").first().attr("data-autocomplete-id"));
        },

        sortList: function(list, search) {
            var bestMatches = [], otherMatches = [];

            for(var i = 0; i < list.length; i++) {
                if(list[i].value.indexOf(search) === 0) {
                    bestMatches.push(list[i]);
                }
                else {
                    otherMatches.push(list[i]);
                }
            }

            var sortFn = function(a, b) {
                var valueA = a.value.toLowerCase(), valueB = b.value.toLowerCase()
                if (valueA < valueB)
                    return -1 
                if (valueA > valueB)
                    return 1
                return 0
            };

            bestMatches.sort(sortFn);
            otherMatches.sort(sortFn);

            console.log(bestMatches, otherMatches);

            return bestMatches.concat(otherMatches);
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
            type: "single", // single|multiple|mentions
            url: "/membres/?q=%s",
            limit: 4
        };

        if(!options) {
            options = $(this).data("autocomplete");
        }

        return new AutoComplete(this, $.extend(defaults, options));
    };

    $(document).ready(function() {
        $("[data-autocomplete]").autocomplete();
    });
})(jQuery);