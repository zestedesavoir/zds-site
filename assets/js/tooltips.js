(function($, undefined) {
    "use strict";

    var Tooltip = function(options) {
        this.options = $.extend({ target: null, content: null }, options);
        if(!Tooltip._initialized) {
            this.firstRun();
        }

        this.init();
    };

    Tooltip.prototype = {
        firstRun: function() {
            Tooltip.container = $("<div>", { class: "tooltips-container" });
            Tooltip.list = [];

            $("body").append(Tooltip.container);
            Tooltip._initialized = true;
        },

        init: function() {
            this.wrapper = $("<div>", { class: "tooltip-wrapper" });
            this.elem = $("<div>", { class: "tooltip" });
            this.target = $(this.options.target);
            this.setOrientation("top");
            this.setContent(this.options.content);
            this.hide();

            this.wrapper.append(this.elem).appendTo(Tooltip.container);

            this.target.on("mouseover", this.mouseover.bind(this));
            this.wrapper.on("mouseover", this.mouseover.bind(this));
            this.target.on("mouseout", this.mouseout.bind(this));
            this.wrapper.on("mouseout", this.mouseout.bind(this));

            this.hideTimeout = null;

            Tooltip.list.push(this);
        },

        mouseover: function() {
            this.visible || this.show();
            clearTimeout(this.hideTimeout);
        },

        mouseout: function() {
            this.hideTimeout = setTimeout(this.hide.bind(this), 50);
        },

        setContent: function(content) {
            this.elem.html(content);

            if(this.visible) {
                this.recalc();
            }
        },

        hide: function() {
            this.visible = false;
            this.wrapper.hide();
        },

        show: function() {
            this.visible = true;
            this.wrapper.show();
            this.recalc();
        },

        guessOrientation: function() {
            if(this.target.offset().top - $(window).scrollTop() < this.wrapper.height()) {
                this.setOrientation("bottom");
            } else {
                this.setOrientation("top");
            }
        },

        recalc: function() {
            var css = {
                top: null,
                bottom: null,
                left: this.target.offset().left + (this.target.outerWidth() / 2) - (this.wrapper.width() / 2)
            };

            this.guessOrientation();
            if(this.orientation === "top") {
                css.top = this.target.offset().top - this.wrapper.outerHeight();
            } else if(this.orientation === "bottom") {
                css.top = this.target.offset().top + this.target.outerHeight();
            } else {
                css.bottom = this.target.offset().top - this.wrapper.outerHeight() + 8;
            }

            this.wrapper.css(css);
        },

        setOrientation: function(orientation) {
            if (orientation !== "top"
             && orientation !== "bottom"
             || orientation === this.orientation) return;

            this.wrapper.addClass(orientation);
            this.wrapper.removeClass(this.orientation);
            this.orientation = orientation;
        }
    };

    $.fn.tooltip = function(content) {
        var tooltip = $(this).data("tooltip");
        if(tooltip) {
            tooltip.setContent(content);
        } else {
            tooltip = new Tooltip({ target: this, content: content });
            $(this).data("tooltip", tooltip);
        }

        return tooltip;
    };
})(jQuery);
