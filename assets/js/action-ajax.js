/* ===== Zeste de Savoir ====================================================
   Manage action button AJAX requests
   ========================================================================== */

(function($, undefined){
    "use strict";

    $(".sidebar").on("click", ".follow", function(e){
        var $act = $(this),
            $form = $(this).parents("form:first"),
            $email = $(this).parents("li:first").next().find(".email");

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
                    $act.removeClass("blue").addClass("yellow").text("Ne plus suivre ce sujet");
                    $form.find("input[name=follow]").val(1);
                } else {
                    $act.removeClass("yellow").addClass("blue").text("Suivre ce sujet");
                    $email.removeClass("blue").text("Être notifié par courriel");
                    $form.find("input[name=follow]").val(0);
                    $email.parents("form:first").find("input[name=email]").val(0);
                }
            }
        });

        e.stopPropagation();
        e.preventDefault();
    });
    $(".sidebar").on("click", ".email", function(e){
        var $act = $(this),
            $follow = $(this).parents("li:first").prev().find(".follow"),
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
                    $act.addClass("blue").text("Ne plus être notifié par courriel");
                    $follow.removeClass("blue").addClass("yellow").text("Ne plus suivre ce sujet");
                    $form.find("input[name=email]").val(1);
                    $follow.parents("form:first").find("input[name=follow]").val(1);
                } else {
                    $act.removeClass("blue").text("Être notifié par courriel");
                    $form.find("input[name=email]").val(0);
                }
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });
    $(".sidebar").on("click", ".solve", function(e){
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
                    $act.removeClass("green").addClass("blue").text("Marquer comme non résolu");
                    $form.find("input[name=solved]").val(1);
                    $(".alert-box").removeClass("empty", 1000);
                } else {
                    $act.removeClass("blue").addClass("green").text("Marquer comme résolu");
                    $form.find("input[name=solved]").val(0);
                    $(".alert-box").addClass("empty", 1000);
                }
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });

    $(".message-actions").on("click", ".cite", function(e){
        var $act = $(this),
            $editor = $(".md-editor");

        $.ajax({
            url: $act.attr("href"),
            dataType: "json",
            success: function(data){
                $editor.val($editor.val() + data.text + "\n\n\n");
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });
    $(".message-bottom").on("click", ".btn-grey", function(e){
        var $form = $(this).parents("form:first");
        var csrfmiddlewaretoken = $form.find("input[name=csrfmiddlewaretoken]").val(),
            text = $form.find("textarea[name=text]").val(),
            lastPost = $form.find("input[name=last_post]").val();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            dataType: "json",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "text": text,
                "last_post": lastPost,
                "preview": "Apercu"
            },
            success: function(data){
                $(".previsualisation").remove();
                var $prev = $("<div class='previsualisation content-wrapper'> <h3 class='reactions-title'>Prévisualisation de votre message</h3><div class='message-content'>"+data.text+"</div></div>");
                $prev.insertAfter($form);
            }
        });
        e.stopPropagation();
        e.preventDefault();
    });
})(jQuery);
