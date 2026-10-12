import test from 'node:test';
import assert from 'node:assert/strict';
import { explainFirstEv, hasEvDefinition, hasProseEvDefinition } from './lib/compounder-ev-first-use.mjs';

test('defines EV inside a Japanese ratio at first use only', () => {
  const html = '<dt>予想EV / 営業利益</dt><p>EVは100億円</p>';
  assert.equal(explainFirstEv(html, 'ja'), '<dt>企業価値（EV） / 予想営業利益</dt><p>EVは100億円</p>');
});
test('keeps forecast ownership on the earnings denominator in English', () => {
  assert.equal(explainFirstEv('<dt>Forward EV/EBIT</dt>', 'en'), '<dt>Enterprise value (EV)/forecast EBIT</dt>');
});
test('ignores attributes and defines the earlier deck before metrics', () => {
  assert.equal(explainFirstEv('<a href="/EV/" data-name="EV">EV/EBITは10倍</a><dt>EV</dt>', 'ja'), '<a href="/EV/" data-name="EV">企業価値（EV）/EBITは10倍</a><dt>EV</dt>');
});
test('preserves existing definitions and is idempotent in both languages', () => {
  for (const [language, html] of [['ja','<p>企業価値（EV）とEV</p>'],['en','<p>Enterprise value (EV) and EV</p>']]) {
    assert.equal(explainFirstEv(html, language), html);
    assert.equal(explainFirstEv(explainFirstEv('<dt>EV/EBIT</dt>', language), language), explainFirstEv('<dt>EV/EBIT</dt>', language));
  }
});
test('does not alter non-EV words or markup without the abbreviation', () => {
  const html = '<p>REVENUE / development</p>';
  assert.equal(explainFirstEv(html, 'en'), html);
});
test('handles an existing definition split across inline tags', () => {
  const html = '<p>企業価値（<span>EV</span>）</p>';
  assert.equal(explainFirstEv(html, 'ja'), html);
});
test('rejects a late definition and a definition in the wrong language', () => {
  assert.equal(hasEvDefinition('EV/営業利益。後段で企業価値（EV）。', 'ja'), false);
  assert.equal(hasEvDefinition('企業価値（EV）', 'en'), false);
  assert.equal(hasEvDefinition('enterprise value (EV)', 'en'), true);
  assert.equal(hasEvDefinition('企業価値（EV）', 'ja'), true);
});

test('a masthead or figure-note definition does not replace a body definition', () => {
  const html='<header>企業価値（EV）</header><p class="figure-note">企業価値（EV）</p><div class="prose"><p>EVは100億円。</p></div>';
  assert.equal(hasProseEvDefinition(html, 'ja'), false);
});
test('checks running prose independently of earlier figure abbreviations', () => {
  const html='<figure>EV/営業利益</figure><div class="prose"><p>企業価値（EV）は100億円。</p><p>EV倍率は10倍。</p></div>';
  assert.equal(hasProseEvDefinition(html, 'ja'), true);
});
test('checks first use across prose containers in both languages', () => {
  assert.equal(hasProseEvDefinition('<div class="prose"><p>EV is 100.</p></div><div class="prose"><p>Enterprise value (EV) is 100.</p></div>', 'en'), false);
  assert.equal(hasProseEvDefinition('<div class="prose"><p>Enterprise value (EV) is 100.</p></div>', 'en'), true);
  assert.equal(hasProseEvDefinition('<div class="prose"><p>売上高は100億円。</p></div>', 'ja'), true);
});
test('does not skip prose inside a layout wrapper or match a different class', () => {
  const html='<div class="layout"><div class="prose"><p>EV is 100.</p></div></div><div class="not-prose"><p>Enterprise value (EV)</p></div>';
  assert.equal(hasProseEvDefinition(html, 'en'), false);
});
