(function($, undefined){
    var categorySelect = $("#categorySelect");
    var verbSelect = $("#verbSelect");
    var tagSelect = $("#tagSelect");
    var url = "/api/contenus/verbs/";
    var itemUrl = "/api/contenus/items/";
    var listOfContentContainer = $("#contentList");

    var appendCategory = function (url) {
        if(categorySelect.val() === ""){
            return url;
        }
        else{
            return url + "?category=" + categorySelect.val();
        }
    };
    var appendVerb = function (url) {
        if(verbSelect.val() === ""){
            return url;
        }
        else{
            return (url.indexOf("?") > -1? url + "&verb=":url + "?verb=") + verbSelect.val();
        }
    };
    var getTagQueryString = function(){
        var $tagList = verbSelect.find(".active");
        var labelList = [];
        $tagList.each(function(){
            labelList.push($(this).attr("data-tag-label"));
        });
        return labelList.join(",");

    }
    var appendTags = function(url){
        var $tagList = verbSelect.find(".active");
        var labelList = [];
        $tagList.each(function(){
            labelList.push($(this).attr("data-tag-label"));
        });
        var queryString = getTagQueryString();
        if(queryString === ""){
            return url;
        }
        return (url.indexOf("?") > -1? url + "&tags=":url + "?tags=") + queryString;
    }
    var updateListOfContentContainer = function (listOfContent) {
        listOfContentContainer.html("");

        listOfContent.forEach(function (cell, i) {
            console.log(i);

            var content = cell; // just because I always get messy with js this.
            listOfContentContainer.append($(content));
        });
    };
    var getFresherContentList = function () {
        $.ajax(appendVerb(appendCategory(itemUrl)), {dataType:"json", method:"GET"}).done(function (data) {

            updateListOfContentContainer(data.results);
            updateTagsSelect(data.tags);
        });
    };
    var updateVerbSelect = function (listOfVerb) {
        verbSelect.html("");
        $.each(listOfVerb, function () {
            var sentenceLabel = "sentence_label";
            $("<option/>").val(this.label).text(this[sentenceLabel]).appendTo(verbSelect);
        });
    };
    var updateTagsSelect = function (listOfTags) {
        var oldQueryString = getTagQueryString();
        tagSelect.html("");
        listOfTags.forEach(function(label) {
                var isActive = oldQueryString .indexOf(label + ",") > -1 || oldQueryString .endswith("," + label);
                $("<li/>").append($("<button/>").attr("data-tag-label", label)
                    .attr("type", "button")
                    .addClass(isActive||oldQueryString === ""? "active":"")
                    .text(label)).appendTo(tagSelect);
            }
        );
    }
    categorySelect.on("change", function () {
        var searchUrl = appendCategory(url);
        $.ajax(searchUrl, {
            dataType:"json",
            "method": "get"
        }).done(function (data) {
            updateVerbSelect(data.results);
        });

    });
    verbSelect.on("change", function () {
        getFresherContentList();

    });
    tagSelect.on("click", "button", function(){
        if($(this).has(".active")){
            $(this).removeClass("active");
        }else {
            $(this).addClass("active");
        }
        getFresherContentList();
    });
})(jQuery);
