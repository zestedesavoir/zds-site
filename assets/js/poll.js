(function($, undefined) {
    "use strict";

    $("#add-form-choice").on("click", function() {
        var total_forms_input = $('#id_choices-TOTAL_FORMS');
        var count = parseInt(total_forms_input.val());
        var choice_form_template = $('#form-choice-template').html();
        var compiled_choice_form_template = choice_form_template.replace(/__prefix__/g, count);
        $('div#forms-choice').append(compiled_choice_form_template);
        total_forms_input.val(count+1);
    });

})(jQuery);