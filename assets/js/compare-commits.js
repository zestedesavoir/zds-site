/*
 * Allow the user to compare two commits
 */

(function(document, $, undefined){
    "use strict";

    function toogleRadioInput($radioInput){
        var $row = $radioInput.parent().parent();

        if($radioInput.attr("name") === "compare-from") {
            $row.prevAll().find("[name='compare-to']").prop("disabled", false);
            $row.nextAll().find("[name='compare-to']").prop("disabled", true);
            $row.find("[name='compare-to']").prop("disabled", true);
        }
        else {
            $row.prevAll().find("[name='compare-from']").prop("disabled", true);
            $row.nextAll().find("[name='compare-from']").prop("disabled", false);
            $row.find("[name='compare-from']").prop("disabled", true);
        }
    }

    $(".commits-list input[name^='compare']").on("change", function(){
        toogleRadioInput($(this));
    });

    $(document).ready(function(){
        $(".commits-list input[name^='compare']:checked").each(function(){
            toogleRadioInput($(this));
        });
    });

    $(".commits-compare-form").on("submit", function(){
        var $form = $(this),
            $fromInput = $form.find("input[name='from']"),
            $toInput = $form.find("input[name='to']"),
            compareFrom = $(".commits-list input[name='compare-from']:checked").val(),
            compareTo = $(".commits-list input[name='compare-to']:checked").val();

        $fromInput.val(compareFrom);
        $toInput.val(compareTo);
    });
})(document, jQuery);
