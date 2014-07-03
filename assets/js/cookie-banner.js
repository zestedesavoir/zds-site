(function(window, document, undefined) {
  // Google Analytics ID
  var gaProperty = "UA-27730868-1";
  
  // Disable tracking if the opt-out cookie exists.
  var disableStr = "ga-disable-" + gaProperty;
  if(window.localStorage.getItem("ga-disable") === "true") {
    window[disableStr] = true;
  }
  else if(window.localStorage.getItem("ga-disable") === "false") {
    window[disableStr] = false;
  }
  else {
    $(".cookie-banner").show();
  }

  $(".cookie-banner .reject").on("click", function() {
    window.localStorage.setItem("ga-disable", "true");
    window[disableStr] = true;
    $(".cookie-banner").fadeOut();
  });

  $(".cookie-banner .accept").on("click", function() {
    window.localStorage.setItem("ga-disable", "false");
    window[disableStr] = false;
    $(".cookie-banner").fadeOut();
  });
})(window, document);