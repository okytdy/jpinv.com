(function () {
  var FOOTER_DESCRIPTION = '株式会社ジャパン・インベスター・インターフェースは、日本企業の英文開示・IR翻訳・投資家面談通訳を支援し、海外IR診断を通じて海外投資家に伝わる開示資料・IRサイト・面談対応を整える海外IR支援会社です。';
  var nodes = document.querySelectorAll('.footer-brand p');
  for (var i = 0; i < nodes.length; i += 1) {
    nodes[i].textContent = FOOTER_DESCRIPTION;
  }
})();
