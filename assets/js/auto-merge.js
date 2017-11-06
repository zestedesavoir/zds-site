(function ($, undefined) {
    "use strict";

    $(document).ready(function () {

        /**
         * Sets up the merge interface (using codemirror) in the $div Object.
         * Data is generally retrieved from a form field or an aditionnal
         * div exposing the old data,also generated in the form.
         * @param {Object} $div - The base object used to set up the interface. Generally created in forms files.
         * @param {Object} $left - The object from which we will pick the content to put in the left hand side (lhs) of the editor.
         * @param {Object} $right - The object from which we will pick the content to put in the right hand side (rhs) of the editor.
         */
        function mergeUISetUp(selector, $left, $right){
            var target = document.getElementsByClassName(selector)[0]; // TODO remplacer par ID ou objet
            if (target) {
                target.innerHTML = "";
                 var merge = window.CodeMirror.MergeView(target, {
                   value: $left.html(),
                   orig: $right.html(),
                   lineNumbers: true,
                   highlightDifferences: true,
                   connect: "align",
                   collapseIdentical: true
                 });
                 return merge;
            }
        }

        var mergeInterfaceList = {};
        mergeInterfaceList.introduction = mergeUISetUp("compare-introduction",$("#your_introduction"),$("#id_introduction"));
        mergeInterfaceList.conclusion = mergeUISetUp("compare-conclusion",$("#your_conclusion"),$("#id_conclusion"));
        mergeInterfaceList.text = mergeUISetUp("compare-text",$("#your_text"),$("#id_text"));

        $(".CodeMirror-merge-editor").append("Votre Version");
        $(".CodeMirror-merge-right").append("La version courante");

        /**
         * Merge content
         */
        $(".merge-btn").on("click", function(e){
            e.stopPropagation();
            e.preventDefault();
            var button = $(this);

            Array.from(this.classList).forEach(function(element){
                if (element.indexOf("need-to-merge-") >= 0) {
                    var substring = element.substring(14);
                    var toMerge = mergeInterfaceList[substring].editor().getValue();
                    $("#id_" + substring).text(toMerge);

                    // Confirmation message
                    var msg = "<div class='alert-box success alert-merge'>" +
                                    "<span>Le contenu a bien été validé.</span>" +
                                    "<a href='#close-alert-box' class='close-alert-box ico-after cross white'>Masquer l'alerte</a>" +
                               "</div>";
                    button.before(msg);
                    setTimeout(function() {
                        $(".alert-merge").fadeOut("fast");
                    }, 2000);
                }
            });
        });
    });
})(jQuery);
