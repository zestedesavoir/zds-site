/* ===== Zeste de Savoir ====================================================
    Nom du fichier   : author_stats.js
    Description      : Script JS pour supprimer les statistiques des quizzs par l'auteur ou staff
    Auteur           : Atman BOZ
   ========================================================================== */


$('.quizz_name').each(function () {
    var quizzName = $(this).text();
    quizzName = quizzName.replace("#", "");
    var parts = quizzName.split("/");
    var statsPart = parts[parts.length - 2] + "/" + parts[parts.length - 1];
    $(this).text(statsPart);
});


$(document).ready(function () {
    // Add an event listener to the quizz delete button
    $(".delete-quizz-button").click(function () {
        var quizzName = $(this).attr('data-quizz');
        deleteQuizz(quizzName, '');
    });

    // Add an event listener to the question delete button
    $(".delete-question-button").click(function () {
        var quizzName = $(this).attr('data-quizz');
        var question = $(this).attr('data-question');
        deleteQuizz(quizzName, question);
    });

});

function deleteQuizz(quizzName, question) {
    const csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val();
    $.ajax({
        url: '/contenus/delete_quizz/',
        type: 'POST',
        data: question ? JSON.stringify({ 'quizzName': quizzName, 'question': question }) : JSON.stringify({ 'quizzName': quizzName }),
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfmiddlewaretoken
        },
        success: function (response) {
            location.reload();
        }
    });
}
