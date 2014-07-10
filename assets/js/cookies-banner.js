/* ===== Zeste de Savoir ====================================================
   Authors: Sandhose
            Alex-D / Alexandre Demode
   ---------------------------------
   Manage tracking cookies message
   ========================================================================== */

(function(window, document, undefined) {
    var $banner = $("#cookies-banner");

    function checkHasConsent(){
        if(document.cookie.indexOf("hasconsent=true") > -1){
            $("#gtm").after(
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
            $banner.show();
            // Accept for the next page
            setHasConsent(true, false);
        }
    }
    checkHasConsent();


    function setHasConsent(hasconsent, hide){
        document.cookie = "hasconsent="+hasconsent+"; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";

        if(hide)
            $banner.slideUp(200);
    }

    $("#reject-cookies").on("click", function(){
        setHasConsent(false, true);
    });

    $("#accept-cookies").on("click", function(){
        setHasConsent(true, true);
        checkHasConsent();
    });
})(window, document);