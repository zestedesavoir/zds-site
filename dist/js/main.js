/* Modernizr 2.8.3 (Custom Build) | MIT & BSD
 * Build: http://modernizr.com/download/#-flexboxlegacy-inlinesvg-svg-svgclippaths-touch-shiv-mq-cssclasses-teststyles-testallprops-prefixes-css_mask-ie8compat
 */
;window.Modernizr=function(a,b,c){function B(a){j.cssText=a}function C(a,b){return B(m.join(a+";")+(b||""))}function D(a,b){return typeof a===b}function E(a,b){return!!~(""+a).indexOf(b)}function F(a,b){for(var d in a){var e=a[d];if(!E(e,"-")&&j[e]!==c)return b=="pfx"?e:!0}return!1}function G(a,b,d){for(var e in a){var f=b[a[e]];if(f!==c)return d===!1?a[e]:D(f,"function")?f.bind(d||b):f}return!1}function H(a,b,c){var d=a.charAt(0).toUpperCase()+a.slice(1),e=(a+" "+o.join(d+" ")+d).split(" ");return D(b,"string")||D(b,"undefined")?F(e,b):(e=(a+" "+p.join(d+" ")+d).split(" "),G(e,b,c))}var d="2.8.3",e={},f=!0,g=b.documentElement,h="modernizr",i=b.createElement(h),j=i.style,k,l={}.toString,m=" -webkit- -moz- -o- -ms- ".split(" "),n="Webkit Moz O ms",o=n.split(" "),p=n.toLowerCase().split(" "),q={svg:"http://www.w3.org/2000/svg"},r={},s={},t={},u=[],v=u.slice,w,x=function(a,c,d,e){var f,i,j,k,l=b.createElement("div"),m=b.body,n=m||b.createElement("body");if(parseInt(d,10))while(d--)j=b.createElement("div"),j.id=e?e[d]:h+(d+1),l.appendChild(j);return f=["&#173;",'<style id="s',h,'">',a,"</style>"].join(""),l.id=h,(m?l:n).innerHTML+=f,n.appendChild(l),m||(n.style.background="",n.style.overflow="hidden",k=g.style.overflow,g.style.overflow="hidden",g.appendChild(n)),i=c(l,a),m?l.parentNode.removeChild(l):(n.parentNode.removeChild(n),g.style.overflow=k),!!i},y=function(b){var c=a.matchMedia||a.msMatchMedia;if(c)return c(b)&&c(b).matches||!1;var d;return x("@media "+b+" { #"+h+" { position: absolute; } }",function(b){d=(a.getComputedStyle?getComputedStyle(b,null):b.currentStyle)["position"]=="absolute"}),d},z={}.hasOwnProperty,A;!D(z,"undefined")&&!D(z.call,"undefined")?A=function(a,b){return z.call(a,b)}:A=function(a,b){return b in a&&D(a.constructor.prototype[b],"undefined")},Function.prototype.bind||(Function.prototype.bind=function(b){var c=this;if(typeof c!="function")throw new TypeError;var d=v.call(arguments,1),e=function(){if(this instanceof e){var a=function(){};a.prototype=c.prototype;var f=new a,g=c.apply(f,d.concat(v.call(arguments)));return Object(g)===g?g:f}return c.apply(b,d.concat(v.call(arguments)))};return e}),r.flexboxlegacy=function(){return H("boxDirection")},r.touch=function(){var c;return"ontouchstart"in a||a.DocumentTouch&&b instanceof DocumentTouch?c=!0:x(["@media (",m.join("touch-enabled),("),h,")","{#modernizr{top:9px;position:absolute}}"].join(""),function(a){c=a.offsetTop===9}),c},r.svg=function(){return!!b.createElementNS&&!!b.createElementNS(q.svg,"svg").createSVGRect},r.inlinesvg=function(){var a=b.createElement("div");return a.innerHTML="<svg/>",(a.firstChild&&a.firstChild.namespaceURI)==q.svg},r.svgclippaths=function(){return!!b.createElementNS&&/SVGClipPath/.test(l.call(b.createElementNS(q.svg,"clipPath")))};for(var I in r)A(r,I)&&(w=I.toLowerCase(),e[w]=r[I](),u.push((e[w]?"":"no-")+w));return e.addTest=function(a,b){if(typeof a=="object")for(var d in a)A(a,d)&&e.addTest(d,a[d]);else{a=a.toLowerCase();if(e[a]!==c)return e;b=typeof b=="function"?b():b,typeof f!="undefined"&&f&&(g.className+=" "+(b?"":"no-")+a),e[a]=b}return e},B(""),i=k=null,function(a,b){function l(a,b){var c=a.createElement("p"),d=a.getElementsByTagName("head")[0]||a.documentElement;return c.innerHTML="x<style>"+b+"</style>",d.insertBefore(c.lastChild,d.firstChild)}function m(){var a=s.elements;return typeof a=="string"?a.split(" "):a}function n(a){var b=j[a[h]];return b||(b={},i++,a[h]=i,j[i]=b),b}function o(a,c,d){c||(c=b);if(k)return c.createElement(a);d||(d=n(c));var g;return d.cache[a]?g=d.cache[a].cloneNode():f.test(a)?g=(d.cache[a]=d.createElem(a)).cloneNode():g=d.createElem(a),g.canHaveChildren&&!e.test(a)&&!g.tagUrn?d.frag.appendChild(g):g}function p(a,c){a||(a=b);if(k)return a.createDocumentFragment();c=c||n(a);var d=c.frag.cloneNode(),e=0,f=m(),g=f.length;for(;e<g;e++)d.createElement(f[e]);return d}function q(a,b){b.cache||(b.cache={},b.createElem=a.createElement,b.createFrag=a.createDocumentFragment,b.frag=b.createFrag()),a.createElement=function(c){return s.shivMethods?o(c,a,b):b.createElem(c)},a.createDocumentFragment=Function("h,f","return function(){var n=f.cloneNode(),c=n.createElement;h.shivMethods&&("+m().join().replace(/[\w\-]+/g,function(a){return b.createElem(a),b.frag.createElement(a),'c("'+a+'")'})+");return n}")(s,b.frag)}function r(a){a||(a=b);var c=n(a);return s.shivCSS&&!g&&!c.hasCSS&&(c.hasCSS=!!l(a,"article,aside,dialog,figcaption,figure,footer,header,hgroup,main,nav,section{display:block}mark{background:#FF0;color:#000}template{display:none}")),k||q(a,c),a}var c="3.7.0",d=a.html5||{},e=/^<|^(?:button|map|select|textarea|object|iframe|option|optgroup)$/i,f=/^(?:a|b|code|div|fieldset|h1|h2|h3|h4|h5|h6|i|label|li|ol|p|q|span|strong|style|table|tbody|td|th|tr|ul)$/i,g,h="_html5shiv",i=0,j={},k;(function(){try{var a=b.createElement("a");a.innerHTML="<xyz></xyz>",g="hidden"in a,k=a.childNodes.length==1||function(){b.createElement("a");var a=b.createDocumentFragment();return typeof a.cloneNode=="undefined"||typeof a.createDocumentFragment=="undefined"||typeof a.createElement=="undefined"}()}catch(c){g=!0,k=!0}})();var s={elements:d.elements||"abbr article aside audio bdi canvas data datalist details dialog figcaption figure footer header hgroup main mark meter nav output progress section summary template time video",version:c,shivCSS:d.shivCSS!==!1,supportsUnknownElements:k,shivMethods:d.shivMethods!==!1,type:"default",shivDocument:r,createElement:o,createDocumentFragment:p};a.html5=s,r(b)}(this,b),e._version=d,e._prefixes=m,e._domPrefixes=p,e._cssomPrefixes=o,e.mq=y,e.testProp=function(a){return F([a])},e.testAllProps=H,e.testStyles=x,g.className=g.className.replace(/(^|\s)no-js(\s|$)/,"$1$2")+(f?" js "+u.join(" "):""),e}(this,this.document),Modernizr.addTest("cssmask",Modernizr.testAllProps("maskRepeat")),Modernizr.addTest("ie8compat",function(){return!window.addEventListener&&document.documentMode&&document.documentMode===7});

/* ===== Zeste de Savoir ====================================================
   Managment of accessibility links
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    $("#accessibility a").on("focus", function() {
        $(".dropdown:visible").parent().find(".active").removeClass("active");
        $("#accessibility").addClass("focused");
    }).on("blur", function() {
        $("#accessibility").removeClass("focused");
    }).on("click", function() {
        var link = $(this).attr("href");
        setTimeout(function() { // Forces the focus on next tick
            $(link).find(":tabbable").first().focus(); // Focus the first focusable element
        });
    });
})(jQuery);


/* ===== Zeste de Savoir ====================================================
   Accordeon for sidebar
   ---------------------------------
   Author: Alex-D
   ========================================================================== */

