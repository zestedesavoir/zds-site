/* ===== Zeste de Savoir ====================================================
   Add autocomplete for members names
   ---------------------------------
   Author: Sandhose / Quentin Gliech
   ========================================================================== */

(function($, undefined) {
    "use strict";

    function AutoComplete(input, options) {
        this.$wrapper = buildDom($(input));
        this.$input = this.$wrapper.find(".autocomplete-input");
        this.$dropdown = this.$wrapper.find(".autocomplete-dropdown");


        this.$input.on("keyup", this.handleInput.bind(this));
        this.$input.on("keydown", this.handleKeydown.bind(this));
        this.$input.on("blur", this.hideDropdown.bind(this));

        this.options = options;

        if(this.options.type === "multiple") {
            this.$form = this.$wrapper.parents("form:first");
            this.$form.on("submit", this.handleSubmit.bind(this));
        }

        if(this.options.clickable) {
          this.$dropdown.css("font-weight","bold");
        }

        this.selected = -1;

        this._lastInput = "";
    }

    AutoComplete.prototype = {
        cache: {},

        handleKeydown: function(e) {
            var $tmp;
            switch (e.which) {
                case 38: // Up
                    e.preventDefault();
                    e.stopPropagation();

                    if (this.selected === -1) {
                        this.select(this.$dropdown.find("ul li").last().attr("data-autocomplete-id"));
                    } else {
                        $tmp = this.$dropdown.find("ul li[data-autocomplete-id=" + this.selected + "]").prev("li");
                        this.select($tmp.length === 1 ? $tmp.attr("data-autocomplete-id") : -1);
                    }
                    break;
                case 40: // Down
                    e.preventDefault();
                    e.stopPropagation();

                    if (this.selected === -1) {
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

        handleInput: function(e) {
            if (e && (e.which === 38 || e.which === 40 || e.which === 13)) {
                e.preventDefault();
                e.stopPropagation();
            }

            var input = this.$input.val();

            if (this._lastInput === input)
                return;

            this._lastInput = input;

            var search = this.parseInput(input),
                self = this;

            if (!search || search === this._lastAutocomplete) {
                this.hideDropdown();
            } else {
                if (!this.options.minLength || search.length >= this.options.minLength) {
                  this.fetchData(search)
                  .done(function(data) {
                    self.updateCache(data.results);
                    self.updateDropdown(self.sortList(data.results, search));
                  })
                  .fail(function() {
                    console.error("[Autocompletition] Something went wrong...");
                  });
                  this.updateDropdown(this.sortList(this.searchCache(search), search));
                  this.showDropdown();
                }
            }
        },

        handleSubmit: function() {
            var content = this.$input.val();
            if(content.slice(-2) === ", ") {
                this.$input.val(content.slice(0, -2));
            }
        },

        showDropdown: function() {
            if (this.$input.is("input"))
                this.$dropdown.css("width", this.$input.outerWidth());
            this.$dropdown.show();
        },

        hideDropdown: function() {
            this.$dropdown.hide();
        },

        select: function(id) {
            this.selected = id;
            this.$dropdown.find("ul li.active").removeClass("active");
            this.$dropdown.find("ul li[data-autocomplete-id=" + this.selected + "]").addClass("active");
        },

        enter: function(selected) {
            selected = selected || this.selected;
            var input = this.$input.val();
            var lastChar = input.substr(-1);
            if ((lastChar === "," || selected === -1) && this.options.type === "multiple")
                return false;

            var completion = this.getFromCache(selected);
            if (!completion)
                return false;

            if (this.options.type === "multiple") {
                var lastComma = input.lastIndexOf(",");
                if (lastComma !== -1) {
                    input = input.substr(0, lastComma) + ", " + completion[this.options.fieldname] + ", ";
                    this.$input.val(input);
                } else {
                    this.$input.val(completion[this.options.fieldname] + ", ");
                }
            } else {
                this.$input.val(completion[this.options.fieldname]);
            }

            this._lastAutocomplete = completion[this.options.fieldname];
            this.selected = -1; // Deselect properly
            this.$input.trigger("input");

            if(this.options.clickable) {
              window.open(completion.url, "_blank");
            }
        },

        updateCache: function(data) {
            for (var i = 0; i < data.length; i++) {
                this.cache[data[i][this.options.fieldname]] = data[i];
            }
        },

        extractWords: function(input) {
            var words = $.grep(
                $.map(input.split(","), $.trim), // Remove empty
                function(e) {
                    return e === "" || e === undefined;
                },
                true
            );

            return words;
        },

        parseInput: function(input) {
            if (this.options.type === "multiple") {
                if (input.substr(-1) === "," || input.substr(-2) === ", ")
                    return false;

                var words = this.extractWords(input);
                if (words.length === 0) return false;

                return words[words.length - 1]; // last word in list
            } else {
                return input;
            }
        },

        searchCache: function(input) {
            var regexp = new RegExp(input, "ig");
            return $.grep(
                this.cache,
                function(e) {
                    return e.this.options.fieldname.match(regexp);
                }
            );
        },

        getFromCache: function(id) {
            for (var i in this.cache) {
                if (parseInt(this.cache[i].id) === parseInt(id))
                    return this.cache[i];
            }
            return false;
        },

        filterData: function(data, exclude) {
            var fieldname = this.options.fieldname;
            return data.filter(function(e) {
                return exclude.indexOf(e[fieldname]) === -1;
            });
        },

        updateDropdown: function(list) {
            var self = this;
            var onClick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.enter($(this).attr("data-autocomplete-id"));
                self.$input.focus();
                self.handleInput();
            };

            list = self.filterData(list, self.extractWords(this.$input.val()));

            if (list.length > this.options.limit) list = list.slice(0, this.options.limit);

            var $list = $("<ul>"),
                $el, selected = false;
            for (var i in list) {
                if ($("#my-account .username").text() === list[i][this.options.fieldname])
                    continue;
                $el = $("<li>").text(list[i][this.options.fieldname]);
                $el.attr("data-autocomplete-id", list[i].id);
                if (list[i].id === this.selected) {
                    $el.addClass("active");
                    selected = true;
                }

                $el.mousedown(onClick);
                $list.append($el);
            }
            this.$dropdown.children().remove();
            if(this.options.header && $list[0].childElementCount) {
              this.$dropdown.append("<div class=\"autocomplete-dropdown-header\">" + this.options.header + "</div>");
            }
            this.$dropdown.append($list);

            if (!selected)
                this.select($list.find("li").first().attr("data-autocomplete-id"));
        },

        sortList: function(list, search) {
            var bestMatches = [],
                otherMatches = [];

            for (var i = 0; i < list.length; i++) {
                if (list[i][this.options.fieldname].indexOf(search) === 0) {
                    bestMatches.push(list[i]);
                } else {
                    otherMatches.push(list[i]);
                }
            }

            var sortFn = function(a, b) {
                var valueA = a[this.options.fieldname].toLowerCase(),
                    valueB = b[this.options.fieldname].toLowerCase();
                if (valueA < valueB)
                    return -1;
                if (valueA > valueB)
                    return 1;
                return 0;
            };

            bestMatches.sort(sortFn.bind(this));
            otherMatches.sort(sortFn.bind(this));

            return bestMatches.concat(otherMatches);
        },

        fetchData: function(input) {
            return $.getJSON(this.options.url.replace("%s", input));
        }
    };

    function buildDom(input) {
        var $input = $(input),
            $wrapper = $("<div/>", {
                "class": "autocomplete-wrapper"
            }),
            $dropdown = $("<div/>", {
                "class": "autocomplete-dropdown"
            });

        return $input.addClass("autocomplete-input")
            .attr("autocomplete", "off")
            .wrap($wrapper)
            .parent()
            .append($dropdown);
    }

    $.fn.autocomplete = function(options) {
        var defaults = { // defaults are set for pm member autocomplete
            type: "single", // single|multiple|mentions
            url: "/api/membres/?search=%s",
            limit: 4,
            fieldname: "username"
        };

        if (!options) {
            options = $(this).data("autocomplete");
        }

        return new AutoComplete(this, $.extend(defaults, options));
    };

    $(document).ready(function() {
        $("[data-autocomplete]").each(function () {
          if ($(this).data)
              $(this).autocomplete();
        });
    });
})(jQuery);
