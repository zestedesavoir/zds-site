/* ===== Zeste de Savoir ====================================================
   Manage tracking cookies message
   ---------------------------------
   Authors: Sandhose
            Alex-D / Alexandre Demode
   ========================================================================== */

(function(document, undefined) {
    var $banner = $("#cookies-banner");

    function checkHasConsent(){
        if(document.cookie.indexOf("hasconsent=true") > -1){
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
            // Accept for the next page
            setHasConsent(true);
            
            // Show the banner
            $banner.show();
        }
    }
    checkHasConsent();


    function setHasConsent(hasconsent){
        document.cookie = "hasconsent="+hasconsent+"; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";
    }

    $("#reject-cookies").on("click", function(){
        setHasConsent(false);
        $banner.slideUp(200);
    });

    $("#accept-cookies").on("click", function(){
        checkHasConsent();
        $banner.slideUp(200);
    });
})(document);