const axeCorePath = require.resolve('axe-core/axe.min.js');

async function preparePage(page) {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
        scroll-behavior: auto !important;
      }
      .reveal { opacity: 1 !important; transform: none !important; }
      .mobile-menu, .mobile-menu-overlay { transition: none !important; }
    `
  });
}

async function gotoRoute(page, routePath) {
  await page.goto(routePath, { waitUntil: 'domcontentloaded' });
  await preparePage(page);
  await page.waitForLoadState('networkidle').catch(() => undefined);
}

async function runAxe(page) {
  await page.addScriptTag({ path: axeCorePath });
  return page.evaluate(async () => {
    return window.axe.run(document, {
      resultTypes: ['violations'],
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']
      }
    });
  });
}

function formatViolations(violations) {
  return violations
    .map((violation) => {
      const nodes = violation.nodes
        .slice(0, 5)
        .map((node) => `    - ${node.target.join(', ')}: ${node.failureSummary || 'No failure summary'}`)
        .join('\n');
      return `${violation.id} [${violation.impact}] ${violation.help}\n  ${violation.helpUrl}\n${nodes}`;
    })
    .join('\n\n');
}

function screenshotName(routeName, suffix, projectName) {
  return `${routeName}-${suffix}-${projectName}.png`;
}

module.exports = { gotoRoute, runAxe, formatViolations, screenshotName };
