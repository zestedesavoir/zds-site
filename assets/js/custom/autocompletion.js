/* ===== Zeste de Savoir ====================================================
   Author: Sandhose / Quentin Gliech
   ---------------------------------
   Add autocompletion for members names
   ========================================================================== */

var AutoComplete = (function($) {
  function AutoComplete(input, options) {
    this.$wrapper = buildDom(input);
    this.$input = this.$wrapper.find(".autocomplete-input");
    this.$dropdown = this.$wrapper.find(".autocomplete-dropdown");

    this.$input.on("keyup", this.handleInput.bind(this));
  }

  AutoComplete.prototype = {
    cache: {},

    handleInput: function() {
      var search = this.parseInput(this.$input.val()),
          self = this;
      if(!search) {
        this.$dropdown.hide();
      }
      else {
        this.fetchUsers(search)
          .done(function(data) {
            self.updateCache(data);
            self.updateDropdown(data);
          })
          .fail(function() {
            console.log("something went wrong...");
          });
        this.updateDropdown(this.searchCache(search));
        this.$dropdown.show();
      }
    },

    updateCache: function(data) {
      for(var i = 0; i < data.length; i++) {
        this.cache[data[i].value] = data[i];
      }
    },

    parseInput: function(input) {
      var lastChar = input.substr(-1);
      if(lastChar === "," || lastChar === " ") return false; // on est passé au pseudo suivant

      input = input.replace(/ /g, ","); // Virgules à la place d'espaces
      var words = input.split(",");
      words = $.grep(words, function(e) { return e === "" || e === undefined; }, true); // vire les empty
      
      if(words.length === 0) return false;

      return words[words.length - 1]; // last word in list
    },

    searchCache: function(input) {
      var regexp = new RegExp(input, "ig")
      return $.grep(this.cache, function(e) {
        return e.value.match(regexp);
      });
    },

    updateDropdown: function(list) {
      var $list = $("<ul>"), el;
      for(var i in list) {
        el = $("<li>").text(list[i].value);
        $list.append(el);
      }
      this.$dropdown.children().remove();
      this.$dropdown.append($list);
    },

    fetchUsers: function(input) {
      return $.getJSON("/membres/?q=" + input);
    }
  };

  function buildDom(input) {
    var $input = $(input);
    var $wrapper = $("<span>", { class: "autocomplete-wrapper" });
    var $dropdown = $("<div>", { class: "autocomplete-dropdown" });

    return $input.addClass("autocomplete-input")
      .wrap($wrapper)
      .parent()
      .append($dropdown);
  }

  return AutoComplete;
})(jQuery);

(function($) {
  $.fn.autocomplete = function(options) {
    var defaults = {
      type: "mp", // mp || mentions
      url: "/membres/?q=%s"
    };

    options = $.extend(defaults, options);

    return new AutoComplete(this, options);
  }
})(jQuery);

$(document).ready(function() {
  $("#id_participants").autocomplete();
});