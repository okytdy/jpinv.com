(function(){
  var root = document.getElementById('jii-share');
  if(!root) return;
  var text = root.dataset.shareText;
  var url = root.dataset.shareUrl;
  var subject = root.dataset.shareSubject;
  var copyLabel = root.dataset.copyLabel;
  var copiedLabel = root.dataset.copiedLabel;
  var e = encodeURIComponent;

  var x = root.querySelector('.share-x');
  if(x) x.href = 'https://twitter.com/intent/tweet?text=' + e(text) + '&url=' + e(url);
  var em = root.querySelector('.share-em');
  if(em) em.href = 'mailto:?subject=' + e(subject) + '&body=' + e(text + '\n\n' + url);

  var perm = document.getElementById('jii-share-url-display');
  if(perm) perm.textContent = url;

  var cp = root.querySelector('.share-cp');
  if(cp) cp.addEventListener('click', function(){
    var btn = this;
    var lbl = btn.querySelector('.lbl');
    var doFlash = function(){
      lbl.textContent = copiedLabel;
      btn.classList.add('copied');
      setTimeout(function(){ lbl.textContent = copyLabel; btn.classList.remove('copied'); }, 2400);
    };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(url).then(doFlash, function(){});
    } else {
      var ta = document.createElement('textarea');
      ta.value = url; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); doFlash(); } catch(_){}
      document.body.removeChild(ta);
    }
  });
})();
