const publicRoutes = [
  { name: 'home-ja', path: '/', locale: 'ja', visual: true, lighthouse: true },
  { name: 'home-en', path: '/en/', locale: 'en', visual: true, lighthouse: true },
  { name: 'services-ja', path: '/サービス/', locale: 'ja', visual: true, lighthouse: true },
  { name: 'services-en', path: '/en/services/', locale: 'en', visual: true, lighthouse: true },
  { name: 'pricing-ja', path: '/料金/', locale: 'ja', visual: true, lighthouse: true, rfq: true },
  { name: 'pricing-en', path: '/en/pricing/', locale: 'en', visual: true, lighthouse: true, rfq: true },
  { name: 'company-ja', path: '/会社概要/', locale: 'ja', visual: false, lighthouse: true },
  { name: 'company-en', path: '/en/company/', locale: 'en', visual: false, lighthouse: true },
  { name: 'faq-ja', path: '/faq/', locale: 'ja', visual: false, lighthouse: true },
  { name: 'faq-en', path: '/en/faq/', locale: 'en', visual: false, lighthouse: true },
  { name: 'compounders-ja', path: '/compounders/', locale: 'ja', visual: true, lighthouse: false },
  { name: 'compounders-en', path: '/en/compounders/', locale: 'en', visual: true, lighthouse: false },
  { name: 'compounders-methodology-ja', path: '/compounders/methodology/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'compounders-methodology-en', path: '/en/compounders/methodology/', locale: 'en', visual: false, lighthouse: false },
  { name: 'compounders-universe-ja', path: '/compounders/universe/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'compounders-universe-en', path: '/en/compounders/universe/', locale: 'en', visual: false, lighthouse: false },
  { name: 'compounder-4194-ja', path: '/compounders/4194/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'compounder-4194-en', path: '/en/compounders/4194/', locale: 'en', visual: false, lighthouse: false },
  { name: 'compounder-4475-ja', path: '/compounders/4475/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'compounder-4475-en', path: '/en/compounders/4475/', locale: 'en', visual: false, lighthouse: false },
  { name: 'compounder-4776-ja', path: '/compounders/4776/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'compounder-4776-en', path: '/en/compounders/4776/', locale: 'en', visual: false, lighthouse: false },
  { name: 'service-diagnostic-ja', path: '/サービス/diagnostic/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-english-review-ja', path: '/サービス/english-review/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-meeting-support-ja', path: '/サービス/meeting-support/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-earnings-review-ja', path: '/サービス/earnings-review/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-disclosure-review-ja', path: '/サービス/disclosure-review/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-ir-support-ja', path: '/サービス/ir-support/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'service-interpretation-ja', path: '/サービス/interpretation/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'articles-ja', path: '/articles/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-why-correct-english-ja', path: '/articles/why-correct-english-doesnt-reach/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-first-10-minutes-ja', path: '/articles/first-10-minutes-overseas-investor/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-common-failures-ja', path: '/articles/common-overseas-ir-failures/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-misreadings-ja', path: '/articles/misreadings-in-english-ir/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-readiness-checklist-ja', path: '/articles/overseas-ir-readiness-checklist/', locale: 'ja', visual: false, lighthouse: false },
  { name: 'article-interpretation-perception-ja', path: '/articles/interpretation-changes-investor-perception/', locale: 'ja', visual: false, lighthouse: false }
];

const redirectRoutes = [
  { name: 'contact-ja-redirect', path: '/お問い合わせ/', target: '/#contact' },
  { name: 'contact-en-redirect', path: '/en/contact/', target: '/en/#contact' }
];

const viewports = {
  desktop: { width: 1440, height: 1400 },
  mobile: { width: 390, height: 844 }
};

module.exports = {
  publicRoutes,
  redirectRoutes,
  lighthouseRoutes: publicRoutes.filter((route) => route.lighthouse),
  axeRoutes: publicRoutes,
  visualRoutes: publicRoutes.filter((route) => route.visual),
  rfqRoutes: publicRoutes.filter((route) => route.rfq),
  viewports
};
