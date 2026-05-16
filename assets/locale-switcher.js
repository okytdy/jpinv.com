(function(){
  var samePageHashes = {top:1, overview:1, services:1, pricing:1, company:1, contact:1};
  function withHash(href){
    if(!location.hash) return href;
    var key = location.hash.slice(1);
    if(!samePageHashes[key]) return href;
    try {
      var url = new URL(href, location.origin);
      if((url.pathname === '/' || url.pathname === '/en/') && !url.hash){ url.hash = location.hash; return url.pathname + url.hash; }
    } catch(e) {}
    return href;
  }
  document.querySelectorAll('[data-locale-route]').forEach(function(a){
    var href = a.getAttribute('href');
    if(!href) return;
    var next = withHash(href);
    if(next !== href) a.setAttribute('href', next);
  });
})();
