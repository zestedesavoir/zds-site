function vote(id_post, tb_up, tb_up_vote, tb_down, tb_down_vote)
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
                    $("#upvote"+id_post).children("img").attr("src",tb_up_vote);
                    $("#downvote"+id_post).children("img").attr("src",tb_down);
                }
                if (parseInt(json["upvotes"])<parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src",tb_up);
                    $("#downvote"+id_post).children("img").attr("src",tb_down_vote);
                }
                if (parseInt(json["upvotes"])== parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src",tb_up);
                    $("#downvote"+id_post).children("img").attr("src",tb_down);
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
                    $("#upvote"+id_post).children("img").attr("src",tb_up_vote);
                    $("#downvote"+id_post).children("img").attr("src",tb_down);
                }
                if (parseInt(json["upvotes"])<parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src",tb_up);
                    $("#downvote"+id_post).children("img").attr("src",tb_down_vote);
                }
                if (parseInt(json["upvotes"])== parseInt(json["downvotes"])) {
                    $("#upvote"+id_post).children("img").attr("src",tb_up);
                    $("#downvote"+id_post).children("img").attr("src",tb_down);
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