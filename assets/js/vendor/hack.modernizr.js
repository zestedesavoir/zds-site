// Detect CSS mask support and hack it into Modernizr
// https://gist.github.com/trey/1827930

var html = document.body.parentNode;
if(document.body.style[ '-webkit-mask-repeat' ] !== undefined){
  Modernizr.cssmasks = true;
  html.className = html.className + " cssmasks";
} else {
  Modernizr.cssmasks = false;
  html.className = html.className + " no-cssmasks";
}