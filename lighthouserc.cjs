const { lighthouseRoutes } = require('./qa/routes.cjs');

const baseUrl = process.env.BASE_URL ? process.env.BASE_URL.replace(/\/$/, '') : '';
const lighthouseUrls = lighthouseRoutes.map((route) => (baseUrl ? `${baseUrl}${route.path}` : route.path));
const collectTarget = baseUrl ? {} : { staticDistDir: 'dist' };

// Lighthouse CI target budgets for public JP/EN core routes.
// Mobile-first release gates: Performance >= 90, LCP <= 2.5s, CLS <= 0.10,
// TBT <= 200ms, JS transfer <= 60 KiB, image transfer <= 70 KiB per route.
module.exports = {
  ci: {
    collect: {
      ...collectTarget,
      url: lighthouseUrls,
      numberOfRuns: 3,
      settings: {
        formFactor: 'mobile',
        screenEmulation: {
          mobile: true,
          width: 390,
          height: 844,
          deviceScaleFactor: 3,
          disabled: false
        },
        throttlingMethod: 'simulate',
        onlyCategories: ['performance', 'best-practices', 'seo'],
        budgets: require('./lighthouse-budgets.json')
      }
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.95 }],
        'categories:seo': ['warn', { minScore: 0.95 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'speed-index': ['warn', { maxNumericValue: 3000 }],
        interactive: ['warn', { maxNumericValue: 3800 }],
        'uses-responsive-images': 'error',
        'offscreen-images': 'error',
        'render-blocking-resources': 'warn',
        'unused-css-rules': 'warn',
        'unused-javascript': 'warn',
        'bootup-time': ['warn', { maxNumericValue: 1200 }],
        'resource-summary:script:size': ['error', { maxNumericValue: 61440 }],
        'resource-summary:image:size': ['error', { maxNumericValue: 71680 }],
        'resource-summary:stylesheet:size': ['warn', { maxNumericValue: 92160 }],
        'third-party-summary:size': ['warn', { maxNumericValue: 204800 }]
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
};
