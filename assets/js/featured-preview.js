/* ===== Zeste de Savoir ====================================================
   Preview when editing news
   ========================================================================== */

(function($, undefined) {
    function updatePreview(data, element) {
        console.log(data);
        var $el = $(element);
        if(data.image) {
            $el.find(".featured-illu").attr("src", data.image);
        }
        if(data.title) {
            $el.find("h3").text(data.title);
        }
        if(data.description) {
            $el.find(".featured-description").html(data.description);
        }
        if(data.link) {
            $el.find("a").attr("href", data.link);
        }
    }

    function buildDescription(_authors, type) {
        var authors = _authors.split(",");
        authors = $.map(authors, $.trim);

        var text = "Un " + type + " par ";
        $.each(authors, function(index, author) {
            text += "<i>" + author + "</i>";
            if(index === authors.length - 2) {
                text += " et ";
            } else if(index !== authors.length - 1) {
                text += ", ";
            }
        });
        return text;
    }

    $(".featured-edit-form form input").on("change", function() {
        updatePreview({
            image: $(".featured-edit-form input[name=image_url]").val(),
            title: $(".featured-edit-form input[name=title]").val(),
            description: buildDescription(
                $(".featured-edit-form input[name=authors]").val(),
                $(".featured-edit-form input[name=type]").val()
            ),
            link: $(".featured-edit-form input[name=url]").val(),
        }, $(".featured-edit-form .featured-item"));
    });
})(jQuery);
