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
    data: ["Admin1", "Admin2", "Admin3"],

    handleInput: function() {
      var search = this.parseInput(this.$input.val());
      if(!search) {
        this.$dropdown.hide();
      }
      else {
        this.updateDropdown(this.search(search));
        this.$dropdown.show();
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

    search: function(input) {
      var regexp = new RegExp(input, "ig")
      return $.grep(this.data, function(e) {
        return e.match(regexp);
      });
    },

    updateDropdown: function(list) {
      console.log(list);
      var $list = $("<ul>"), el;
      for(var i in list) {
        el = $("<li>").text(list[i]);
        $list.append(el);
      }
      this.$dropdown.children().remove();
      this.$dropdown.append($list);
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
})