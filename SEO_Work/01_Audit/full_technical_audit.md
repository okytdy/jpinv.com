# Technical SEO Audit — jpinv.com / 2026-05-16

## 0. 監査範囲
- ファイル数: 27 HTML pages (JA + EN)
- フレームワーク: 静的 HTML (no framework, no SSR)
- ホスティング想定: GitHub Pages (CNAME: jpinv.com)

## 1. Indexability
- ✅ robots.txt: `Allow: /` で全公開
- ✅ Sitemap.xml: 既存、hreflang alternates 付き
- ⚠️ 旧 fix-pages-excluded-by-noindex-tag ブランチが remote にある → 過去に noindex 問題があった形跡。HEAD では解消済み確認。
- ⚠️ sitemap.xml に新規サービス LP / 記事の URL が含まれていない → 本セッションで更新済

## 2. Title / Meta description
全主要ページで title/description 設定済 ✅
- Home: `海外IR診断カード｜海外投資家目線のIR診断｜JII` ✅
- サービス: `サービス｜海外IR診断カードの内容と進め方｜JII` ✅
- 料金: `料金｜海外IR診断カードのプランと条件｜JII` ✅
- FAQ: `FAQ｜海外IR診断カードのよくある質問｜JII` ✅
- 会社概要: `会社概要｜Japan Investor Interface Co., Ltd.` ✅
- お問い合わせ: `お問い合わせ｜海外IR診断カード｜JII` ✅

潜在課題:
- meta keywords が全ページ同一文字列 `海外IR診断, IR診断カード, 海外投資家 IR, 英文IR点検, 海外IR支援, 海外IR診断レポート` — Google は keywords を無視するため害はないが、Bing/Yandex 用にページごとに調整する余地あり。
- 重複は title/description には**ない** ✅

## 3. Canonical
- 全主要ページで canonical 正しく設定 ✅

## 4. hreflang
- JA / EN / x-default 全ページ設定済 ✅
- 注意: 新規 LP / 記事を追加するときは hreflang も同時設定必須

## 5. Structured Data (JSON-LD)
- Home: Organization + ProfessionalService + WebSite + WebPage ✅
- サービス etc.: WebPage schema 想定
- ❌ Service schema 不在 → 本セッション仕様化
- ❌ FAQPage schema 不在 (FAQ ページに) → 本セッション仕様化
- ❌ Breadcrumb schema 不在 → 本セッション仕様化
- ❌ Person schema (代表者) 不在 → 本セッション仕様化
- ❌ Article schema (記事) — 記事自体が未作成

## 6. OGP / Twitter Card
- og:title / og:description / og:url 全主要ページ ✅
- og:image: `https://jpinv.com/assets/logo-jii-wordmark.svg` ✅
- twitter:card: summary_large_image ✅
- ⚠️ SVG が og:image に — 一部 SNS (LinkedIn, Slack) では SVG 非対応。PNG 版併用推奨。

## 7. Heading hierarchy
詳細抜き打ち調査:
- Home: H1 1個 ✅、H2 多数、H3 多数 — 正しい階層
- サービス: 未抽出だが title から判断可
- ⚠️ 一部 compounders 系で H1 が複数ある可能性 (要確認)

## 8. Page speed (推定)
- ⚠️ 全ページに **長大なインライン CSS** (1000-2400 行) → 共有CSS化で大幅な転送量削減可能
- ⚠️ Home の about-photo が **data:image/jpeg;base64** で巨大 (≥1MB のbase64 文字列が HTML 内に存在) → 既存 WIP で「image-of-text audit + photo externalisation」が working tree にあるため、これを採用すれば解決
- ✅ Google Fonts は preconnect 済み
- ⚠️ CSS Critical path 最適化なし
- ⚠️ JS 最小化未確認 (現状 inline JS のため最小化不要)

## 9. Lazy load
- ❌ `loading="lazy"` 属性が画像に未付与 → 本セッションでの推奨。compounders 系 画像にも要適用

## 10. Duplicate
- title / description: 重複なし ✅
- content: compounders/methodology vs compounders/methodology/ja で重複の可能性 (URL 構造的に)。canonical で対応されているか要確認

## 11. Orphan pages
- ❌ `/availability/` がメインナビにない可能性 (要確認)
- 新規サービス LP / 記事 を追加した後、必ず footer + サービスハブから link されているか確認

## 12. Internal links
- ✅ Home → /サービス/, /料金/, /会社概要/, /お問い合わせ/ は確認できる
- ⚠️ /サービス/ → 各サブサービス (新規 LP) への link 必要 → 本セッションで仕様化
- ⚠️ /compounders/ ↔ /articles/ の cross-link 不在 → 仕様化

## 13. Multilingual structure
- JA at `/{japanese-path}/`, EN at `/en/{english-path}/` ✅
- locale switcher (header に「JA | EN」) ✅
- assets/i18n-routes.json で URL mapping 管理 ✅
- assets/locale-switcher.js で動的切替 ✅
- ⚠️ Japanese URL は %E3%82... 形式に encode される — 一部ツール / 共有時に醜くなる可能性。ASCII slug 採用も将来検討余地

## 14. Mobile SEO
- viewport meta 全ページ ✅
- Responsive CSS @media queries 多数 ✅
- ⚠️ font sizes: hero H1 で clamp() 使用、small viewport (375px 以下) でも問題なし

## 15. Image alt
- ❌ data:image base64 の about-photo に alt 確認必要
- ⚠️ logo 画像の alt: og:image:alt は設定済だが <img> tag の alt 要確認
- ✅ favicon 系 (alt 不要)

## 16. Accessibility (WCAG)
- ✅ recent commit `5af3892 Improve WCAG accessibility across public pages` — 直近で WCAG 2.1 AA 対応済
- ⚠️ skip-to-content link 確認余地
- ⚠️ aria-label が一部の section にあるが、全 nav / button にあるか要確認

## 17. Security
- ✅ CSP: `upgrade-insecure-requests; block-all-mixed-content`
- ✅ HTTPS auto-redirect: inline JS で http → https
- ⚠️ CSP に script-src/style-src directive 不在 (XSS 緩和余地)

## 18. SSL
- ✅ CNAME=jpinv.com / GitHub Pages SSL 自動
- 過去に `fix-ssl-issues-for-jpinv.com` ブランチがあった形跡 → 解消済

---

## 19. 高優先度 fix list

`SEO_Work/01_Audit/high_priority_fixes.md` 参照
