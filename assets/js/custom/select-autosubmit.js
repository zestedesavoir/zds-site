$(".select-autosubmit").change(function() {
    $(this).parents('form:first').submit();
});
