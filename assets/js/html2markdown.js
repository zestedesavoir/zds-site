/* ===== Zeste de Savoir ====================================================
   Parse HTML to Markdown
   ---------------------------------
   Author: A-312
   ========================================================================== */

(function(window, $, undefined) {
	"use strict";

	window.html2markdown = function(aParam) {
		var abbr = {},
			footer = "";

		var html2Text = function(element) {
			var text = $(element).text();
			var repaceWithTextNode = function(string, oldChild) {
				var child = (oldChild || element);
				child.parentNode.replaceChild(document.createTextNode(string), child);
			};
			var html2MD = function(obj) {
				return $(recursiveWalk(obj)).text();
			};
			//console.log("-->", element.nodeName, $(element).html());
			if (element.nodeName === "BR") {
				repaceWithTextNode("  ");
			}
			//bold
			else if (element.nodeName === "STRONG") {
				repaceWithTextNode("**" + html2MD(element) + "**");
			}
			//italic
			else if (element.nodeName === "EM") {
				repaceWithTextNode("*" + html2MD(element) + "*");
			}
			//strike
			else if (element.nodeName === "DEL") {
				repaceWithTextNode("~~" + html2MD(element) + "~~");
			}
			//sup
			else if (element.nodeName === "SUP") {
				repaceWithTextNode("^" + html2MD(element) + "^");
			}
			//sub
			else if (element.nodeName === "SUB") {
				repaceWithTextNode("~" + html2MD(element) + "~");
			}
			//abbr & footnote
			else if (element.nodeName === "ABBR") {
				repaceWithTextNode(text);
				abbr[text] = element.title;
			}
			//key
			else if (element.nodeName === "KBD") {
				repaceWithTextNode("||" + text + "||");
			}
			//titles h1, h2, h3, h4
			else if (element.nodeName[0] === "H" && /^H[3-6]$/.test(element.nodeName)) {
				repaceWithTextNode("\n" + new Array(element.nodeName[1] - 1).join("#") + " " + html2MD(element));
			}
			//ul & ol
			else if (element.nodeName === "LI") {
				if (!$(this).data("num") && $(element).parent()[0].nodeName === "OL") {
					$(element).parent().children().each(function() {
						$(this).data("num", ($(this).index() + 1) + ". ");
					});
				}
				repaceWithTextNode(($(element).data("num") || "- ") + html2MD(element));
			}
			//center & right
			else if (element.nodeName === "DIV" && $(element).attr("align")) {
				text = html2MD(element);
				text = text.replace(/^\s*(.*?)\s*$/, "$1") || text;
				if ($(element).attr("align") === "center") {
					repaceWithTextNode("\n-> " + text + " <-");
				} else if ($(element).attr("align") === "right") {
					repaceWithTextNode("\n-> " + text + " ->");
				} else {
					return false;
				}
			}
			//quote
			else if (element.nodeName === "FIGURE" && $(element).children("blockquote")[0]) {
				var $blockquote = $(element).children("blockquote");

				recursiveWalk($blockquote);

				text = $blockquote.children("p").text().replace(/( {2})?\n/g, "  \n> ");
				text += "\nSource:" + html2MD($(element).children("figcaption")).replace(/^\n/, "");

				repaceWithTextNode(text);
			}
			//image
			else if (element.nodeName === "FIGURE" && $(element).children("img")[0]) {
				var src = $(element).children("img").attr("src"),
					title = $(element).children("figcaption").text();
				repaceWithTextNode("![" + title + "](" + src + ")");
			}
			//inline image & smiley
			else if (element.nodeName === "IMG") {
				if ($(element).attr("src").indexOf("/static/smileys") === 0)
					repaceWithTextNode(element.alt);
				else
					repaceWithTextNode("![" + element.alt + "](" + $(element).attr("src") + ")");
			}
			//link
			else if (element.nodeName === "A") {
				text = html2MD(element);
				if ($(element).hasClass("spoiler-title")) {
					repaceWithTextNode(""); // remove "Afficher/Masquer le contenu masqué"
				} else if (text.indexOf("http") === 0) {
					repaceWithTextNode($(element).attr("href"));
				} else {
					repaceWithTextNode("[" + text + "](" + $(element).attr("href") + ")");
				}
			}
			//table
			/* ... */
			else if (element.nodeName === "DIV" && $(element).is(".information, .question, .warning, .error, .spoiler")) {
				var makeBlock = function(type) {
					var text = "";
					for (var i = 0, t = ""; i < $(element).children("p").length; i++) {
						t = html2MD($(element).children("p").get(i));
						if (i === 0)
							t = t.replace(/^\n/, "| "); //delete the start new line.
						t = t.replace(/( {2})?\n/g, "  \n| ");
						text += t;
					}
					repaceWithTextNode("\n[[" + type + "]]\n" + text);
				};
				//information
				if ($(element).hasClass("information")) {
					makeBlock("information");
				}
				//question
				else if ($(element).hasClass("question")) {
					makeBlock("question");
				}
				//attention
				else if ($(element).hasClass("warning")) {
					makeBlock("attention");
				}
				//error
				else if ($(element).hasClass("error")) {
					makeBlock("erreur");
				}
				//secret
				else if ($(element).hasClass("spoiler")) {
					makeBlock("secret"); // see A (remove "Afficher/Masquer le contenu masqué")
				} else {
					return false;
				}
			}
			//monospace
			else if (element.nodeName === "CODE") {
				repaceWithTextNode("`" + text + "`");
			}
			//blockcode
			else if (element.nodeName === "TABLE" && $(element).hasClass("codehilitetable")) {
				text = $(element).find("td.code pre").text();
				if (text.split("\n").length <= 2)
					repaceWithTextNode("\n    " + text.replace(/\n$/, ""));
				else
					repaceWithTextNode("\n```\n" + text + "```");
			}
			//math
			else if (element.nodeName === "MATHJAX") {
				text = $(element).children("script[type='math/tex']").text();
				repaceWithTextNode("$" + text + "$");
			}
			//iframe
			else if (element.nodeName === "FIGURE" && $(element).children("iframe")[0]) {
				text = html2MD($("<div></div>").append($(element).children("iframe")));
				text += "\nVideo:" + html2MD($(element).children("figcaption")).replace(/^\n/, "");

				repaceWithTextNode(text);
			}
			//inline iframe
			else if (element.nodeName === "IFRAME") {
				var embeds = [
					/^https?:\/\/www\.dailymotion\.com\/embed\/video\/(.+)$/,
					/^https?:\/\/www\.metacafe\.com\/embed\/(.+)\/$/,
					/^https?:\/\/www\.veoh\.com\/videodetails2\.swf\?.*permalinkId\=(.+)$/,
					/^https?:\/\/player\.vimeo\.com\/video\/(.+)$/,
					/^https?:\/\/screen\.yahoo\.com\/(.+)\/?/, // don't add $
					/^https?:\/\/www\.youtube\.com\/embed\/(.+)$/,
					/^https?:\/\/jsfiddle\.net\/(.*)\/(.*)\// // don't add $
				];
				var urls = [
					"http://www.dailymotion.com/video/$1",
					"http://www.metacafe.com/watch/$1/",
					"http://www.veoh.com/watch/$1",
					"http://vimeo.com/$1",
					"http://screen.yahoo.com/$1",
					"http://youtu.be/$1",
					"http://jsfiddle.net/$1/$2/" // don't add $
				];
				text = $(element).attr("src");
				for (var i = 0; i < embeds.length; i++) {
					if (embeds[i].test(text)) {
						repaceWithTextNode("\n!(" + text.replace(embeds[i], urls[i]) + ")");
						break;
					}
				}
			}
			//hr
			else if (element.nodeName === "HR") {
				repaceWithTextNode("\n\n------\n\n");
			}
			//other
			else {
				return false;
			}
			return true;
		};

		var $message = (aParam instanceof jQuery) ? aParam : $("<div></div>").append(aParam),
			element, text,
			boolstisP = !!($message.children(":first").is("p"));

		$message.find("p").prepend("\n");

		var recursiveWalk = function(element) {
			if ($(element).children()[0]) {
				$(element).children().each(function() {
					if (html2Text(this))
						return;
					else
						recursiveWalk(this);
				});
			}

			return element;
		};

		while ($message[0].children.length > 0 && $message[0].children[0]) {
			element = $message[0].children[0];
			if (!html2Text(element)) {
				if ($(element).children()[0]) {
					recursiveWalk(element);
				}
				element.parentNode.replaceChild(document.createTextNode($(element).text()), element);
			}
		}

		$.each(abbr, function(word, title) {
			footer += "\n\n*[" + word + "]: " + title;
		});

		text = $message.text();
		if (boolstisP) //remove first new line
			text = text.replace(/^\n/, "");
		text = text.replace(/\n( +)\n/g, "\n\n");

		return text + footer;
	};
})(window, jQuery);