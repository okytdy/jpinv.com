import test from 'node:test';
import assert from 'node:assert/strict';
import { explainFirstEv, hasEvDefinition } from './lib/compounder-ev-first-use.mjs';

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
