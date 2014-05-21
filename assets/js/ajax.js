function vote(id_post)
{
    $("#upvote"+id_post).click(function(e){
        var lien = $(this).attr('href');
        $('#cptup'+id_post).fadeOut('fast', function(){
            $('#cptup'+id_post).load(lien, function(data) {
                var json = $.parseJSON(data);
                if ($('#upvote'+id_post).hasClass('upvote')) {
                    $('#upvote'+id_post).removeClass('upvote');
                }
                else {
                    $('#upvote'+id_post).addClass('upvote');
                    if ($('#downvote'+id_post).hasClass('downvote')) {
                        $('#downvote'+id_post).removeClass('downvote');
                    }
                }
                if (parseInt(json["upvotes"])>parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up-voted.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down.png' %}");
                }
                if (parseInt(json["upvotes"])<parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down-voted.png' %}");
                }
                if (parseInt(json["upvotes"])== parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down.png' %}");
                }

                $('#cptdown'+id_post).fadeOut('fast');
                $('#cptup'+id_post).html("+"+json["upvotes"])
                $('#cptdown'+id_post).html("-"+json["downvotes"])
                $('#cptup'+id_post).fadeIn('fast');
                $('#cptdown'+id_post).fadeIn('fast');
            });
        });
        e.preventDefault()
    });
    $("#downvote"+id_post).click(function(e){
        var lien = $(this).attr('href');
        $('#cptdown'+id_post).fadeOut('fast', function(){
            $('#cptdown'+id_post).load(lien, function(data) {
                var json = $.parseJSON(data);
                if ($('#downvote'+id_post).hasClass('downvote')) {
                    $('#downvote'+id_post).removeClass('downvote');
                }
                else {
                    $('#downvote'+id_post).addClass('downvote');
                    if ($('#upvote'+id_post).hasClass('upvote')) {
                        $('#upvote'+id_post).removeClass('upvote');
                    }
                }

                if (parseInt(json["upvotes"])>parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up-voted.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down.png' %}");
                }
                if (parseInt(json["upvotes"])<parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down-voted.png' %}");
                }
                if (parseInt(json["upvotes"])==parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src","{% static 'img/thumb-up.png' %}");
                    $("#downvote"+id_post).children("img").attr("src","{% static 'img/thumb-down.png' %}");
                }

                $('#cptup'+id_post).fadeOut('fast');
                $('#cptup'+id_post).html("+"+json["upvotes"])
                $('#cptdown'+id_post).html("-"+json["downvotes"])
                $('#cptdown'+id_post).fadeIn('fast');
                $('#cptup'+id_post).fadeIn('fast');
            });
        });
        e.preventDefault()
    });
}