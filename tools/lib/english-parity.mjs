import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function sourceHash(value) {
  // Navigation cache versions and line-ending conventions do not change copy.
  const stable = value.replaceAll('\r\n', '\n').replace(/(assets\/(?:nav\.js|hero\.js|hero\.css)\?v=)[0-9a-zA-Z]+/g, '$1');
  return crypto.createHash('sha256').update(stable).digest('hex');
}

export function readCheckedTranslation(root, relativePath, source) {
  const translation = JSON.parse(fs.readFileSync(path.join(root, relativePath), 'utf8'));
  if (translation.sourceSha256 !== sourceHash(source)) {
    throw new Error(`${relativePath}: Japanese source changed; update its English translation before rebuilding.`);
  }
  return translation;
}

export function englishRoute(href, routes) {
  if (!href || !href.startsWith('/') || href.startsWith('//')) return href;
  const url = new URL(href, 'https://jpinv.com');
  const pathname = decodeURI(url.pathname);
  const route = routes[pathname] || (pathname.startsWith('/governance/') || pathname.startsWith('/compounders/') ? `/en${pathname}` : null);
  return route ? `${encodeURI(route)}${url.search}${url.hash}` : href;
}
