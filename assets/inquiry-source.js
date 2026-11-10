/* Retain the referring JII page only; send it with an inquiry, never on its own. */
(function () {
  'use strict';
  var source = '';
  try {
    var previous = document.referrer && new URL(document.referrer);
    if (previous && previous.origin === location.origin) {
      source = previous.pathname;
      if (/^\/(?:en\/)?governance\//.test(source)) {
        sessionStorage.setItem('jii_inquiry_source', source);
      }
    }
    source = sessionStorage.getItem('jii_inquiry_source') || source;
  } catch (e) { /* The form works when storage or referrer access is unavailable. */ }
  var form = document.getElementById('inquiry-form');
  if (!form || !source) return;
  var field = document.createElement('input');
  field.type = 'hidden';
  field.name = 'website_source';
  field.value = source.slice(0, 240);
  form.appendChild(field);
}());
