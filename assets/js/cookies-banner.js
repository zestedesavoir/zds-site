/* ===== Zeste de Savoir ====================================================
   Manage tracking cookies message
   ---------------------------------
   Authors: Sandhose
            Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, undefined) {
    var $banner = $("#cookies-banner");

    function getDNTHeader() {
        var dnt = navigator.doNotTrack || navigator.msDoNotTrack || window.doNotTrack;
        return !(dnt !== undefined) ? (dnt && dnt !== "yes" && dnt !== 1 && dnt !== "1") : true;
    }

    function checkHasConsent(){
        if(document.cookie.indexOf("hasconsent=true") > -1){
            if ($("#doNotTrack")[0])
                $banner.show(); // Show bar on support

            $("head").append(
                "<script>" +
                    "dataLayer = [{'gaTrackingId': 'UA-27730868-1'}];" +
                    "(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':" +
                    "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0]," +
                    "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=" +
                    "'//www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);" +
                    "})(window,document,'script','dataLayer','GTM-WH7642');" +
                "</script>"
            );
        } else if(document.cookie.indexOf("hasconsent=false") === -1){
            if (!getDNTHeader()) // Accept for the next page (only if DNT Header is not true)
                setCookie("hascontent", true);

            $banner.show();
        } else {
            $banner.show();
        }
    }
    checkHasConsent();

    function deleteAnalyticsCookies() {
        var cookieNames = ["__utma","__utmb","__utmc","__utmt","__utmv","__utmz","_ga","_gat"]
        for (var i = 0; i < cookieNames.length; i++)
            setCookie(cookieNames[i], null);
    }

    function setCookie(name, value) {
        if (value === null) {
            document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/";
        } else {
            document.cookie = name + "=" + value + "; expires=Thu, 31 Dec 2099 23:59:59 GMT; path=/";
        }
    }

    $("[data-cookie-action=reject]").on("click", function(){
        setCookie("hascontent", false);
        deleteAnalyticsCookies();

        $banner.slideUp(200);
    });

    $("[data-cookie-action=undo]").on("click", function(){
        if (!$("#doNotTrack")[0]) // If user clicks on button when he isn't on the help page.
            setCookie("hascontent", null);

        $banner.slideUp(200);
    });

    $("[data-cookie-action=accept]").on("click", function(){
        setCookie("hascontent", true);
        $banner.slideUp(200);
    });
})(document);