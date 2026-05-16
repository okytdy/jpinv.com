# Content Strategy — jpinv.com / 2026-05-16

## 1. authority articles 全体方針

目的: 「海外IRの専門家」としてのEEAT 構築。
配信先: jpinv.com/articles/{slug}/。Substack に既存記事があれば双方向リンク。
頻度: 既存記事を最初に投入後、月1-2本の継続。

## 2. 6 本の article 詳細

### A1. なぜ「正しい英語」でも海外投資家に伝わらないのか
- URL: `/articles/why-correct-english-doesnt-reach/`
- Word count target: 1800-2400
- Sections:
  1. はじめに — 「英語の正確さ ≠ 投資家への伝達力」
  2. 投資家フレームと日本企業説明フレームのギャップ
  3. 「hedged で polite な英語」が投資家に与える印象 (具体例)
  4. KPI / 数値の文脈不足が引き起こす誤読
  5. capital allocation narrative の不足
  6. では何を整えるか — 4 つの観点
  7. CTA: 英文IRレビュー / 海外IR診断
- Internal links: english-review, diagnostic, disclosure-review

### A2. 海外投資家が最初の10分で見ていること
- URL: `/articles/first-10-minutes-overseas-investor/`
- Word count: 1500-2000
- Sections:
  1. 1on1 ミーティングの最初の 10 分間
  2. 投資家が確認している 3 つの要素
     a. capital allocation の優先順位
     b. unit economics (or core driver economics)
     c. management trajectory (continuity / commitment)
  3. 通訳越しでも読み取られているシグナル
  4. CFO/IR が 10 分以内に主導権を取るための準備
  5. CTA: 海外投資家面談支援 / 海外IR診断

### A3. 海外IRでよく起きるコミュニケーションの失敗5パターン
- URL: `/articles/common-overseas-ir-failures/`
- Word count: 1700-2200
- Sections (5 失敗パターン):
  1. Numbers without context — 数値の連発で物語が消える
  2. Hedged conclusions — 結論が "may" "could" "expected to" で曖昧
  3. KPI 不整合 — 開示 KPI と説明 KPI と内部 KPI のずれ
  4. Governance silence — 取締役会 / 報酬 / 後継者 への沈黙
  5. Capital allocation 不明確 — Cash, CapEx, Buyback, M&A の優先順位がない
  6. 改善するための 4 つの観点
  7. CTA: 海外IR診断 / 海外投資家向けIR支援

### A4. 英文IR資料で起きやすい誤解5選
- URL: `/articles/misreadings-in-english-ir/`
- Word count: 1500-2000
- Sections (5 誤解):
  1. "expect to" の確度ニュアンス (日本人は努力目標、投資家はガイダンス)
  2. "challenging" の文化的含意
  3. "may achieve" の hedge 過剰
  4. KPI の percentage point vs percent
  5. 「達成」「実現」の英訳における時制
  6. レビュー観点 4 つ
  7. CTA: 英文IRレビュー / 英文開示レビュー

### A5. 海外投資家向けIR readiness チェックリスト
- URL: `/articles/overseas-ir-readiness-checklist/`
- Word count: 1500-2000
- リードマグネット型: 12 項目チェックリスト
- 各項目に解説 + 例
- CTA は前面に: 海外IR診断 (= このチェックリストの拡張版)

### A6. 決算説明会通訳で変わる海外投資家の印象
- URL: `/articles/interpretation-changes-investor-perception/`
- Word count: 1500-2000
- Sections:
  1. 一般通訳 vs IR現場経験のある通訳者
  2. 投資家が通訳越しに判断している 4 つのこと
  3. よく起きる誤訳パターン (capital allocation, segment KPI, governance)
  4. 通訳と IR チームの事前すり合わせの 5 項目
  5. CTA: IRミーティング通訳支援 / 海外投資家面談支援

---

## 3. 記事制作スタイル

- 段落 3-5 文程度、過剰な箇条書きは避ける
- 「私は」「私たちは」型の subjective 一人称はやや控えめ
- 「観察してきた」「面談に立ち会ってきた」型の **実務観察** voice
- 具体的な架空ケース (匿名化) を 1-2 個必ず含める
- 「これは違法/不正/問題」型の批判的記述は避ける (上場企業相手にネガティブを出さない)
- 結論は「以下の 4 観点で点検することを推奨します」型で具体的アクションに着地

## 4. 記事の internal link 設計

各記事末尾に必ず:
- 関連 LP 2 つ (Primary + Secondary)
- 関連 article 1-2 つ

例 (A1):
```
[関連サービス]
- 英文IRレビュー (= /サービス/english-review/)
- 海外IR診断 (= /サービス/diagnostic/)

[関連 article]
- 英文IR資料で起きやすい誤解5選 (A4)
- 海外IRでよく起きる失敗5パターン (A3)
```

## 5. 記事の schema 設計

各記事の `<head>` に:
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{Title}",
  "description": "{meta description}",
  "image": "https://jpinv.com/assets/logo-jii-wordmark.svg",
  "datePublished": "2026-05-16",
  "dateModified": "2026-05-16",
  "author": {
    "@type": "Person",
    "name": "屋山テディ",
    "alternateName": "Teddy Okuyama",
    "jobTitle": "代表取締役",
    "url": "https://jpinv.com/会社概要/"
  },
  "publisher": {"@id": "https://jpinv.com/#organization"},
  "mainEntityOfPage": "https://jpinv.com/articles/{slug}/",
  "about": ["海外IR", "英文IR", "海外投資家", "投資家コミュニケーション"],
  "inLanguage": "ja"
}
```

## 6. /articles/ ハブページ

`/articles/index.html` に全 6 記事を一覧表示:
- 大カード (画像 / タイトル / 抜粋 / 公開日)
- カテゴリ別 filter (「英文IR」「面談」「通訳」「Disclosure」)
- 最新順

H1: `海外IRに関する考察｜実務観察から書く記事一覧`
Title: `Articles｜海外IRと英文IRに関する考察｜JII`

## 7. 公開後の運用

- 投稿即時: Search Console に submit
- 投稿1週間: 関連検索KWでの indexation 確認
- 投稿1ヶ月: KW ranking レビュー
- 必要なら **記事間 cross-link** を強化 (Pillar / cluster 型)

## 8. 将来の article 拡張案 (P2)

- 統合報告書の英文化で起きる典型ミス10選
- 海外 IR デイの設計
- JPX プライム市場 / TOPIX100 入り後の海外投資家対応
- アクティビスト株主と海外 IR の交差点
- ESG 開示英文化の落とし穴
- 中期経営計画英文 — what gets lost in translation
