(function () {
  'use strict';

  var ALLOWED_PARAMS = {
    page_path: true,
    locale: true,
    cta_id: true,
    service_type: true,
    document_type: true,
    field_name: true,
    error_type: true,
    transport: true,
    debug_mode: true
  };
  var EVENT_NAMES = {
    language_switch: true,
    cta_click: true,
    rfq_form_start: true,
    rfq_field_error: true,
    rfq_submit_success: true,
    rfq_submit_error: true,
    generate_lead: true
  };
  var startedForms = new WeakSet();

  function locale() {
    return document.documentElement.lang || (location.pathname.indexOf('/en/') === 0 ? 'en' : 'ja');
  }

  function debugEnabled() {
    try {
      var params = new URLSearchParams(location.search);
      return params.get('analytics_debug') === '1' || params.get('gtm_debug') === '1' || localStorage.getItem('jii_analytics_debug') === '1';
    } catch (e) {
      return false;
    }
  }

  function cleanValue(value) {
    if (value === undefined || value === null || value === '') return undefined;
    return String(value).replace(/[^a-zA-Z0-9_\-/.]/g, '_').slice(0, 80);
  }

  function baseParams() {
    return {
      page_path: location.pathname,
      locale: locale()
    };
  }

  function cleanParams(params) {
    var rawParams = Object.assign({}, baseParams(), params || {});
    var cleaned = {};
    Object.keys(rawParams).forEach(function (key) {
      if (!ALLOWED_PARAMS[key]) return;
      var value = key === 'debug_mode' ? Boolean(rawParams[key]) : cleanValue(rawParams[key]);
      if (value !== undefined) cleaned[key] = value;
    });
    if (debugEnabled()) cleaned.debug_mode = true;
    return cleaned;
  }

  function pushDataLayer(eventName, params) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: eventName }, params));
  }

  function sendGtag(eventName, params) {
    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
      return true;
    }
    return false;
  }

  function trackEvent(eventName, params) {
    if (!EVENT_NAMES[eventName]) return;
    var payload = cleanParams(params);
    pushDataLayer(eventName, payload);
    var usedGtag = sendGtag(eventName, payload);
    if (debugEnabled() && window.console && typeof window.console.info === 'function') {
      window.console.info('[JII analytics]', eventName, Object.assign({ transport: usedGtag ? 'dataLayer+gtag' : 'dataLayer' }, payload));
    }
  }

  function getCtaId(el) {
    return el.dataset.analyticsCta || el.dataset.rfqSource || el.id || cleanValue((el.textContent || '').trim().toLowerCase().replace(/\s+/g, '_')) || 'cta';
  }

  function getRfqParams(el) {
    return {
      cta_id: getCtaId(el),
      service_type: el.dataset.rfqService,
      document_type: el.dataset.rfqDocument
    };
  }

  function formParams(form) {
    if (!form) return {};
    return {
      service_type: form.elements.service_type && form.elements.service_type.value,
      document_type: form.elements.document_type && form.elements.document_type.value
    };
  }

  function startForm(form) {
    if (!form || startedForms.has(form)) return;
    startedForms.add(form);
    trackEvent('rfq_form_start', formParams(form));
  }

  function instrument() {
    document.querySelectorAll('[data-locale-route]').forEach(function (link) {
      link.addEventListener('click', function () {
        trackEvent('language_switch', { cta_id: link.getAttribute('lang') || link.dataset.locale || 'locale_switcher' });
      });
    });

    document.querySelectorAll('a[href*="#contact"], button[type="submit"], [data-rfq-service], [data-rfq-document], [data-rfq-message]').forEach(function (el) {
      el.addEventListener('click', function () {
        if (el.type === 'submit') return;
        trackEvent('cta_click', getRfqParams(el));
      });
    });

    document.querySelectorAll('form[id*="inquiry"], form[data-recaptcha-site-key]').forEach(function (form) {
      form.addEventListener('focusin', function () { startForm(form); }, { once: true });
      form.addEventListener('input', function () { startForm(form); }, { once: true });
      form.addEventListener('change', function () { startForm(form); }, { once: true });
    });
  }

  window.JIIAnalytics = {
    trackEvent: trackEvent,
    trackRfqError: function (form, fieldName, errorType) {
      trackEvent('rfq_field_error', Object.assign({ field_name: fieldName, error_type: errorType || 'validation' }, formParams(form)));
    },
    trackRfqSuccess: function (form) {
      var params = formParams(form);
      trackEvent('rfq_submit_success', params);
      trackEvent('generate_lead', params);
    },
    trackRfqSubmitError: function (form, errorType) {
      trackEvent('rfq_submit_error', Object.assign({ error_type: errorType || 'submission' }, formParams(form)));
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', instrument, { once: true });
  else instrument();
}());
