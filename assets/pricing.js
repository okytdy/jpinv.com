(function () {
  'use strict';

  const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
  const yen = new Intl.NumberFormat('ja-JP');
  const tabs = Array.from(document.querySelectorAll('.quote-tab'));
  const panels = Array.from(document.querySelectorAll('.quote-panel'));
  const quoteCta = document.getElementById('quote-cta');
  const translationDirection = document.getElementById('quote-direction');
  const documentType = document.getElementById('quote-document');
  const translationCount = document.getElementById('quote-count');
  const translationUnit = document.getElementById('quote-unit');
  const translationPrice = document.getElementById('quote-translation-price');
  const translationResult = document.getElementById('quote-translation-result');
  const translationSummary = document.getElementById('quote-translation-summary');
  const meetingCount = document.getElementById('quote-meetings');
  const meetingDuration = document.getElementById('quote-duration');
  const interpretationPrice = document.getElementById('quote-interpretation-price');
  const interpretationResult = document.getElementById('quote-interpretation-result');
  const interpretationSummary = document.getElementById('quote-interpretation-summary');

  if (!tabs.length || !quoteCta) return;

  let activeMode = 'translation';
  let currentEstimate = null;

  function readPositiveNumber(field, max) {
    if (!field || !field.value.trim()) return null;
    const number = Number(field.value);
    if (!Number.isFinite(number) || number < 1) return null;
    return Math.min(Math.round(number), max);
  }

  function displayRange(low, high) {
    return `¥${yen.format(low)}${isEnglish ? '–' : '〜'}¥${yen.format(high)}`;
  }

  function setActiveMode(mode, focusPanel) {
    activeMode = mode;
    tabs.forEach((tab) => {
      const selected = tab.dataset.quoteMode === mode;
      tab.setAttribute('aria-selected', selected ? 'true' : 'false');
      tab.tabIndex = selected ? 0 : -1;
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.quotePanel !== mode;
    });
    if (focusPanel) {
      const panel = panels.find((item) => item.dataset.quotePanel === mode);
      const firstField = panel && panel.querySelector('select, input');
      if (firstField) firstField.focus();
    }
    updateEstimate();
  }

  function setResultState(result, summary, valid) {
    result.classList.toggle('is-empty', !valid);
    summary.hidden = !valid;
    quoteCta.hidden = !valid;
    if (!valid) currentEstimate = null;
  }

  function updateTranslation() {
    const direction = translationDirection.value;
    const isEnglishSource = direction === 'en-ja';
    documentType.disabled = isEnglishSource;
    documentType.setAttribute('aria-disabled', isEnglishSource ? 'true' : 'false');
    translationUnit.textContent = isEnglish
      ? (isEnglishSource ? 'words' : 'characters')
      : (isEnglishSource ? 'ワード' : '文字');

    const count = readPositiveNumber(translationCount, 1000000);
    if (count === null) {
      translationPrice.textContent = isEnglish ? 'Enter the source volume' : '原稿の分量を入力してください';
      translationSummary.textContent = '';
      setResultState(translationResult, translationSummary, false);
      return;
    }

    let lowRate = 6;
    let highRate = 9;
    let serviceLabel = isEnglish ? 'earnings release or timely disclosure' : '決算短信・適時開示など';
    if (isEnglishSource) {
      lowRate = 12;
      highRate = 22;
      serviceLabel = isEnglish ? 'English-to-Japanese IR translation' : 'IR関連文書の英日翻訳';
    } else if (documentType.value === 'strategic') {
      lowRate = 10;
      highRate = 14;
      serviceLabel = isEnglish ? 'integrated report, securities report, or medium-term plan' : '統合報告書・有報・中計など';
    }

    const low = count * lowRate;
    const high = count * highRate;
    translationPrice.textContent = displayRange(low, high);
    translationSummary.textContent = isEnglish
      ? `${yen.format(count)} ${isEnglishSource ? 'words' : 'characters'} × ¥${lowRate}–${highRate}`
      : `${yen.format(count)}${isEnglishSource ? 'ワード' : '文字'} × ${lowRate}～${highRate}円`;
    currentEstimate = {
      mode: 'translation',
      direction,
      count,
      unit: isEnglish ? (isEnglishSource ? ' words' : ' characters') : (isEnglishSource ? 'ワード' : '文字'),
      document: isEnglishSource ? 'other' : (documentType.value === 'strategic' ? 'annual_report' : 'earnings_release'),
      low,
      high,
      label: serviceLabel
    };
    setResultState(translationResult, translationSummary, true);
  }

  function updateInterpretation() {
    const meetings = readPositiveNumber(meetingCount, 24);
    if (meetings === null) {
      interpretationPrice.textContent = isEnglish ? 'Enter the number of bookings' : '回数を入力してください';
      interpretationSummary.textContent = '';
      setResultState(interpretationResult, interpretationSummary, false);
      return;
    }
    const duration = meetingDuration.value;
    const unitPrice = duration === 'full' ? 80000 : 50000;
    const total = meetings * unitPrice;
    const durationLabel = isEnglish
      ? (duration === 'full' ? 'Full day (up to 8 hours)' : 'Half day (up to 3 hours)')
      : (duration === 'full' ? '1日（8時間まで）' : '半日（3時間まで）');
    interpretationPrice.textContent = `¥${yen.format(total)}${isEnglish ? '+' : '〜'}`;
    interpretationSummary.textContent = isEnglish ? `${durationLabel} × ${meetings}` : `${durationLabel} × ${meetings}回`;
    currentEstimate = {
      mode: 'interpretation',
      meetings,
      duration,
      durationLabel,
      total
    };
    setResultState(interpretationResult, interpretationSummary, true);
  }

  function updateEstimate() {
    if (activeMode === 'translation') updateTranslation();
    else updateInterpretation();
  }

  function setSelect(name, value) {
    const form = document.getElementById('inquiry-form');
    const field = form && form.elements[name];
    if (!field) return;
    const valid = Array.from(field.options || []).some((option) => option.value === value);
    if (valid) field.value = value;
  }

  function prefillInquiry() {
    if (!currentEstimate) return;
    const form = document.getElementById('inquiry-form');
    if (!form) return;
    const volume = form.elements.estimated_volume;
    const message = form.elements.message;
    const sourceId = document.getElementById('cta_source');
    const context = document.getElementById('cta_context');
    let messageText = '';

    if (currentEstimate.mode === 'translation') {
      const isEnglishSource = currentEstimate.direction === 'en-ja';
      setSelect('service_type', 'translation');
      setSelect('document_type', currentEstimate.document);
      setSelect('source_language', isEnglishSource ? 'en' : 'ja');
      setSelect('target_language', isEnglishSource ? 'ja' : 'en');
      if (volume) volume.value = `${yen.format(currentEstimate.count)}${currentEstimate.unit}`;
      messageText = isEnglish
        ? `I would like a formal quote for ${currentEstimate.label}. Estimate: ${yen.format(currentEstimate.count)}${currentEstimate.unit}, ${displayRange(currentEstimate.low, currentEstimate.high)} excluding tax.`
        : `${currentEstimate.label}の正式見積もりを希望します。概算条件：${yen.format(currentEstimate.count)}${currentEstimate.unit}、${displayRange(currentEstimate.low, currentEstimate.high)}（税別）。`;
    } else {
      setSelect('service_type', 'interpretation');
      setSelect('document_type', 'meeting_script');
      setSelect('source_language', 'ja');
      setSelect('target_language', 'bilingual');
      if (volume) volume.value = isEnglish
        ? `${currentEstimate.durationLabel} × ${currentEstimate.meetings}`
        : `${currentEstimate.durationLabel} × ${currentEstimate.meetings}回`;
      messageText = isEnglish
        ? `I would like a formal quote for IR interpretation. Estimate: ${currentEstimate.durationLabel} × ${currentEstimate.meetings}, from ¥${yen.format(currentEstimate.total)} excluding tax.`
        : `IR通訳の正式見積もりを希望します。概算条件：${currentEstimate.durationLabel} × ${currentEstimate.meetings}回、¥${yen.format(currentEstimate.total)}〜（税別）。`;
    }

    if (message && !message.value.trim()) message.value = messageText;
    if (sourceId) sourceId.value = 'pricing_instant_quote';
    if (context) context.value = messageText;
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => setActiveMode(tab.dataset.quoteMode, false));
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const nextIndex = event.key === 'ArrowRight' ? (index + 1) % tabs.length : (index - 1 + tabs.length) % tabs.length;
      tabs[nextIndex].focus();
      setActiveMode(tabs[nextIndex].dataset.quoteMode, false);
    });
  });

  [translationDirection, documentType, translationCount, meetingCount, meetingDuration].forEach((field) => {
    if (!field) return;
    field.addEventListener('input', updateEstimate);
    field.addEventListener('change', updateEstimate);
  });
  quoteCta.addEventListener('click', prefillInquiry);

  setActiveMode('translation', false);
})();
