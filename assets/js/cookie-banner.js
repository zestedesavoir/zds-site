(function(window, document, undefined) {
  // Google Analytics ID
  var gaProperty = "UA-27730868-1";
  
  // Disable tracking if the opt-out cookie exists.
  var disableStr = "ga-disable-" + gaProperty;
  if(document.cookie.indexOf("ga-disable=true") > -1) {
    window[disableStr] = true;
  }
  else if(document.cookie.indexOf("ga-disable=false") > -1) {
    window[disableStr] = false;
  }
  else {
    $(".cookie-banner").show();
  }

  $(".cookie-banner .reject").on("click", function() {
    window.localStorage.setItem("ga-disable", "true");
    document.cookie = "ga-disable=true; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";
    window[disableStr] = true;
    $(".cookie-banner").fadeOut();
  });

  $(".cookie-banner .accept").on("click", function() {
    window.localStorage.setItem("ga-disable", "false");
    document.cookie = "ga-disable=false; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";
    window[disableStr] = false;
    $(".cookie-banner").fadeOut();
  });
})(window, document);