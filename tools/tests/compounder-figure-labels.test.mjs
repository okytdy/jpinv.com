import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectFigureLabels } from '../lib/compounder-figure-labels.mjs';

const shared = `<figure id="figure-2"><div class="cp-process-columns"><span aria-hidden="true"></span><span class="cp-evidence-key" id="role">NSDが担う仕事</span><span class="cp-evidence-key" id="impact">受注・業績への影響</span></div><ol class="cp-process-list"><li class="cp-process-step"><h4>設計</h4><div role="group" aria-labelledby="role"><p>移行手順を設計</p></div><div role="group" aria-labelledby="impact"><p>受注範囲が広がる</p></div></li><li class="cp-process-step"><h4>開発</h4><div role="group" aria-labelledby="role"><p>開発を実施</p></div><div role="group" aria-labelledby="impact"><p>売上高を計上</p></div></li></ol></figure>`;

test('one shared header with cell associations passes', () => {
  assert.deepEqual(inspectFigureLabels(shared), []);
});
test('rejects the original repeated Japanese process labels', () => {
  const cell = '<li class="cp-process-step"><div><span class="cp-evidence-key">NSDが担う仕事</span><p>作業</p></div><div><span class="cp-evidence-key">受注・業績への影響</span><p>業績</p></div></li>';
  const findings = inspectFigureLabels(`<figure id="figure-2"><ol class="cp-process-list">${cell.repeat(4)}</ol></figure>`);
  assert.equal(findings.filter((finding) => finding.includes('appears 4 times')).length, 2);
  assert.ok(findings.some((finding) => finding.includes('requires one shared')));
});
test('rejects the original repeated English evidence labels regardless of wording', () => {
  const row = '<div class="cp-evidence-row"><div><span class="cp-evidence-key">Next disclosure to watch</span></div><div><span class="cp-evidence-key">JII view</span></div></div>';
  assert.equal(inspectFigureLabels(`<figure id="figure-7"><div class="cp-evidence-list">${row.repeat(4)}</div></figure>`).filter((finding) => finding.includes('appears 4 times')).length, 2);
});
test('a duplicate inside a row still fails when a shared header exists', () => {
  assert.match(inspectFigureLabels(shared.replace('<p>移行手順を設計</p>', '<span class="cp-evidence-key">NSDが担う仕事</span><p>移行手順を設計</p>')).join('\n'), /appears 2 times/);
});
test('rejects missing cell references and duplicate ids', () => {
  assert.match(inspectFigureLabels(shared.replace('aria-labelledby="role"', 'aria-labelledby="missing"')).join('\n'), /missing header/);
  assert.match(inspectFigureLabels(shared.replace('id="impact"', 'id="role"')).join('\n'), /duplicate header\/element id/);
});
test('removing labels entirely does not evade the shared-header requirement', () => {
  assert.match(inspectFigureLabels('<figure><ol class="cp-process-list"><li class="cp-process-step"><p>Work</p><p>Impact</p></li></ol></figure>').join('\n'), /requires one shared/);
  assert.match(inspectFigureLabels(shared.replace(/<span class="cp-evidence-key" id="role">.*?<\/span>/, '')).join('\n'), /must name both data columns/);
});
test('shared labels may recur in a separate figure and comparisons keep local periods', () => {
  assert.deepEqual(inspectFigureLabels(shared + shared.replace('figure-2', 'figure-3')), []);
  assert.deepEqual(inspectFigureLabels('<figure><div class="cp-comparison-list"><span class="cp-evidence-key">FY3/26</span><span class="cp-evidence-key">FY3/26</span></div></figure>'), []);
});
