(function(window, document, undefined) {
    // Google Analytics ID
    var gaProperty = "UA-27730868-1";

    var $banner = $("#cookies-banner");

    // Disable tracking if the opt-out cookie exists.
    var disableStr = "ga-disable-" + gaProperty;
    if(document.cookie.indexOf("hasconsent=true") > -1){
        window[disableStr] = false;
    } else if(document.cookie.indexOf("hasconsent=false") > -1){
        window[disableStr] = true;
    } else {
        $banner.show();
    }

    function sethasconsent(hasconsent){
        document.cookie = "hasconsent="+hasconsent+"; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";
        window[disableStr] = !hasconsent;
        $banner.slideUp(200);
    }

    $("#reject-cookies").on("click", function(){
        sethasconsent(false);
    });

    $("#accept-cookies").on("click", function(){
        sethasconsent(true);
    });
})(window, document);