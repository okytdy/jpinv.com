function attribute(tag, name) {
  return tag.match(new RegExp(`\\b${name}=["']([^"']*)["']`, 'i'))?.[1] || '';
}

function plain(html) {
  return html.replace(/<[^>]*>/g, ' ').replace(/&#39;|&apos;/g, "'")
    .replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
}

// Qualitative evidence/process rows share a schema. Numerical comparison cards
// retain their local period labels; these are a separate component contract.
export function inspectFigureLabels(html) {
  const failures = [];
  for (const match of html.matchAll(/<figure\b[^>]*>[\s\S]*?<\/figure>/gi)) {
    const figure = match[0];
    if (!/class=["'][^"']*\b(?:cp-evidence-list|cp-process-list)\b/.test(figure)) continue;
    const name = attribute(figure.match(/^<figure\b[^>]*>/i)[0], 'id') || 'unnamed figure';
    for (const [list, header] of [['cp-evidence-list', 'cp-evidence-columns'], ['cp-process-list', 'cp-process-columns']]) {
      if (new RegExp(`class=["'][^"']*\\b${list}\\b`).test(figure)
        && !new RegExp(`class=["'][^"']*\\b${header}\\b`).test(figure)) {
        failures.push(`${name}: ${list} requires one shared ${header} header`);
      }
    }
    const labels = new Map();
    for (const label of figure.matchAll(/<span\b([^>]*)>([\s\S]*?)<\/span>/gi)) {
      if (!attribute(label[1], 'class').split(/\s+/).includes('cp-evidence-key')) continue;
      const text = plain(label[2]);
      if (text) labels.set(text, (labels.get(text) || 0) + 1);
    }
    for (const [label, count] of labels) {
      if (count > 1) failures.push(`${name}: shared label "${label}" appears ${count} times; use one shared header and aria-labelledby on its cells`);
    }
    const ids = new Map();
    for (const opening of figure.matchAll(/<[a-z][^>]*>/gi)) {
      const id = attribute(opening[0], 'id');
      if (id) ids.set(id, (ids.get(id) || 0) + 1);
    }
    for (const [id, count] of ids) {
      if (count > 1) failures.push(`${name}: duplicate header/element id "${id}"`);
    }
    const refs = [...figure.matchAll(/\baria-labelledby=["']([^"']+)["']/g)]
      .flatMap((ref) => ref[1].trim().split(/\s+/));
    for (const ref of new Set(refs)) {
      if (!ids.has(ref)) failures.push(`${name}: aria-labelledby references missing header "${ref}"`);
    }
    for (const header of figure.matchAll(/<div\b([^>]*\bclass=["'][^"']*\b(?:cp-evidence-columns|cp-process-columns)\b[^"']*["'][^>]*)>([\s\S]*?)<\/div>/gi)) {
      const keys = [...header[2].matchAll(/<span\b([^>]*)>([\s\S]*?)<\/span>/gi)]
        .filter((label) => attribute(label[1], 'class').split(/\s+/).includes('cp-evidence-key'));
      if (keys.length !== 2) failures.push(`${name}: shared qualitative header must name both data columns`);
      for (const label of keys) {
        const id = attribute(label[1], 'id');
        if (!id || !refs.includes(id)) failures.push(`${name}: shared header "${plain(label[2])}" must have an id referenced by its cells`);
      }
    }
  }
  return failures;
}