(function($, undefined){
    "use strict";

    function accordeon($elem){
        $("h4 + ul, h4 + ol", $elem).each(function(){
            if($(".current", $(this)).length === 0)
                $(this).hide();
        });

        $("h4", $elem).click(function(e){
            $("+ ul, + ol", $(this)).slideToggle(100);

            e.preventDefault();
            e.stopPropagation();
        });
    }
    
    $(document).ready(function(){
        $(".main .sidebar.accordeon, .main .sidebar .accordeon")
        .each(function(){
            accordeon($(this));
        })
        .on("DOMNodeInserted", function(e){
            accordeon($(e.target));
        });
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function($, undefined){
    "use strict";

    /**
     * Toggle the text of the element by the text of an attribute
     *
     * @param {string} dataAttribute
     */
    $.fn.toggleText = function(dataAttribute){
        var text = this.text(),
            textToPut = this.data(dataAttribute);

        this.text(textToPut);
        this.data(dataAttribute, text);
    };

    function synchText() {
        $("#mobile-menu [data-ajax-input]").each(function () {
            var dataAjaxInput = $(this).data("ajax-input");
            console.log($(this).text(), $(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']").text(), dataAjaxInput);

            $(this).text($(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']").text());
        });
    }

    /**
     * Karma of the messages
     */
    $(".topic-message").on("click", "button.upvote, button.downvote", function(e){
        var $thumb = $(this),
            $form = $(this).parents("form:first"),
            $karma = $thumb.parents(".message-karma:first"),
            $upvote = $karma.find(".upvote"),
            $downvote = $karma.find(".downvote"),
            $otherThumb = $thumb.hasClass("downvote") ? $upvote : $downvote;

        var message = $form.find("input[name=message]").val(),
            csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "message": message,
                "csrfmiddlewaretoken": csrfmiddlewaretoken
            },
            success: function(data){
                // Update upvotes
                if(data.upvotes > 0){
                    $upvote.addClass("has-vote").text("+" + data.upvotes);
                } else {
                    $upvote.removeClass("has-vote").empty();
                }
                // Update downvotes
                if(data.downvotes > 0){
                    $downvote.addClass("has-vote").text("-" + data.downvotes);
                } else {
                    $downvote.removeClass("has-vote").empty();
                }

                // Show to the user what thumb is voted
                $thumb.toggleClass("voted");
                $otherThumb.removeClass("voted");

                // Show to the user what thumb is the more voted
                if(data.upvotes > data.downvotes) {
                    $upvote.addClass("more-voted");
                } else {
                    $upvote.removeClass("more-voted");
                }
                if(data.downvotes > data.upvotes) {
                    $downvote.addClass("more-voted");
                } else {
                    $downvote.removeClass("more-voted");
                }

                $thumb.blur();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Follow a topic
     */
    $(".sidebar").on("click", "[data-ajax-input='follow-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $email = $(this).parents("li:first").next().find("[data-ajax-input='follow-topic-by-email']");

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            follow = $form.find("input[name=follow]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "follow": follow,
                "page": page
            },
            success: function(data){
                if(data.follow){
                    $form.find("input[name=follow]").val(1);
                } else {
                    if($email.hasClass("blue") === false){
                        $email.toggleText("content-on-click");
                        $email.addClass("blue");

                        $email.parents("form:first").find("input[name=email]").val(0);
                    }

                    $form.find("input[name=follow]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("blue yellow");

                synchText();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Be notify by email
     */
    $(".sidebar").on("click", "[data-ajax-input='follow-topic-by-email']", function(e){
        var $act = $(this),
            $follow = $(this).parents("li:first").prev().find("[data-ajax-input='follow-topic']"),
            $form = $(this).parents("form:first");

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            email = $form.find("input[name=email]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "email": email,
                "page": page
            },
            success: function(data){
                if(data.email){
                    if($follow.hasClass("yellow") === false){
                        $follow.toggleText("content-on-click");
                        $follow.removeClass("blue");
                        $follow.addClass("yellow");

                        $follow.parents("form:first").find("input[name=follow]").val(1);
                    }

                    $form.find("input[name=email]").val(1);
                } else {
                    $form.find("input[name=email]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("blue");

                synchText();
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Mark a topic solved
     */
    $(".sidebar").on("click", "[data-ajax-input='solve-topic']", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first");

        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            topic = $form.find("input[name=topic]").val(),
            solved = $form.find("input[name=solved]").val(),
            page = $form.find("input[name=page]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "topic": topic,
                "solved": solved,
                "page": page
            },
            success: function(data){
                if(data.solved){
                    $form.find("input[name=solved]").val(1);
                } else {
                    $form.find("input[name=solved]").val(0);
                }

                $act.toggleText("content-on-click");
                $act.toggleClass("green blue");
                $("[data-ajax-output='solve-topic']").toggleClass("empty");

                synchText();
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Mobile action
     */
    $("#mobile-menu").on("click", "[data-ajax-input]", function(e){
        var dataAjaxInput = $(this).data("ajax-input");
        var $button = $(".sidebar").find("button[data-ajax-input='" + dataAjaxInput + "']");

        if ($button[0]) {
            $(this).toggleText("content-on-click");
            $button.click();

            e.stopPropagation();
            e.preventDefault();
        }
    });

    /**
     * Cite a message
     */
    $(".message-actions").on("click", "[data-ajax-input='cite-message']", function(e){
        var $act = $(this),
            $editor = $(".md-editor");

        $.ajax({
            url: $act.attr("href"),
            dataType: "json",
            success: function(data){
                $editor.val($editor.val() + data.text + "\n\n");
            }
        });

        // scroll to the textarea and focus the textarea
        $("html, body").animate({ scrollTop: $editor.offset().top }, 500);
        $editor.focus();

        e.stopPropagation();
        e.preventDefault();
    });

    /**
     * Preview the message
     */
    $(".message-bottom").on("click", "[data-ajax-input='preview-message']", function(e){
        var $form = $(this).parents("form:first");
        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            text = $form.find("textarea[name=text]").val(),
            lastPost = $form.find("input[name=last_post]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "text": text,
                "last_post": lastPost,
                "preview": "preview"
            },
            success: function(data){
                $(".previsualisation").remove();

                $(data).insertAfter($form);

                /* global MathJax */
                if ($(data).find("mathjax").length > 0)
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    /*
     * Mark a message useful
     */
    $(".topic-message").on("click", "[data-ajax-input='mark-message-as-useful']", function(e){
        var $button = $(this),
            $form = $button.parents("form:first"),
            $message = $form.parents("article"),
            $usefulText = $message.find("[data-ajax-output='mark-message-as-useful']"),
            csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken
            },
            success: function(){
                $message.toggleClass("helpful");
                $button.toggleText("content-on-click");
                $usefulText.toggleClass("hidden");
                $button.blur();
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });
})(jQuery);


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
                this.fetchUsers(search)
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
                    input = input.substr(0, lastComma) + ", " + completion.username + ", ";
                    this.$input.val(input);
                } else {
                    this.$input.val(completion.username + ", ");
                }
            } else {
                this.$input.val(completion.username);
            }

            this._lastAutocomplete = completion.username;
            this.selected = -1; // Deselect properly
            this.$input.trigger("input");
        },

        updateCache: function(data) {
            for (var i = 0; i < data.length; i++) {
                this.cache[data[i].username] = data[i];
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
                    return e.username.match(regexp);
                }
            );
        },

        getFromCache: function(id) {
            for (var i in this.cache) {
                if (parseInt(this.cache[i].pk) === parseInt(id))
                    return this.cache[i];
            }
            return false;
        },

        filterData: function(data, exclude) {
            return data.filter(function(e) {
                return exclude.indexOf(e.username) === -1;
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
                if ($("#my-account .username").text() === list[i].username)
                    continue;
                $el = $("<li>").text(list[i].username);
                $el.attr("data-autocomplete-id", list[i].pk);
                if (list[i].pk === this.selected) {
                    $el.addClass("active");
                    selected = true;
                }

                $el.mousedown(onClick);
                $list.append($el);
            }
            this.$dropdown.children().remove();
            this.$dropdown.append($list);

            if (!selected)
                this.select($list.find("li").first().attr("data-autocomplete-id"));
        },

        sortList: function(list, search) {
            var bestMatches = [],
                otherMatches = [];

            for (var i = 0; i < list.length; i++) {
                if (list[i].username.indexOf(search) === 0) {
                    bestMatches.push(list[i]);
                } else {
                    otherMatches.push(list[i]);
                }
            }

            var sortFn = function(a, b) {
                var valueA = a.username.toLowerCase(),
                    valueB = b.username.toLowerCase();
                if (valueA < valueB)
                    return -1;
                if (valueA > valueB)
                    return 1;
                return 0;
            };

            bestMatches.sort(sortFn);
            otherMatches.sort(sortFn);

            return bestMatches.concat(otherMatches);
        },

        fetchUsers: function(input) {
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
        var defaults = {
            type: "single", // single|multiple|mentions
            url: "/api/membres/?search=%s",
            limit: 4
        };

        if (!options) {
            options = $(this).data("autocomplete");
        }

        return new AutoComplete(this, $.extend(defaults, options));
    };

    $(document).ready(function() {
        $("[data-autocomplete]").autocomplete();
        $("#content").on("DOMNodeInserted", "input", function(e) {
            var $input = $(e.target);
            if ($input.is("[data-autocomplete]"))
                $input.autocomplete();
        });
    });
})(jQuery);


/* ===== Zeste de Savoir ====================================================
   Close alert-boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    $(".main").on("click", ".close-alert-box:not(.open-modal)", function(e) {
        $(this).parents(".alert-box:first").slideUp(150, function(){
            $(this).remove();
        });
        e.preventDefault();
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Simulate click on element from another
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, document, undefined){
    "use strict";
    
    var dropdownMouseDown = false;

    function dataClick($elem){
        $elem
        .attr("tabindex", -1)
        .attr("aria-hidden", true)
        .on("mousedown", function(){
            dropdownMouseDown = true;
        })
        .on("mouseup", function(){
            dropdownMouseDown = false;
        })
        .on("click focus", function(e){
            if(e.type === "focus" && dropdownMouseDown)
                return false;

            if(!($(this).hasClass("dont-click-if-sidebar") && $(".header-container .mobile-menu-btn").is(":visible"))){
                e.preventDefault();
                e.stopPropagation();
                $("#" + $(this).attr("data-click")).trigger(e.type);
            }
        });
    }

    $(document).ready(function(){
        dataClick($("[data-click]"));
        $("#content").on("DOMNodeInserted", "[data-click]", function(e){
            dataClick($(e.target));
        });
    });
})(jQuery, document);

/* ===== Zeste de Savoir ====================================================
   Dropdown menu open/close
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    var mouseDown = false,
        shiftHold = false;

    $(document).on("keydown keyup", function(e){
        shiftHold = e.shiftKey;
    });

    $(".dropdown").each(function(){
        var $dropdown = $(this),
            $elem = $(this).parent().find("> a");

        if(!$elem.parents(".logbox").length)
            $elem.addClass("has-dropdown");

        $elem
        .on("mousedown", function(){
            mouseDown = true;
        })
        .on("mouseup", function(){
            mouseDown = false;
        })
        .on("click", function(e){
            if(($(this).parents(".header-menu-list").length > 0 && parseInt($("html").css("width")) < 960))
                return true;

            e.preventDefault();
            e.stopPropagation();

            if(!$(this).hasClass("active")){
                activeDropdown($(this));
                $(this).off("blur");
            } else {
                $(this).removeClass("active");
                triggerCloseDropdown($(this));
            }
        })
        .on("focus", function(e){
            e.preventDefault();

            if(!mouseDown && !$elem.hasClass("active")){
                activeDropdown($elem);
                
                $elem
                .off("blur")
                .on("blur", function(){
                    $elem
                    .one("blur", function(){
                        if(shiftHold)
                            triggerCloseDropdown($elem);
                    });

                    setTimeout(function(){
                        if($(":tabbable:focus", $dropdown).length){
                            var listenBlurLast = function(){
                                $(":tabbable:last", $dropdown)
                                .one("blur", function(){
                                    if(shiftHold){
                                        listenBlurLast();
                                        return;
                                    }
                                    $elem.removeClass("active");
                                    triggerCloseDropdown($elem);
                                });
                            };
                            listenBlurLast();
                        } else {
                            $elem.removeClass("active");
                            triggerCloseDropdown($elem);
                        }
                    }, 10);
                })
                .one("mousemove", function(){
                    $(this).off("blur");
                });
            }
        });
    });

    $(".dropdown-list").on("focus", function(){
        $(this).find(":tabbable:first").focus();
    });

    $("body").on("keydown", function(e){
        if(e.which === 27)
            $(".has-dropdown.active, .ico-link.active, #my-account.active").focus().removeClass("active");
    });

    function activeDropdown($elem){
        $("body").trigger("click");
        $elem.addClass("active");
        $elem.parent().find(".dropdown-list").scrollTop(0);

        if($elem.is("[data-active]"))
            $("#" + $elem.attr("data-active")).addClass("active");

        if($elem.parents(".logbox").length)
            $("html").addClass("dropdown-active");

        triggerCloseDropdown($elem);
    }
    function triggerCloseDropdown($that){
        if($that.hasClass("active")){
            $("body").one("click", function(e){
                if(!$(e.target).hasClass("dropdown") && !$(e.target).parents(".dropdown").length) {
                    $that.removeClass("active");
                    $that.next(":tabbable").focus();

                    if($that.is("[data-active]"))
                        $("#" + $that.attr("data-active")).removeClass("active");
                }
                
                triggerCloseDropdown($that);
            });
        } else {
            $("html").removeClass("dropdown-active");
            $(".dropdown :tabbable").off("blur");

            if($that.is("[data-active]"))
                $("#" + $that.attr("data-active")).removeClass("active");
        }
    }
})(jQuery);


(function(window, document, undefined){
    "use strict";

    var zForm = {
        buttons: "bold,italic,strike,abbr,key#sup,sub#center,right#ul,ol#titles,blockcode,image,quote,link#infoblocks",
        isExecuted: false,
        selection: null,

        addEvent: function(elem, evt, listener) {
            if (elem.addEventListener) {
                elem.addEventListener(evt, listener, false);
            } else {
                elem.attachEvent("on" + evt, listener);
            }
        },

        tags: {
            bold:       { title: "Gras",                        start: "**",                end: "**"   },
            italic:     { title: "Italique",                    start: "*",                 end: "*"    },
            strike:     { title: "Barré",                       start: "~~",                end: "~~"   },
            sup:        { title: "Exposant",                    start: "^",                 end: "^"    },
            sub:        { title: "Indice",                      start: "~",                 end: "~"    },
            abbr:       { title: "Abréviation" },
            key:        { title: "Touche",                      start: "||",                end: "||"   },

            titles:     { title: "Titres",                      action: "buildTitles"                   },

            ul:         { title: "Liste à puces"                                                        },
            ol:         { title: "Liste ordonnée"                                                       },

            center:     { title: "Aligner au centre",           start: "-> ",               end: " <-"  },
            right:      { title: "Aligner à droite",            start: "-> ",               end: " ->"  },

            quote:      { title: "Citation"                                                             },
            image:      { title: "Image"                                                                },
            link:       { title: "Lien"                                                                 },

            table:      { title: "Tableau"                                                              },

            infoblocks: { title: "Blocs spéciaux",              action: "buildInfoblocks"               },
            information:{ title: "Bloc Information"                                                     },
            question:   { title: "Bloc Question"                                                        },
            attention:  { title: "Bloc Attention"                                                       },
            error:      { title: "Bloc Erreur"                                                          },
            secret:     { title: "Bloc masqué"                                                          },

            monospace:  { title: "Code inline",                 start: "`",                 end: "`"    },
            blockcode:  { title: "Bloc de code coloré",         action: "buildCode"                     },

            math:       { title: "Formule mathématique",        start: "$",                 end: "$"    },
            hr:         { title: "Ligne horizontalle",          start: "\n\n------\n\n",    end: ""     },

            footnote:   { title: "Note en bas de page"                                                  }
        },

        codes: {
            Web: [
                ["html",    "HTML"],
                ["css",     "CSS"],
                ["js",      "Javascript"],
                ["php",     "PHP"],
                ["jfx",     "JavaFX"],
                ["cf",      "ColdFusion"],
                ["as3",     "Actionscript 3"],
                ["pl",      "Perl"],
                ["sql",     "SQL"],
                ["xml",     "XML"]
            ],
            Prog: [
                ["c",       "C"],
                ["cpp",     "C++"],
                ["csharp",  "C#"],
                ["java",    "Java"],
                ["delphi",  "Delphi"],
                ["py",      "Python"],
                ["ruby",    "Ruby"],
                ["pascal",  "Pascal"],
                ["vb",      "Visual Basic"],
                ["vbnet",   "VB.NET"],
            ],
            Autres: [
                ["bash",    "Bash"],
                ["diff",    "Diff"],
                ["erl",     "Erlang"],
                ["scala",   "Scala"],
                ["groovy",  "Groovy"],
                ["ps",      "PowerShell"],
                ["text",    "Autre"]
            ]
        },

        titles: {
            "link" :    "Lien hypertexte",
            "abbr" :    "Abréviation",
            "image":    "Image"
        },

        init: function() {
            var listTexta = document.getElementsByTagName("textarea");

            for (var i=0, c=listTexta.length; i<c; i++) {
                if (/md.editor/.test(listTexta[i].className)) {
                    this.setup(listTexta[i].id);
                }
            }

            this.addEvent(document.getElementById("content"), "DOMNodeInserted", (function(_this){
                return function(e) {
                    var element = e.target;
                    if (/md.editor/.test(element.className)) {
                        if(element.previousElementSibling.indexOf("zform-toolbar") > -1) {
                            _this.setup(element.id);
                        }
                    }
                };
            }) (this));

            var overlay = document.body.appendChild(document.createElement("div"));
                overlay.id = "zform-modal-overlay";

            var wrapper = document.body.appendChild(document.createElement("div"));
                wrapper.id = "zform-modal-wrapper";

            wrapper.innerHTML =
            "<div>" +
                "<header id=\"zform-modal-header\"></header>" +

                "<section class=\"zform-modal\" id=\"zform-modal-link\">" +
                    "<div>" +
                        "<label for=\"zform-modal-link-href\">Lien :</label>" +
                        "<input type=\"text\" id=\"zform-modal-link-href\" />" +
                    "</div>" +

                    "<div>" +
                        "<label for=\"zform-modal-link-text\">Texte :</label>" +
                        "<input type=\"text\" id=\"zform-modal-link-text\" />" +
                    "</div>" +
                "</section>" +

                "<section class=\"zform-modal\" id=\"zform-modal-image\">" +
                    "<div>" +
                        "<label for=\"zform-modal-image-src\">URL :</label>" +
                        "<input type=\"text\" id=\"zform-modal-image-src\" />" +
                    "</div>" +

                    "<div>" +
                        "<label for=\"zform-modal-image-text\">Texte :</label>" +
                        "<input type=\"text\" id=\"zform-modal-image-text\" />" +
                    "</div>" +
                "</section>" +

                "<section class=\"zform-modal\" id=\"zform-modal-abbr\">" +
                    "<div>" +
                        "<label for=\"zform-modal-abbr-abbr\">Abréviation :</label>" +
                        "<input type=\"text\" id=\"zform-modal-abbr-abbr\" />" +
                    "</div>" +

                    "<div>" +
                        "<label for=\"zform-modal-abbr-text\">Texte :</label>" +
                        "<input type=\"text\" id=\"zform-modal-abbr-text\" />" +
                    "</div>" +
                "</section>" +

                "<section class=\"zform-modal\" id=\"zform-modal-footnote\">" +
                    "<div>" +
                        "<label for=\"zform-modal-footnote-guid\">Identifiant :</label>" +
                        "<input type=\"text\" id=\"zform-modal-footnote-guid\" />" +
                    "</div>" +

                    "<div>" +
                        "<label for=\"zform-modal-footnote-text\">Texte :</label>" +
                    "</div>" +

                    "<div>" +
                        "<textarea id=\"zform-modal-footnote-text\"></textarea>" +
                    "</div>" +
                "</section>" +

                "<footer><a id=\"zform-modal-validate\" class=\"btn btn-submit\">Valider</a> <a id=\"zform-modal-cancel\" class=\"btn btn-cancel secondary tiny\">Annuler</a></footer>" +
            "</div>";

            this.addEvent(document.getElementById("zform-modal-validate"), "click", (function(_this) {
                return function() {
                    _this.validatePopup();
                };
            }) (this));

            this.addEvent(document.getElementById("zform-modal-cancel"), "click", (function(_this) {
                return function() {
                    _this.closePopup();
                };
            }) (this));
        },

        setup: function(textareaId) {
            var elemTexta = document.getElementById(textareaId);
            var elemTools = document.createElement("ul");
            elemTools.className = "zform-toolbar hide-for-small";

            elemTexta.parentNode.insertBefore(elemTools, elemTexta);

            if (!this.isExecuted) {
                this.addEvent(document, "click", function(event) {
                    if (~event.target.className.indexOf("zform-button") && !(~event.target.className.indexOf("zform-subbutton"))) {
                        return event.stopPropagation();
                    }

                    var menus = document.getElementsByClassName("zform-popup"), i = 0;

                    while (menus[i]) {
                        if (menus[i].getAttribute("data-zform-info") !== "dontclose" || event.target.nodeName.toLowerCase() === "textarea") {
                            menus[i].style.display = "none";
                        }
                        i++;
                    }
                }, false);

                this.isExecuted = true;
            }

            var groups = this.buttons.split("#");
            var buttons;

            var elemButtonLi, elemButton, currentButton;
            var elemPopup;

            for (var g=0, cg=groups.length; g<cg; g++) {
                buttons = groups[g].split(",");

                for (var b=0, cb=buttons.length; b<cb; b++) {
                    if (!(currentButton = this.tags[buttons[b]])) {
                        alert("La valeur '" + buttons[b] + "' n\'est pas reconnue comme étant une valeur correcte pour un bouton de zForm ! Corrigez votre syntaxe.");
                        continue;
                    }

                    elemButtonLi = elemTools.appendChild(document.createElement("li"));
                    elemButton = elemButtonLi.appendChild(document.createElement("a"));
                    elemButton.style.position = "relative";

                    elemButton.className = "ico-after zform-button zform-button-" + buttons[b];
                    elemButton.setAttribute("data-zform-textarea", textareaId);
                    elemButton.title = currentButton.title;
                    elemButton.innerText = currentButton.title;

                    if (currentButton.action) {
                        elemButton.href = "#";
                        this.addEvent(elemButton, "click", function(event, elemPopup) {
                            event.preventDefault();

                            if (elemPopup = this.getElementsByTagName("div")[0]) {
                                elemPopup.style.display = "block";
                            }
                        });

                        elemPopup = elemButton.appendChild(document.createElement("div"));
                        elemPopup.className = "zform-popup";
                        elemPopup.style.position = "absolute";
                        elemPopup.style.display = "none";
                        elemPopup.style.left = "0";
                        elemPopup.style.width = "auto";
                        elemPopup.style.whiteSpace = "nowrap";
                        elemPopup.style.textAlign = "left";

                            elemPopup = this[currentButton.action](elemPopup, currentButton, textareaId);
                    } else {
                        elemButton.addEventListener("click", (function(_button, _textareaId, _this, _tagtype) {
                            return function() {
                                _this.wrap(_button.start, _button.end, _textareaId, _tagtype);
                            };
                        }) (currentButton, textareaId, this, buttons[b]), false);

                    }
                }

                elemButton.style.marginRight = "20px";
            }
        },

        openPopup: function(popupGuid) {
            this.closePopup();

            document.getElementById("zform-modal-overlay").style.display = "block";
            document.getElementById("zform-modal-wrapper").style.display = "block";

            document.getElementById("zform-modal-header").innerHTML = this.titles[popupGuid] || "Markdown";

            document.getElementById("zform-modal-" + popupGuid).style.display = "block";

            return false;
        },

        closePopup: function() {
            var modals = document.getElementsByTagName("section");

            for (var i=0, c=modals.length; i<c; i++) {
                if (modals[i].className === "zform-modal") {
                    modals[i].style.display = "none";
                }
            }

            document.getElementById("zform-modal-overlay").style.display = "none";
            document.getElementById("zform-modal-wrapper").style.display = "none";
        },

        validatePopup: function() {
            //var wrapper = document.getElementById("zform-modal-wrapper");

            if (this.selection && this.selection.type) {
                this.wrap("___", "+++", this.selection.textareaId, this.selection.type, null, true);
            }

            this.closePopup();
        },

        buildTitles: function(elemPopup, currentButton, textareaId, elemItem) {
            for (var i=1; i<=4; i++) {
                elemItem = elemPopup.appendChild(document.createElement("a"));
                elemItem.className = "ico-after zform-button zform-subbutton zform-button-title" + i;
                elemItem.title = "Titre de niveau " + i;
                elemItem.innerText = "Titre de niveau " + i;
                this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                    return function(event) {
                        event.preventDefault(); // IE madafaker
                        _this.wrap("", "", _textareaId, _options);
                    };
                }) (this, textareaId, "title" + i), false);
            }

            return elemPopup;
        },

        buildInfoblocks: function(elemPopup, currentButton, textareaId, elemItem) {
            var ids = ["information", "question", "attention", "error", "secret"];

            for (var i=0; i<5; i++) {
                elemItem = elemPopup.appendChild(document.createElement("a"));
                elemItem.className = "ico-after zform-button zform-subbutton zform-button-" + ids[i];
                elemItem.title = this.tags[ids[i]].title;
                elemItem.innerText = this.tags[ids[i]].title;
                this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                    return function(event) {
                        event.preventDefault(); // IE
                        _this.wrap("", "", _textareaId, _options);
                    };
                }) (this, textareaId, ids[i]), false);
            }

            return elemPopup;
        },

        buildCode: function(elemPopup, currentButton, textareaId) {
            var elemCol, elemItem, elemStg, i, c;

            for (var category in this.codes) {
                elemCol = elemPopup.appendChild(document.createElement("div"));
                elemCol.className = "zform-code-col";
                elemStg = elemCol.appendChild(document.createElement("b"));
                elemStg.style.display = "block";
                elemStg.style.fontWeight = "bold";
                elemStg.innerHTML = category;

                for (i=0, c=this.codes[category].length; i<c; i++) {
                    elemItem = elemCol.appendChild(document.createElement("span"));
                    elemItem.innerHTML = this.codes[category][i][1];

                    this.addEvent(elemItem, "mousedown", (function(_this, _textareaId, _options) {
                        return function(event) {
                            event.preventDefault();
                            _this.wrap("", "", _textareaId, "blockcode", _options);
                        };
                    }) (this, textareaId, this.codes[category][i][0]));
                }
            }

            return elemPopup;
        },

        wrap: function(startTag, endTag, textareaId, type, options, isFromPopup) {
            var field       = document.getElementById(textareaId);
            var scroll      = field.scrollTop;
            var selection   = (!isFromPopup) ? {
                before:     null,
                current:    null,
                after:      null,
                range:      null,
                startTag:   startTag,
                endTag:     endTag,
                textareaId: textareaId,
                type:       type,
                options:    options
            } : this.selection;

            field.focus();

            if (field.setSelectionRange) {
                if (!isFromPopup) {
                    selection.before    = field.value.substring(0, field.selectionStart);
                    selection.current   = field.value.substring(field.selectionStart, field.selectionEnd);
                    selection.after     = field.value.substring(field.selectionEnd);
                }

                field.blur();

                if (selection = this.tagType(selection, selection.type, selection.options, isFromPopup)) {
                    field.value = selection.before + selection.startTag + selection.current + selection.endTag + selection.after;
                    field.focus();
                    field.setSelectionRange(selection.before.length + selection.startTag.length, selection.before.length + selection.startTag.length + selection.current.length);
                }
            } else { // IE < 9 with IE-only stuff
                if (!isFromPopup) {
                    selection.range     = document.selection.createRange();
                    selection.current   = selection.range.text;
                }

                if (selection = this.tagType(selection, selection.type, selection.options, isFromPopup)) {
                    selection.range.text = selection.startTag + selection.current + selection.endTag;
                    selection.range.moveStart("character",  -selection.endTag.length - selection.current.length);
                    selection.range.moveEnd("character",    -selection.endTag.length);
                    selection.range.select();
                }
            }

            field.scrollTop = scroll;
        },

        tagType: function(selection, type, options, isFromPopup) {
            if (!type)
                return selection;

            this.selection = selection;

            var input = "", href, text, regex;

            function iterateRows(txt, char) {
                var spltd = txt.split("\n");
                var order = (char === 0);

                for (var i=0, c=spltd.length; i<c; i++) {
                    spltd[i] = ((order) ? ++char + "." : char) + " " + spltd[i];
                }

                return spltd.join("\n");
            }

            switch (type) {
                case "link":
                    if (isFromPopup) {
                        href = document.getElementById("zform-modal-link-href").value;
                        text = document.getElementById("zform-modal-link-text").value;

                        selection.current = "[" + text + "](" + href + ")";
                    } else {
                        regex = new RegExp("^(http[s]?:\\/\\/(www\\.)?|ftp:\\/\\/(www\\.)?|www\\.){1}([0-9A-Za-z-\\.@:%_+~#=]+)+((\\.[a-zA-Z]{2,3})+)(/(.)*)?(\\?(.)*)?");

                        if (regex.test(selection.current)){

                            document.getElementById("zform-modal-link-href").value = selection.current;
                            document.getElementById("zform-modal-link-text").value = "";
                            document.getElementById("zform-modal-link-text").focus();
                        } else {
                            document.getElementById("zform-modal-link-text").value = selection.current;
                            document.getElementById("zform-modal-link-href").value = "";
                            document.getElementById("zform-modal-link-href").focus();
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "image":
                    if (isFromPopup) {
                        var src   = document.getElementById("zform-modal-image-src").value;
                        text  = document.getElementById("zform-modal-image-text").value || "Image utilisateur";

                        selection.current = "![" + text + "](" + src + ")";
                    } else {
                        regex = new RegExp("^(http[s]?:\\/\\/(www\\.)?|ftp:\\/\\/(www\\.)?|www\\.){1}([0-9A-Za-z-\\.@:%_+~#=]+)+((\\.[a-zA-Z]{2,3})+)(/(.)*)?(\\?(.)*)?");

                        if (regex.test(selection.current)){
                            document.getElementById("zform-modal-image-src").value = selection.current;
                            document.getElementById("zform-modal-image-text").value = "";
                        } else {
                            document.getElementById("zform-modal-image-text").value = selection.current;
                            document.getElementById("zform-modal-image-src").value = "";
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "quote":
                    selection.current = iterateRows(selection.current, ">");
                    break;

                case "information":
                case "attention":
                case "question":
                case "secret":
                    selection.current = "[[" + type + "]]\n" + iterateRows(selection.current, "|");
                    break;

                case "error":
                    selection.current = "[[erreur]]\n" + iterateRows(selection.current, "|");
                    break;

                case "ul":
                    selection.current = iterateRows(selection.current, "-");
                    break;

                case "ol":
                    selection.current = iterateRows(selection.current, 0);
                    break;

                case "title1":
                case "title2":
                case "title3":
                case "title4":
                    for (var i=0, c=parseInt(type.charAt(5)); i<c; i++) {
                        input += "#";
                    }

                    selection.current = selection.current.replace(/^\s*?/, input + " ");
                    break;

                case "footnote":
                    if (!selection.current) return;

                    if (input = prompt("Entrez la signification de cette abréviation")) {
                        selection.after += "\n\n*[" + selection.current +"]: " + input;
                    }
                    break;

                case "abbr":
                    if (isFromPopup) {
                        var valtext = document.getElementById("zform-modal-abbr-text").value;
                        if (valtext.trim() === "") {
                            valtext = document.getElementById("zform-modal-abbr-abbr").value;
                        }
                        selection.after += "\n\n*[" + document.getElementById("zform-modal-abbr-abbr").value + "]: "+ valtext;
                    } else {
                        if (selection.current.length < 10) {
                            document.getElementById("zform-modal-abbr-abbr").value = selection.current;
                            document.getElementById("zform-modal-abbr-text").value = "";
                        } else {
                            document.getElementById("zform-modal-abbr-text").value = selection.current;
                            document.getElementById("zform-modal-abbr-abbr").value = "";
                        }

                        return this.openPopup(type);
                    }
                    break;

                case "blockcode":
                    selection.startTag = "```" + selection.options + ((selection.current.indexOf("\n") === 0) ? "" : "\n");
                    selection.endTag = "\n```";
                    break;
            }

            if (!selection.startTag)
                selection.startTag = "";

            if (!selection.endTag)
                selection.endTag = "";

            return selection;
        }
    };

    zForm.addEvent(window, "load", (function(_this) {
        return function() {
            _this.init();
        };
    }) (zForm));
})(window, document);


(function($, undefined){
    "use strict";

    $(".md-editor").on("keydown", function(e){
        // the message is submitted if the user is pressing Ctrl or Cmd with Enter and isn't pressing Alt or Shift
        if((e.ctrlKey || e.metaKey) && e.which === 13 && !e.altKey && !e.shiftKey){
            e.preventDefault();

            $(".message-submit > button[name=answer]").click();
        }
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Preview when editing news
   ========================================================================== */

(function($, undefined) {
    function updatePreview(data, element) {
        var $el = $(element);
        if(data.image) {
            $el.find(".featured-resource-illu").show().attr("src", data.image);
        }
        else {
            $el.find(".featured-resource-illu").hide();
        }

        $el.find("h3").text(data.title);
        $el.find(".featured-resource-description").html(data.description);
        $el.find("a").attr("href", data.link);
    }

    function buildDescription(authors, type) {
        var text = type;
        if(authors.length > 0)
            text += " par " + authors;
        return text;
    }

    $(".featured-resource-edit-form form input").on("change input", function() {
        updatePreview({
            image: $(".featured-resource-edit-form input[name=image_url]").val(),
            title: $(".featured-resource-edit-form input[name=title]").val(),
            description: buildDescription(
                $(".featured-resource-edit-form input[name=authors]").val(),
                $(".featured-resource-edit-form input[name=type]").val()
            ),
            link: $(".featured-edit-form input[name=url]").val(),
        }, $(".featured-resource-edit-form .featured-resource-item"));
    });
})(jQuery);


/* ===== Zeste de Savoir ====================================================
   Search for solved topics when create a new topic
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    var $solvedTopicsElem = $("main [data-solved-topics-url]");
    if($solvedTopicsElem.length > 0){
        //var solvedTopicsUrl = $solvedTopicsElem.attr("data-solved-topics-url");
        // TODO : le back fonctionne désormais
    }
})(jQuery);

/**
 * Used by recovering password and send again validation email functionality.
 */
(function($, undefined) {
    "use strict";

    if($("body").hasClass("form-email-username")) {
        var $emailInput = $("#id_email"),
            $emailForm = $("#form-email"),
            $emailButton = $("[data-form-email-username-button=email]");

        var $usernameInput = $("#id_username"),
            $usernameForm = $("#form-username"),
            $usernameButton = $("[data-form-email-username-button=username]");

        if ($emailInput.val() === "") {
            $emailForm.addClass("hidden");
        }
        else {
            $emailForm.removeClass("hidden");
        }

        $emailButton.on("click", function(e) {
            $emailForm.toggleClass("hidden");
            $usernameForm.addClass("hidden");

            $usernameInput.val("");

            e.preventDefault();
        });

        if ($usernameInput.val() === "") {
            $usernameForm.addClass("hidden");
        }
        else {
            $usernameForm.removeClass("hidden");
        }

        $usernameButton.on("click", function(e) {
            $usernameForm.toggleClass("hidden");
            $emailForm.addClass("hidden");

            $emailInput.val("");

            e.preventDefault();
        });
    }
})(jQuery);



/* ===== Zeste de Savoir ====================================================
   Gallery list and grid views management
   ---------------------------------
   Author: Sandhose / Quentin Gliech
   ========================================================================== */

(function($, undefined){
    "use strict";

    var $btn = $(".toggle-gallery-view"),
        $galleryView = $(".gallery");

    var updateBtn = function(){
        $btn.text($galleryView.hasClass("list-view") ? "Vue grille" : "Vue liste");
    };

    if($btn.length > 0){
        $btn.on("click", function(){
            if($galleryView.hasClass("list-view")) 
                $galleryView.removeClass("list-view").addClass("grid-view");
            else 
                $galleryView.removeClass("grid-view").addClass("list-view");
            updateBtn();
        });

        updateBtn();
    }

    var updateCheckbox = function(){
        if(this.checked) $(this).parents(".gallery-item").addClass("selected");
        else $(this).parents(".gallery-item").removeClass("selected");
    };

    if($galleryView.length > 0){
        $(".gallery-item input[type=checkbox]")
            .on("change", updateCheckbox)
            .each(updateCheckbox)
        ;
    }
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   jQuery :tabbable and :focusable selectors plugin
   ========================================================================== */

(function($){
  "use strict";

  $.extend($.expr[ ":" ], {
    data: $.expr.createPseudo ?
      $.expr.createPseudo(function(dataName){
        return function(elem){
          return !!$.data(elem, dataName);
        };
      }) :
      // support: jQuery <1.8
      function(elem, i, match){
        return !!$.data(elem, match[ 3 ]);
      },

    focusable: function(element){
      return focusable(element, !isNaN($.attr(element, "tabindex")));
    },

    tabbable: function(element){
      var tabIndex = $.attr(element, "tabindex"),
        isTabIndexNaN = isNaN(tabIndex);
      return ( isTabIndexNaN || tabIndex >= 0 ) && focusable(element, !isTabIndexNaN);
    }
  });

  /**
   * focussable function, taken from jQuery UI Core
   * @param element
   * @returns {*}
   */
  function focusable(element){
    var map, mapName, img,
      nodeName = element.nodeName.toLowerCase(),
      isTabIndexNotNaN = !isNaN($.attr(element, "tabindex"));
    if("area" === nodeName){
      map = element.parentNode;
      mapName = map.name;
      if(!element.href || !mapName || map.nodeName.toLowerCase() !== "map"){
        return false;
      }
      img = $("img[usemap=#" + mapName + "]")[0];
      return !!img && visible(img);
    }
    return ( /input|select|textarea|button|object/.test(nodeName) ?
      !element.disabled :
      "a" === nodeName ?
        element.href || isTabIndexNotNaN :
        isTabIndexNotNaN) &&
      // the element and all of its ancestors must be visible
      visible(element);

    function visible(element){
      return $.expr.filters.visible(element) && !$(element).parents().addBack().filter(function(){
        return $.css(this, "visibility") === "hidden";
      }).length;
    }
  }
})(jQuery);


/* ===== Zeste de Savoir ====================================================
   Keyboard navigation in navigables lists, with j/k keys
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined){
    "use strict";
    
    $(document).ready(function(){
        var $lists = $("#content .navigable-list");

        if($lists.length > 0){
            var $navigableElems = $lists.find(".navigable-elem");

            $("body").on("keydown", function(e){
                if(!$(document.activeElement).is(":input") && (e.which === 74 || e.which === 75)){
                    var $current = $lists.find(".navigable-elem.active"),
                        nextIndex = null;

                    if($current.length === 1){
                        var currentIndex = $navigableElems.index($current);
                        if(e.which === 75){ // J
                            if(currentIndex > 0)
                                nextIndex = currentIndex - 1;
                        } else { // K
                            if(currentIndex + 1 < $navigableElems.length)
                                nextIndex = currentIndex + 1;
                        }
                    } else {
                        nextIndex = 0;
                    }

                    if(nextIndex !== null){
                        $current.removeClass("active");
                        activeNavigableElem($navigableElems.eq(nextIndex));
                    }
                }
            });

            $("#content .navigable-list")
            .on("focus", ".navigable-link", function(){
                if(!$(this).parents(".navigable-elem:first").hasClass("active")){
                    $lists.find(".navigable-elem.active").removeClass("active");
                    activeNavigableElem($(this).parents(".navigable-elem"));
                }
            })
            .on("blur", ".navigable-link", function(){
                $(this).parents(".navigable-elem:first").removeClass("active");
            });
        }

        function activeNavigableElem($elem){
            $elem
                .addClass("active")
                .find(".navigable-link")
                    .focus();
        }

        $("#content").on("DOMNodeInserted", ".navigable-list, .navigable-elem", function(){
            $lists = $("#content .navigable-list");
        });
    });
})(document, jQuery);

/* ===== Zeste de Savoir ====================================================
   Ugly markdown help block management
   TEMP : Add this to the future awesome Markdown editor directly
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document ,$, undefined){
    "use strict";

    function addDocMD($elem){
        $elem.each(function(){
            var $help = $("<div/>", {
                "class": "markdown-help",
                "html": "<div class=\"markdown-help-more\">" +
                        "<p>Les simples retours à la ligne ne sont pas pris en compte. Pour créer un nouveau paragraphe, pensez à <em>sauter une ligne</em> !</p>" +
                        "<pre><code>**gras** \n*italique* \n[texte de lien](url du lien) \n> citation \n+ liste à puces </code></pre>" +
                        "<a href=\"//zestedesavoir.com/tutoriels/221/rediger-sur-zds/\">Voir la documentation complète du markdown</a>" +
                        "<p>Vous pouvez également <a href=\"//zestedesavoir.com/tutoriels/202/comment-rediger-des-maths-sur-zeste-de-savoir/\">écrire des formules mathématiques</a> en encadrant ces dernières du signe dollar ($) !</p></div>"+
                        "<a href=\"#open-markdown-help\" class=\"open-markdown-help btn btn-grey ico-after help\">"+
                            "<span class=\"close-markdown-help-text\">Masquer</span>" +
                            "<span class=\"open-markdown-help-text\">Afficher</span> l'aide Markdown" +
                        "</a>"
            });
            $(this).after($help);
            $(".open-markdown-help, .close-markdown-help", $help).click(function(e){
                $(".markdown-help-more", $help).toggleClass("show-markdown-help");
                e.preventDefault();
                e.stopPropagation();
            });
        });
    }
    

    $(document).ready(function(){
        addDocMD($(".md-editor"));
        $("#content").on("DOMNodeInserted", ".md-editor", function(e){
            var $editor = $(e.target);
            if($editor.next().hasClass("markdown-help") === false) {
                addDocMD($editor);
            }
        });
    });
})(document, jQuery);


/* ===== Zeste de Savoir ====================================================
   Toggle message content for staff
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    $("#content [href^=#show-message-hidden]").on("click", function(e){
        $(this).parents(".message:first").find(".message-hidden-content").toggle();
		e.preventDefault();
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Mobile sidebar menu, swipe open/close
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(window, document, $, undefined){
    "use strict";

    /**
     * Add class for mobile navigator does not support fixed position
     */
    var navU = navigator.userAgent;

    // Android Mobile
    var isAndroidMobile = navU.indexOf("Android") > -1 && navU.indexOf("Mozilla/5.0") > -1 && navU.indexOf("AppleWebKit") > -1;

    // Android Browser (not Chrome)
    var regExAppleWebKit = new RegExp(/AppleWebKit\/([\d.]+)/);
    var resultAppleWebKitRegEx = regExAppleWebKit.exec(navU);
    var appleWebKitVersion = (resultAppleWebKitRegEx === null ? null : parseFloat(regExAppleWebKit.exec(navU)[1]));
    var disableMobileMenu = isAndroidMobile && appleWebKitVersion !== null && appleWebKitVersion < 537;

    if(disableMobileMenu)
        $("html").removeClass("enable-mobile-menu");



    /**
     * Get prefix to support CSS transform
     */
    var transform = "";
    var prefixedPropertyNames = ["transform", "msTransform", "MozTransform", "WebkitTransform", "OTransform"];
    var prefixes = ["", "-ms-", "-moz-", "-webkit-", "-o-"];
    var tempDiv = document.createElement("div");
    for(var i = 0; i < prefixedPropertyNames.length; ++i){
        if(typeof tempDiv.style[prefixedPropertyNames[i]] !== "undefined"){
            transform = prefixes[i];
            break;
        }
    }
    transform = transform+"transform";



    /**
     * Manage mobile sidebar on resize
     */
    $(window).on("resize", function(){
        if(parseInt($("html").css("width")) < 960 && !disableMobileMenu){
            $(".page-container").css("width", $("html").css("width"));

            if(!$("#mobile-menu").hasClass("initialized")){
                $("#mobile-menu").addClass("initialized");


                /**
                 * Manage menu button
                 */
                $(".mobile-menu-btn").on("click", function(e){
                    if(!$("html").hasClass("show-mobile-menu")){
                        toggleMobileMenu(true);

                        e.preventDefault();
                        e.stopPropagation();
                    }
                });



                /**
                 * Build sidebar menu from page
                 */

                appendToSidebar($("#search"), true);
                appendToSidebar($(".logbox .my-account"), true);
                appendToSidebar($(".header-menu"));

                $(".page-container .mobile-menu-bloc .mobile-menu-bloc").each(function(){
                    appendToSidebar($(this));
                });
                $(".page-container .mobile-menu-bloc:not(.my-account-dropdown)").each(function(){
                    appendToSidebar($(this));
                });

                appendToSidebar($(".my-account-dropdown"));
            }


            /**
             * Manage touch events for mobile sidebar
             */
            if(!$("#mobile-menu").hasClass("initialized-events")){
                var beginTouchDown = 0;
                var borderWidth    = 50;
                var swipping       = false;

                $("body")
                .on("touchstart", function(e){
                    beginTouchDown = parseInt(e.originalEvent.touches[0].pageX, 10) - $(".page-container").offset().left;
                });

                $(".page-container")
                .on("touchmove", function(e){
                    if(swipping || parseInt(e.originalEvent.touches[0].pageX, 10) - $(this).offset().left < borderWidth){
                        e.preventDefault();
                        $("body:not(.swipping)").addClass("swipping");

                        swipping   = true;

                        var toMove = parseInt(e.originalEvent.touches[0].pageX, 10) - beginTouchDown;
                        toMove     = (toMove * 100) / parseInt($("html").width());

                        if(toMove > 0 && toMove < 90){
                            var props = {};
                            props[transform] = "translate3d("+toMove+"%, 0, 0)";
                            $(this).css(props);

                            toMove  = ((toMove * 20) / 90) - 20;
                            props[transform] = "translate3d("+toMove+"%, 0, 0)";
                            $("#mobile-menu").css(props);
                        }
                    }
                })
                .on("touchend touchleave touchcancel", function(){
                    if(swipping){
                        var offset  = parseInt($(this).offset().left);
                        var width   = parseInt($("html").width());
                        var visible = (offset > width/3 && !$("html").hasClass("show-mobile-menu")) || (offset > width-width/3 && $("html").hasClass("show-mobile-menu"));
                        toggleMobileMenu(visible);

                        swipping = false;
                        $("body").removeClass("swipping");

                        var props = {};
                        props[transform] = "";
                        $(".page-container, #mobile-menu").css(props);
                    }
                });


                $(".page-container").on("click", function(e){
                    if($("html").hasClass("show-mobile-menu")){
                        toggleMobileMenu(false);

                        e.preventDefault();
                        e.stopPropagation();
                    }
                });


                $("#mobile-menu").addClass("initialized-events");
            }
        } else {
            $("html").removeClass("show-mobile-menu");
            $("#mobile-menu").removeClass("initialized-events");
            $(".page-container").removeAttr("style");
            $(".page-container").off("click touchstart touchmove touchend");
        }
    });
    $(window).trigger("resize");



    function appendToSidebar($elem, force){
        if($elem.hasClass("mobile-menu-imported"))
            return;

        if(force){
            $elem.addClass("mobile-menu-imported");
            $elem.clone().removeAttr("id").appendTo("#mobile-menu");
            return;
        }

        var $div = $("<div/>");
        $div.addClass("mobile-menu-bloc");
        $div.attr("data-title", $elem.attr("data-title"));

        if($elem.hasClass("mobile-show-ico"))
            $div.addClass("mobile-show-ico");

        var $links = ($elem.hasClass("mobile-all-links")) ? $("a, button, span.disabled", $elem).not(".action-hover").addClass("mobile-menu-link") : $(".mobile-menu-link", $elem);

        $links.each(function(){
            if($(this).parents(".mobile-menu-imported, .modal").length === 0){
                var $elem = $(this).clone().addClass("light");
                var formId;

                if($(this).is("button")){
                    var $form = $(this).parents("form:first");
                    if(!$form.attr("id")){
                        formId = "form" + $(".identified-form").length;
                        $form.attr("id", formId).addClass("identified-form");
                    } else {
                        formId = $form.attr("id");
                    }
                    $elem.attr("form", formId);
                }

                $div.append($elem);
            }
        });

        $elem.addClass("mobile-menu-imported");

        $div.appendTo($("#mobile-menu"));
    }





    /**
     * Toggle sidebar for mobiles
     */
    function toggleMobileMenu(visible){
        var scrollTop;
        if(visible === null)
            visible = !$("html").hasClass("show-mobile-menu");

        $("body").removeClass("swipping");

        var viewportmeta = document.querySelector("meta[name=\"viewport\"]");

        if(visible){
            if(!$("html").hasClass("show-mobile-menu")){
                scrollTop = $(document).scrollTop();
                $(".page-container").css({
                    "margin-top": "-" + scrollTop + "px",
                    "padding-bottom": scrollTop + "px"
                });
                $("html").addClass("show-mobile-menu");

                viewportmeta.content = "width=device-width, minimum-scale=1.0, maximum-scale=1.0, initial-scale=1.0";
            }

            // Manage back button to close sidebar
            /*
            if(history && history.pushState){
                history.pushState(null, document.title, this.href);

                $(window).off("popstate").one("popstate", function(e){
                    if($("html").hasClass("show-mobile-menu"))
                        toggleMobileMenu(false);
                    else
                        window.history.back();
                });
            }
            */
        } else {
            $("html").removeClass("show-mobile-menu");

            // Reset CSS modifications for restore scroll
            scrollTop = parseInt($(".page-container").css("padding-bottom"));
            $(".page-container").css({
                "margin-top": "",
                "padding-bottom": ""
            });
            if(scrollTop > 0)
                $(document).scrollTop(scrollTop);

            // Stop swipping
            $("body").removeClass("swipping");

            setTimeout(function(){
                // Reinit mobile menu at top
                $("#mobile-menu").scrollTop(0);

                // Restore zoom
                viewportmeta.content = "width=device-width, minimum-scale=1.0, initial-scale=1.0";

                // Bugfix <html> element
                $("html").css({
                    "position": "absolute",
                    "left": "0"
                });
                setTimeout(function(){
                    $("html").removeAttr("style");
                }, 500);
            }, 200);
        }
    }




    /**
     * Manage actions buttons, move them at the top af core of page
     */
    $(window).on("resize", function(){
        if(parseInt($("html").css("width")) < 960 && !disableMobileMenu){
            var $newBtns = $(".sidebar .new-btn:not(.mobile-btn-imported)");
            if($newBtns.length > 0){
                var $prevElem = $("#content")
                    .find("> .content-wrapper, > .full-content-wrapper, > .content-col-2")
                    .first()
                    .find("h1, h2")
                    .first();
                if($prevElem.next(".license").length > 0)
                    $prevElem = $prevElem.next(".license");
                if($prevElem.next(".subtitle").length > 0)
                    $prevElem = $prevElem.next(".subtitle");
                if($prevElem.next(".taglist").length > 0)
                    $prevElem = $prevElem.next(".taglist");

                var $newBtnContainer = $("<div/>", {
                    "class": "new-btn-container"
                });
                $newBtns.each(function(){
                    $newBtnContainer.append($(this).clone().removeAttr("id").removeClass("blue"));
                    $(this).addClass("mobile-btn-imported");
                });
                $prevElem.after($newBtnContainer);
            }
        }
    });
    $(window).trigger("resize");
})(window, document, jQuery);


/* ===== Zeste de Savoir ====================================================
   Manage modals boxes
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined){
    "use strict";
    
    var $overlay = $("<div/>", {
        "id": "modals-overlay"
    }).on("click", function(e){
        closeModal();
        e.preventDefault();
        e.stopPropagation();
    });

    var $modals = $("<div/>", { "id": "modals" });
    $("body").append($modals);
    $modals.append($overlay);

    function buildModals($elems){
        $elems.each(function(){
            $modals.append($(this).addClass("tab-modalize"));
            $(this).append($("<a/>", {
                class: "btn btn-cancel " + ($(this).is("[data-modal-close]") ? "btn-modal-fullwidth" : ""),
                href: "#close-modal",
                text: $(this).is("[data-modal-close]") ? $(this).attr("data-modal-close") : "Annuler",
                click: function(e){
                    closeModal();
                    e.preventDefault();
                    e.stopPropagation();
                }
            }));
            var $link = $("[href=#"+$(this).attr("id")+"]:first");
            var linkIco = $link.hasClass("ico-after") ? " light " + $link.attr("class").replace(/btn[a-z-]*/g, "") : "";
            $(this).prepend($("<span/>", {
                class: "modal-title" + linkIco,
                text: $link.text()
            }));
        });
    }

    $("body").on("click", ".open-modal", function(e){
        $overlay.show();
        $($(this).attr("href")).show(0, function(){
            $(this).find("input:visible, select, textarea").first().focus();
        });
        if(!$("html").hasClass("enable-mobile-menu"))
            $("html").addClass("dropdown-active");

        e.preventDefault();
        e.stopPropagation();
    });

    $("body").on("keydown", function(e){
        // Escape close modal
        if($(".modal:visible", $modals).length > 0 && e.which === 27){
            closeModal();
            e.stopPropagation();
        }
    });

    function closeModal(){
        $(".modal:visible", $modals).fadeOut(150);
        $overlay.fadeOut(150);
        $("html").removeClass("dropdown-active");
    }


    $(document).ready(function(){
        buildModals($(".modal"));
        $("#content").on("DOMNodeInserted", ".modal", function(e){
            buildModals($(e.target));
        });
    });
})(document, jQuery);

/* ===== Zeste de Savoir ====================================================
   Auto submit forms
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    $("body").on("change", ".select-autosubmit", function() {
        $(this).parents("form:first").submit();
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Toggle spoiler content
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, $, undefined) {
    "use strict";

    function buildSpoilers($elem) {
        $elem.each(function() {
            $(this).addClass("spoiler-build");
            $(this).before($("<a/>", {
                text: "Afficher/Masquer le contenu masqué",
                class: "spoiler-title ico-after view",
                href: "#",
                click: function(e) {
                    $(this).next(".spoiler").toggle();
                    e.preventDefault();
                }
            }));
        });
    }

    $(document).ready(function() {
        var $content = $("#content");
        buildSpoilers($content.find(".spoiler"));
        $content.on("DOMNodeInserted", function() {
            var $spoilers = $(this).find(".spoiler:not(.spoiler-build)");
            if ($spoilers.length > 0)
                return buildSpoilers($spoilers);
            else if ($(this).is(".spoiler:not(.spoiler-build)"))
                return buildSpoilers($(this));
        });
    });
})(document, jQuery);

/* ===== Zeste de Savoir ====================================================
   Prevent from double clic on submit buttons
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    var buttonsSelector = "[type=submit], [type=reset]",
        $lastButtonClicked = null;

    $("body").on("submit", "form", function(){
        $(buttonsSelector)
            .addClass("disabled");

        if($lastButtonClicked === null)
            $lastButtonClicked = $(buttonsSelector, $(this));

        $lastButtonClicked
            .addClass("submitted")
            .append($("<span/>", { class: "line-loading" }));
    });
    $("form").on("click", buttonsSelector, function(e){
        $lastButtonClicked = $(this);

        if($(this).hasClass("disabled"))
            e.preventDefault();
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Keyboad accessibility for overlayed boxes (modals, etc)
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";
    
    $("body").on("keydown", function(e){
        var $modal = $(".tab-modalize:visible");
        if($modal.length > 0){
            // Tab do not go out modal
            if(e.which === 9){
                var $current = $modal.find(":focus"),
                    $tabbables = $modal.find(":tabbable"),
                    nextIndex = e.shiftKey ? $tabbables.length - 1 : 0;

                if($current.length === 1){
                    var currentIndex = $tabbables.index($current);
                    if(e.shiftKey){
                        if(currentIndex > 0)
                            nextIndex = currentIndex - 1;
                    } else {
                        if(currentIndex + 1 < $tabbables.length)
                            nextIndex = currentIndex + 1;
                    }
                }

                $tabbables.eq(nextIndex).focus();
                e.stopPropagation();
                e.preventDefault();
            }
        }
    });
})(jQuery);

/* ===== Zeste de Savoir ====================================================
   Zen mode for content-pages
   ---------------------------------
   Author: Alex-D / Alexandre Demode
   ========================================================================== */

(function($, undefined){
    "use strict";

    if($(".open-zen-mode").length > 0){
        $(".open-zen-mode").on("click", function(e){
                var Text = $(".open-zen-mode").text();
                var TextToPut = $(".open-zen-mode").attr("data-content-on-click");
                $(".open-zen-mode").attr("data-content-on-click", Text);
                $(".open-zen-mode").text(TextToPut);

                if(typeof sessionStorage !== "undefined"){
                    if($(".content-container").hasClass("zen-mode")){
                        if("zenMode" in sessionStorage){
                            sessionStorage.setItem("zenMode", "false");
                        }
                    }
                    else{
                        sessionStorage.setItem("zenMode", "true");
                    }
                }

                $(".content-container").toggleClass("zen-mode tab-modalize");
                $(this).blur();
                e.preventDefault();
                e.stopPropagation();
            }
        );

        $("body").on("keydown", function(e){
            // Escape close modal
            if($(".zen-mode").length > 0 && e.which === 27){
                var Text = $(".open-zen-mode").text();
                var TextToPut = $(".open-zen-mode").attr("data-content-on-click");
                $(".open-zen-mode").attr("data-content-on-click", Text);
                $(".open-zen-mode").text(TextToPut);

                if(typeof sessionStorage !== "undefined"){
                    if("zenMode" in sessionStorage){
                        sessionStorage.setItem("zenMode", "false");
                    }
                }

                $(".content-container").toggleClass("zen-mode tab-modalize");
                $(this).blur();
                e.stopPropagation();
            }
        });

        if(typeof sessionStorage !== "undefined"){
            if("zenMode" in sessionStorage){
                if(sessionStorage.getItem("zenMode") === "true"){
                    $(".open-zen-mode").click();
                }
            }
        }
    }
})(jQuery);