# High Priority Fixes — jpinv.com SEO

## Tier 1: 即時 (本セッションで実装/仕様化)

### F1. Sitemap update with new URLs
- File: `sitemap.xml`
- Action: 新規 7 LP + 6 記事 + /articles/ ハブを追加, hreflang 完備
- Status: ✅ 実装済 (本セッション)

### F2. 7 service LPs
- Files: `/サービス/{slug}/index.html`
- Action: KW別の検索意図に応じた LP を新設
- Status: 仕様化済 + 1-2 LP を実装

### F3. 6 authority articles
- Files: `/articles/{slug}/index.html` + `/articles/index.html` (hub)
- Action: EEAT 強化 + ロングテール KW 取得
- Status: 仕様化済 + 1 article を実装

### F4. Service / FAQPage / Breadcrumb / Article schema
- Action: 各 LP / 記事 / FAQ ページに JSON-LD 追加
- Status: パッチ仕様済

### F5. Person schema for 屋山テディ
- File: `/会社概要/index.html` (and `/en/company/`)
- Action: Person schema を Organization と紐付け
- Status: パッチ仕様済

## Tier 2: 短期 (1-2週間)

### F6. footer の 3 カラム再構成
- 全ページの footer を サービス/Articles/会社情報 3 カラムに
- 内部リンクの hub-and-spoke 強化

### F7. /サービス/ をハブページに再構成
- 現状 1 枚で完結 → 7 サブ LP へのカード型ハブに

### F8. CTA 文言の置換
- 「お問い合わせ」「お見積もり」 → 「IRの伝わり方を相談」 → CV率改善

### F9. about-photo 外部画像化
- data:image/jpeg base64 → /assets/photos/founder.jpg
- HTML size 大幅削減 (既存 WIP に含まれる)

## Tier 3: 中期 (1ヶ月)

### F10. 全ページの inline CSS を共有 CSS 化
- /assets/jpinv.css に集約
- 全ページの HTML が 90% 削減

### F11. loading="lazy" 全画像
- compounders 系の画像が多いため特に効果大

### F12. WebP/AVIF 変換
- 主要画像を modern format に

### F13. Article schema with author
- 全記事に author=屋山テディ Person schema

### F14. EN サイトの search intent 再検証
- /en/ 配下を海外投資家視点で再点検

## Tier 4: 長期 (継続)

### F15. Substack 等外部記事との cross-link
- substack.com から jpinv.com への back-link 設計
- jpinv.com から substack 記事への link

### F16. GA4 / Search Console event tracking
- KW別のCV計測

### F17. Core Web Vitals monitoring
- LCP / CLS / INP の継続改善

### F18. 月次 KW ranking review
- 主要 KW での順位推移を月次レポート化
