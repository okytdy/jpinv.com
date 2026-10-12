const EV = /\bEV\b/;

export function hasEvDefinition(text, language) {
  const match = EV.exec(text);
  if (!match) return true;
  const preceding = text.slice(0, match.index);
  return language === 'ja'
    ? /企業価値\s*[（(]\s*$/.test(preceding)
    : /enterprise value\s*\(\s*$/i.test(preceding);
}

export function hasProseEvDefinition(bodyHtml, language) {
  // Canonical running prose is held in .prose containers. Figures, figure notes,
  // metric strips and captions do not satisfy its independent first-use rule.
  const prose = [...bodyHtml.matchAll(/<div\b[^>]*class=["'](?:[^"']*\s)?prose(?:\s[^"']*)?["'][^>]*>([\s\S]*?)<\/div>/g)]
    .map((match) => match[1].replace(/<[^>]+>/g, ' ')).join(' ');
  return hasEvDefinition(prose, language);
}

// Input is a template-rendered header, not arbitrary article HTML. Only text
// tokens change; attribute values, data, URLs and all later mentions stay intact.
export function explainFirstEv(headerHtml, language) {
  const expansion = language === 'ja' ? '企業価値（EV）' : 'enterprise value (EV)';
  let found = false;
  let precedingText = '';
  return headerHtml.replace(/<[^>]*>|[^<]+/g, (token) => {
    if (token.startsWith('<') || found) return token;
    const match = EV.exec(token);
    if (!match) { precedingText += token; return token; }
    found = true;
    if (hasEvDefinition(precedingText + token, language)) return token;
    // In a forward multiple, the forecast belongs to earnings. Keep that
    // relationship clear when spelling out the abbreviation.
    const forward = language === 'ja'
      ? /予想\s*EV(\s*[/／]\s*)(営業利益|EBITDA|EBIT)/.exec(token)
      : /Forward\s+EV(\s*\/\s*)(EBITDA|EBIT|operating profit)/i.exec(token);
    if (forward && forward.index + forward[0].indexOf('EV') === match.index) {
      const expandedRatio = language === 'ja'
        ? expansion + forward[1] + '予想' + forward[2]
        : 'Enterprise value (EV)' + forward[1] + 'forecast ' + forward[2];
      return token.slice(0, forward.index) + expandedRatio + token.slice(forward.index + forward[0].length);
    }
    return token.slice(0, match.index) + expansion + token.slice(match.index + 2);
  });
}
