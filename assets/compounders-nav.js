/* ===================================================================
   RETIRED — August 3, 2026.

   This file used to draw a second navigation bar for the Compounders
   section only. That bar carried its own brand, every one of its links
   pointed inside /compounders/, and it hid the links back to the main
   site — so a reader who arrived at a Compounder profile from X or
   Substack had no route to サービス, 料金 or お問い合わせ.

   jpinv.com now has ONE navigation, in assets/nav.js.

   This file is kept, rather than deleted, only so that a page still
   cached in someone's browser keeps working. It loads the real
   navigation and does nothing else. Do not add anything to it, and do
   not reference it from a new page.
   =================================================================== */
(function () {
  "use strict";
  if (document.getElementById("jii-nav")) return;
  if (document.querySelector('script[src*="assets/nav.js"]')) return;
  var s = document.createElement("script");
  s.src = "/assets/nav.js?v=129cd945c8";
  s.defer = true;
  document.head.appendChild(s);
})();
