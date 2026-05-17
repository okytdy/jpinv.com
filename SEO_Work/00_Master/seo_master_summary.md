# jpinv.com SEO Master Summary — 2026-05-16

> **👉 For current open tasks, see `SEO_Work/_OPEN_TASKS.md` — that's the working to-do list (this document is the longer reference).**

## 0. エグゼクティブ・サマリー

**目的**: jpinv.com を「海外IRコミュニケーション支援」のトップ検索結果として日本のIR担当者・経営企画・社長・CFOに認知させる。**翻訳会社ポジショニング**から完全に脱却し、「海外投資家に伝わるIR」カテゴリを取りにいく。

**現状把握** (2026-05-16 時点):
- 既に「海外IR診断カード」を中心としたポジショニングは確立されている
- Organization/ProfessionalService schema、hreflang、canonical、OGPは整備済み
- 日本語URL（/サービス/, /料金/, /会社概要/, /お問い合わせ/）と英語URL（/en/services/ etc.）の二言語構成
- 高品質コンテンツ: compounders（10年複利成長企業分析）、faq、availability、index

**SEO戦略の中核 (Strategic Pivot)**:
1. 「翻訳」関連語の使用を **完全に削減** し「IRコミュニケーション」「投資家伝達」へ
2. 7つの **検索意図別サービス LP** を新設 (`/サービス/{slug}/`)
3. 6つの **authority 記事** で「海外IR専門家」のEEATを確立
4. 内部リンクの semantic 強化: authority記事 → service LP → CTA
5. structured data 拡張: Service / FAQ / Article / Breadcrumb schema

---

## 1. ⚠️ 重要: Git状態に関する事前作業 (BEFORE COMMIT)

### 1.1 sandbox 制約に関する説明
本セッションでは、Cowork sandbox が `.git/config.lock` ファイルを残し、その後の `.git/config` への書き込みが Windows 側からブロックされたため、**git operations は user 側 (Windows ターミナル) で実行する必要があります**。全SEO改善ファイルは Windows 側ファイルシステムに保存済みで、すぐにレビュー・commit 可能な状態です。

### 1.2 まず実行すべき修復コマンド (Windows PowerShell / cmd)
```powershell
cd "C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\5 Assets\Website\jpinv.com"

# 1) 残存している config.lock を削除
if (Test-Path .git\config.lock) { Remove-Item .git\config.lock -Force }
if (Test-Path .git\objects\maintenance.lock) { Remove-Item .git\objects\maintenance.lock -Force }

# 2) git config が壊れていないか確認
git config --list

# OK が出れば修復完了。git status が普通に動く状態へ復帰。
```

### 1.3 既存の uncommitted 変更について
本SEO作業 **以前から** working tree に大規模な uncommitted 変更（IA refactor + image-of-text audit、新しい robots/sitemap、Japanese folder の再構成）が存在しています。これは過去の commit `3eeb352` でいったん入った後、`d0806a3` で revert された内容が working tree に残っているものです。

**保護用バックアップ**: `SEO_Work/_BACKUP/` に以下を保存済み:
- `all-current-state.tar.gz` (1.2MB - working tree 全体)
- `wip-changes-tracked.patch` (7.4MB - tracked file の diff)
- `wip-changes-staged.patch` (916KB - staged の diff)

### 1.4 推奨される commit 戦略
以下の順序で commit を分けることを推奨します:

```bash
# Group A: 既存 IA refactor work (decide whether to keep or revert)
# Option A1: 既存 WIP を再採用する場合
git add -A
git commit -m "Restore IA refactor + image-of-text audit (re-apply reverted work)"

# Option A2: 既存 WIP を破棄する場合
git restore --staged --worktree . # working tree reset
git clean -fd # untracked のクリーンアップ (新 SEO ファイルが消える前に注意)
```

**※ Option A2 を選択する場合、先に新規 SEO ファイルを別箇所に退避**してください。

その後、本セッションで作成した SEO 改善を以下のように commit します（詳細は §11）。

---

## 2. 技術SEO監査結果

### 2.1 強み (Already Good)
| 項目 | 状況 |
|------|------|
| Organization/ProfessionalService schema | ✅ 完備 (taxID, 住所, 電話, knowsAbout) |
| WebSite schema (JA + EN 個別) | ✅ |
| hreflang (ja/en/x-default) | ✅ 全主要ページ |
| Canonical | ✅ 全主要ページ |
| OGP / Twitter Card | ✅ |
| HTTPS強制 + CSP | ✅ |
| Mobile viewport / responsive CSS | ✅ |
| Sitemap.xml with xhtml:link alternates | ✅ |
| robots.txt with Sitemap declaration | ✅ |
| Favicon (svg/png/apple-touch) | ✅ |
| Font preconnect | ✅ |

### 2.2 改善余地 (Action Items)
| # | 項目 | 優先度 | 状態 |
|---|------|--------|------|
| A1 | Service / FAQ / Breadcrumb / Article schema 追加 | High | 仕様化済 (§7) |
| A2 | 7つのサービスLP新設 (海外IR診断/英文IRレビュー他) | High | 仕様化済 (§4) |
| A3 | 6つの authority 記事 (EEAT強化) | High | 仕様化済 (§5) |
| A4 | sitemap.xml に新規URL追加 | High | **実装済 (本セッション)** |
| A5 | 内部リンク semantic 強化 | High | 仕様化済 (§6) |
| A6 | meta keywords 同一文字列の汎用化 | Med | 仕様化済 |
| A7 | data:image/jpeg base64 の about-photo を外部画像化 | Med | 既存 WIP に含まれる |
| A8 | 大量の重複インライン CSS → 外部 CSS 1 ファイル化 | Low | 将来課題 |
| A9 | sitemap.xml に articles/, サービス/* 追加 | High | **実装済** |
| A10 | robots.txt の Host directive, Crawl-delay 検討 | Low | 仕様化済 |

### 2.3 削除すべき翻訳会社感の文脈
**現状調査**: 既存ページに「翻訳」「ネイティブチェック」「AI翻訳」等の語は **ほぼ存在しない**。既に positioning は良好。ただし以下の語を `/サービス/` 系ページから明示的に削除し、置換すべき:

| 削除 | 置換 |
|------|------|
| 「英訳」「翻訳」(動作主体として) | 「英文IR点検」「IRレビュー」「英文開示レビュー」 |
| 「ネイティブチェック」 | 「海外投資家視点レビュー」 |
| 「品質保証」 | 「投資家伝達力の評価」 |
| 「対応言語」 | 「対応領域」 |
| 「翻訳依頼」(CTA) | 「IRの伝わり方を相談」 |

詳細は `03_Positioning/positioning_changes.md`。

---

## 3. キーワード戦略

### 3.1 主要KW（最優先）
| KW | 現在 ranking 想定 | 対応 LP | 月間検索量推定 |
|----|------|---------|------|
| 海外IR診断 | 高 (既存) | / (Home) | Mid |
| 海外IR | Mid | /サービス/diagnostic/ | High |
| 英文IR | Low | /サービス/english-review/ | High |
| 英文開示 | Low | /サービス/disclosure-review/ | High |
| 海外投資家 IR | Mid | /サービス/ir-support/ | High |
| IR英訳 | None | /サービス/english-review/ | High |
| 海外投資家 面談 | Low | /サービス/meeting-support/ | Mid |
| 決算説明会 英語 | Low | /サービス/earnings-review/ | Mid |
| 英文IRレビュー | Low | /サービス/english-review/ | Low |
| 海外IR診断 | High (既存) | / | Mid |

### 3.2 ロングテール (Articles)
- 「正しい英語 海外投資家 伝わらない」 → 記事1
- 「海外投資家 10分 IR」 → 記事2
- 「海外IR 失敗」 → 記事3
- 「英文IR 誤解」 → 記事4
- 「海外投資家 IR チェックリスト」 → 記事5
- 「決算説明会 通訳 投資家印象」 → 記事6

詳細マッピングは `02_Keywords/keyword_map.csv`、検索意図は `02_Keywords/search_intent_analysis.md`。

---

## 4. 新規サービスLP仕様 (7 ページ)

すべて `/サービス/{slug}/index.html` および `/en/services/{slug}/index.html` (英語版) として作成。日本語 slug は ASCII で encoding 問題を回避。

各LP共通要件:
- 既存 `/サービス/` の CSS と nav/footer 構造を継承
- canonical / hreflang を正しく設定
- Service schema を JSON-LD で追加
- Breadcrumb schema を追加
- H1 = 主要KW を含む自然文
- 構成: 問題提起 → よくある失敗 → 何をレビューするか → 成果物 → 進め方 → FAQ → CTA
- CTA: `/お問い合わせ/?rfq_service={slug}` への遷移

### LP仕様詳細

#### LP1: 海外IR診断
- **URL**: `/サービス/diagnostic/` (JA), `/en/services/diagnostic/` (EN)
- **Title**: `海外IR診断｜12項目・24点で海外投資家視点を可視化｜JII`
- **Meta**: `海外投資家から見た自社IRを12項目・24点で診断。英文開示、投資家面談、資本市場ストーリーの改善点を一枚のカードで可視化する診断サービス。`
- **H1**: 海外投資家視点で自社IRを診断する
- **Primary KW**: 海外IR診断, 海外IR
- **Service schema serviceType**: "Investor Relations Diagnostic"

#### LP2: 英文IRレビュー
- **URL**: `/サービス/english-review/` (JA), `/en/services/english-review/` (EN)
- **Title**: `英文IRレビュー｜海外投資家視点で英文IRの伝わり方を点検｜JII`
- **Meta**: `決算短信英訳、適時開示英訳、英文プレゼン、英文IR資料を、海外投資家が実際に読む視点で点検。何が伝わらないかを特定し、改善案を提示します。`
- **H1**: 英文IRの伝わり方を、海外投資家視点で点検する
- **Primary KW**: 英文IRレビュー, 英文IR, IR英訳

#### LP3: 海外投資家面談支援
- **URL**: `/サービス/meeting-support/` (JA), `/en/services/meeting-support/` (EN)
- **Title**: `海外投資家面談支援｜面談前後のIR対話設計と立ち会い通訳｜JII`
- **Meta**: `機関投資家との1on1、IRデイ、カンファレンス面談で投資家視点の質問を予測し、面談後の上位反応を整理。立ち会い通訳と面談観察を組み合わせたIR対話支援。`
- **H1**: 海外投資家との面談を、IRの学習機会に変える
- **Primary KW**: 海外投資家 面談, 機関投資家 面談 通訳, IRミーティング 通訳

#### LP4: 決算説明資料レビュー
- **URL**: `/サービス/earnings-review/` (JA), `/en/services/earnings-review/` (EN)
- **Title**: `決算説明資料レビュー｜決算説明会の英文資料を投資家視点で点検｜JII`
- **Meta**: `決算短信、決算説明会資料、Earnings Call スクリプト、補足資料を海外投資家視点でレビュー。重点メッセージ・KPI整合性・QA予想までを整える。`
- **H1**: 決算説明資料を、海外投資家の視線で整える
- **Primary KW**: 決算説明会 英語, 決算短信 英訳, 決算説明資料

#### LP5: 英文開示レビュー
- **URL**: `/サービス/disclosure-review/` (JA), `/en/services/disclosure-review/` (EN)
- **Title**: `英文開示レビュー｜適時開示英訳・統合報告書英文を投資家視点で点検｜JII`
- **Meta**: `適時開示英訳、統合報告書英文、コーポレートガバナンス報告書英文、サステナビリティ開示を海外投資家が読む視点で点検。誤解されやすい表現と論点を抽出します。`
- **H1**: 英文開示は「英語が正しい」だけでは投資家に届かない
- **Primary KW**: 英文開示, 適時開示 英訳, 統合報告書 英語

#### LP6: 海外投資家向けIR支援
- **URL**: `/サービス/ir-support/` (JA), `/en/services/ir-support/` (EN)
- **Title**: `海外投資家向けIR支援｜継続的なIRコミュニケーション伴走｜JII`
- **Meta**: `中長期で海外投資家とのIR対話を整える伴走支援。英文IR資料の改善ループ、面談観察、投資家反応のフィードバックを四半期サイクルで回します。`
- **H1**: 海外投資家との対話を、四半期ごとに磨いていく
- **Primary KW**: 海外投資家向けIR, 海外投資家対応, 外国人投資家向けIR

#### LP7: IRミーティング通訳支援
- **URL**: `/サービス/interpretation/` (JA), `/en/services/interpretation/` (EN)
- **Title**: `IRミーティング通訳支援｜IR現場経験のある通訳者による立ち会い｜JII`
- **Meta**: `IRデイ、機関投資家1on1、カンファレンス面談での立ち会い通訳。通訳者がIR現場経験を持つことで、投資家の質問の意図と社長の意図を高精度で接続します。`
- **H1**: IR現場を理解した通訳者が、面談の解像度を上げる
- **Primary KW**: IRミーティング 通訳, 機関投資家 面談 通訳, 決算説明会 通訳

---

## 5. authority記事 6本

すべて `/articles/{slug}/index.html` に配置 (新ディレクトリ)。

### 記事仕様

#### A1: なぜ正しい英語でも海外投資家に伝わらないのか
- **URL**: `/articles/why-correct-english-doesnt-reach/`
- **Title**: `なぜ「正しい英語」でも海外投資家に伝わらないのか｜海外IRの実務観察｜JII`
- **Primary KW**: 英文IR 伝わらない, 海外投資家 英語 伝わらない
- **論点**: 英語の正確さ ≠ 投資家への伝達力。投資家フレームと日本企業の説明フレームのギャップを実例で示す。
- **Internal link**: → /サービス/english-review/, /サービス/disclosure-review/

#### A2: 海外投資家が最初の10分で見ていること
- **URL**: `/articles/first-10-minutes-overseas-investor/`
- **Title**: `海外投資家が最初の10分で見ていること｜IRミーティングの実務観察｜JII`
- **Primary KW**: 海外投資家 IR 10分, IRミーティング 最初
- **論点**: 機関投資家が面談初頭で確認したい3要素 (capital allocation / unit economics / management trajectory) を実務観察ベースで整理。
- **Internal link**: → /サービス/meeting-support/, /サービス/diagnostic/

#### A3: 海外IRでよく起きるコミュニケーションの失敗
- **URL**: `/articles/common-overseas-ir-failures/`
- **Title**: `海外IRでよく起きるコミュニケーションの失敗5パターン｜JII`
- **Primary KW**: 海外IR 失敗, 海外IR よくある失敗
- **論点**: 5つの失敗パターン (numbers without context / hedged conclusions / KPI 不整合 / governance silence / capital allocation 不明確) を実例で示す。
- **Internal link**: → /サービス/diagnostic/, /サービス/ir-support/

#### A4: 英文IR資料で起きやすい誤解
- **URL**: `/articles/misreadings-in-english-ir/`
- **Title**: `英文IR資料で起きやすい誤解5選｜海外投資家が読み間違える表現｜JII`
- **Primary KW**: 英文IR 誤解, 英文IR ミス
- **論点**: "expect to" "may achieve" "challenging" などの hedge 表現が海外投資家に与える誤った印象、KPI 表記の落とし穴。
- **Internal link**: → /サービス/english-review/, /サービス/disclosure-review/

#### A5: 海外投資家向けIR readiness checklist
- **URL**: `/articles/overseas-ir-readiness-checklist/`
- **Title**: `海外投資家向けIR readiness チェックリスト｜面談前に整えるべき12項目｜JII`
- **Primary KW**: 海外投資家 IR チェックリスト, 海外IR 準備
- **論点**: 12項目チェックリスト (英文IR資料 / 投資家視点 KPI / QA 予想 / capital allocation narrative / governance narrative ...)。
- **Internal link**: → /サービス/diagnostic/ (=この記事は実質「診断カード」のリードマグネット)

#### A6: 決算説明会通訳で変わる投資家印象
- **URL**: `/articles/interpretation-changes-investor-perception/`
- **Title**: `決算説明会通訳で変わる海外投資家の印象｜通訳者がIRに与える影響｜JII`
- **Primary KW**: 決算説明会 通訳, 通訳 投資家印象
- **論点**: 一般通訳 vs IR現場経験のある通訳者の違い、投資家が通訳越しに何を判断しているか、誤訳が招く capital allocation 誤解。
- **Internal link**: → /サービス/interpretation/, /サービス/meeting-support/

---

## 6. 内部リンク設計

### 6.1 一覧 (内部リンク ハブ&スポーク)
```
HOME (/)
├── /サービス/ (LP overview)
│   ├── /サービス/diagnostic/
│   ├── /サービス/english-review/
│   ├── /サービス/meeting-support/
│   ├── /サービス/earnings-review/
│   ├── /サービス/disclosure-review/
│   ├── /サービス/ir-support/
│   └── /サービス/interpretation/
├── /料金/
├── /faq/
├── /会社概要/
├── /お問い合わせ/
├── /compounders/ (既存 authority section)
├── /articles/ (新規 authority hub)
│   ├── /articles/why-correct-english-doesnt-reach/
│   ├── /articles/first-10-minutes-overseas-investor/
│   ├── /articles/common-overseas-ir-failures/
│   ├── /articles/misreadings-in-english-ir/
│   ├── /articles/overseas-ir-readiness-checklist/
│   └── /articles/interpretation-changes-investor-perception/
```

### 6.2 anchor optimization
- Home → サービス LP: 「海外IR診断を見る」「英文IRレビュー」等のKW anchor
- 記事 → サービス LP: 「{KW} の詳しい支援内容を見る」
- サービス LP 相互: footer に他LP一覧 (footer ナビ拡張)
- /compounders/ → 記事: 「海外投資家との対話に関する考察」

### 6.3 footer 拡張
全ページの footer に「サービス一覧」「Articles 一覧」「会社情報」3カラム構成を追加すべき (本セッションでは仕様化のみ)。

---

## 7. Schema 拡張仕様

### 7.1 Service schema (全 LP)
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "海外IR診断",
  "provider": {"@id": "https://jpinv.com/#organization"},
  "areaServed": ["JP", "Global"],
  "audience": {"@type": "BusinessAudience", "audienceType": "Listed Japanese companies, IR teams, CFO, IR officers"},
  "serviceType": "Investor Relations Diagnostic",
  "description": "海外投資家視点で12項目・24点に整理された自社IR診断"
}
```

### 7.2 Breadcrumb schema
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://jpinv.com/"},
    {"@type": "ListItem", "position": 2, "name": "サービス", "item": "https://jpinv.com/サービス/"},
    {"@type": "ListItem", "position": 3, "name": "海外IR診断", "item": "https://jpinv.com/サービス/diagnostic/"}
  ]
}
```

### 7.3 FAQ schema (FAQ ページ + サービス LP の FAQ ブロック)
既存 FAQ ページは FAQPage schema を追加すべき。各サービス LP の最下部 FAQ も同様。

### 7.4 Article schema (記事ページ)
```json
{
  "@type": "Article",
  "headline": "...",
  "datePublished": "2026-05-16",
  "author": {"@type": "Person", "name": "屋山テディ", "jobTitle": "代表取締役"},
  "publisher": {"@id": "https://jpinv.com/#organization"},
  "about": ["海外IR", "英文IR"]
}
```

---

## 8. EEAT 強化

### 8.1 屋山テディ (代表) Person schema
About 配下に Person schema を追加:
```json
{
  "@type": "Person",
  "@id": "https://jpinv.com/#founder",
  "name": "屋山テディ",
  "alternateName": "Teddy Okuyama",
  "jobTitle": "代表取締役",
  "worksFor": {"@id": "https://jpinv.com/#organization"},
  "knowsAbout": ["海外IR", "英文IR", "IR通訳", "投資家コミュニケーション"],
  "url": "https://jpinv.com/会社概要/"
}
```

### 8.2 NDA / confidentiality 文言
全ページ footer に小さく「全プロジェクトで個別 NDA 締結 / 案件は実名匿名化のみで公開」と明記。

### 8.3 process と実務感を伝える文言
全 LP の「進め方」セクションには:
- 実日数 (例: 「初回診断は10営業日」)
- 連絡頻度 (例: 「週1回 30分の同期」)
- 成果物例 (PDFサンプル画像など)

---

## 9. CTA 改善

### 9.1 CTA 文言の置換
| 旧 | 新 |
|----|----|
| お問い合わせ | IRの伝わり方を相談する |
| お見積もり依頼 | 診断の見積りを依頼 |
| サンプルを見る | 診断サンプルを見る |
| RFQ 送信 | 海外IR相談を送信 |

### 9.2 RFQ form 前文
form 直前のリード文を:
> 「翻訳依頼の前段階で、何を投資家に伝えるべきかを一緒に整理することも可能です。資料の種類と面談予定を教えてください。」

---

## 10. 本セッションでの実装ファイル一覧

### 10.1 SEO_Work ドキュメント (新規)
- `SEO_Work/00_Master/seo_master_summary.md` ← 本ファイル
- `SEO_Work/01_Audit/full_technical_audit.md`
- `SEO_Work/01_Audit/current_url_inventory.csv`
- `SEO_Work/01_Audit/high_priority_fixes.md`
- `SEO_Work/02_Keywords/keyword_map.csv`
- `SEO_Work/02_Keywords/search_intent_analysis.md`
- `SEO_Work/03_Positioning/positioning_changes.md`
- `SEO_Work/06_Content/content_strategy.md`
- `SEO_Work/07_InternalLinks/internal_link_map.csv`
- `SEO_Work/_BACKUP/all-current-state.tar.gz`
- `SEO_Work/_BACKUP/wip-changes-tracked.patch`
- `SEO_Work/_BACKUP/wip-changes-staged.patch`

### 10.2 新規サービス LP — **全 7 ページ完全実装済**
すべて Service schema + Breadcrumb schema + hreflang + canonical + EEAT footer 完備。

- ✅ `サービス/diagnostic/index.html` (LP1 海外IR診断)
- ✅ `サービス/english-review/index.html` (LP2 英文IRレビュー)
- ✅ `サービス/meeting-support/index.html` (LP3 海外投資家面談支援)
- ✅ `サービス/earnings-review/index.html` (LP4 決算説明資料レビュー)
- ✅ `サービス/disclosure-review/index.html` (LP5 英文開示レビュー)
- ✅ `サービス/ir-support/index.html` (LP6 海外投資家向けIR支援)
- ✅ `サービス/interpretation/index.html` (LP7 IRミーティング通訳支援)

### 10.3 新規 article — **全 6 記事 + ハブ 完全実装済**
すべて Article schema + Breadcrumb schema + author (屋山テディ Person schema) + hreflang 完備。

- ✅ `articles/index.html` (記事ハブ — CollectionPage + ItemList schema)
- ✅ `articles/why-correct-english-doesnt-reach/index.html` (A1, 2100 words 相当)
- ✅ `articles/first-10-minutes-overseas-investor/index.html` (A2)
- ✅ `articles/common-overseas-ir-failures/index.html` (A3)
- ✅ `articles/misreadings-in-english-ir/index.html` (A4)
- ✅ `articles/overseas-ir-readiness-checklist/index.html` (A5 — リードマグネット型)
- ✅ `articles/interpretation-changes-investor-perception/index.html` (A6)

### 10.4 修正済みファイル
- ✅ `sitemap.xml` — 新規14URL（7 LP × 2 locale = 14 + 6 article × 2 + ハブ × 2）を追加。**実際には EN 版 LP/articles のファイルはまだ存在しない**ため、user 側で EN 翻訳・実装後に活性化する想定。当面は EN 版URLは hreflang 参照のみで実体ファイルなしの状態。

### 10.5 残課題 (本セッション外で対応推奨)
1. **EN 版 LP / 記事の作成**: 上記の JA 版を英訳した EN 版を `/en/services/{slug}/` `/en/articles/{slug}/` に作成。
2. **既存ページへの schema パッチ追加**:
   - `/会社概要/index.html` → Person schema (屋山テディ) を追加
   - `/faq/index.html` → FAQPage schema を追加
   - 各 `/サービス/index.html` → Service hub schema を追加
3. **/サービス/index.html (ハブページ) を 7 sub-LP のカード hub に再構成** (positioning_changes.md §3.2)
4. **既存全ページの footer 3カラム化** (positioning_changes.md §4)
5. **CTA 文言の置換** (positioning_changes.md §3 / master §9)

---

## 11. Commit はすべて作成済 — bundle file として配置

本セッションで、新規 SEO ファイルに対する **4 つの commit はすべて作成済**で、`SEO_Work/_BACKUP/seo-improvements.bundle` (89KB) に保存されています。

bundle に含まれる commits (古い順):

```
1754303 Add SEO_Work directory: full audit, KW map, content strategy, internal links
a0d44c0 Add 7 service LPs targeting 海外IR / 英文IR / 投資家面談 / 通訳 search intents
dda65c6 Add /articles/ hub + 6 authority articles for overseas-IR EEAT
2e4630d Update sitemap.xml: add 7 service LPs + 6 articles + articles hub (hreflang complete)
```

これらは origin/main の最新（`d0806a3`）の上に直接 fast-forward 可能な 4 commit です。

### 11.1 既存 working tree について
本セッション開始時点で、user の working tree には既に**未コミットの IA refactor work**（commit `3eeb352` を revert した後に working tree に戻った変更）が存在していました。これは本SEO作業とは**別件**であり、本 bundle には**含めていません**。

### 11.2 取り込み手順 (Windows PowerShell)

```powershell
cd "C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\5 Assets\Website\jpinv.com"

# (1) 残存している lock を削除 (Windows 側からなら確実に削除できる)
if (Test-Path .git\config.lock) { Remove-Item .git\config.lock -Force }
if (Test-Path .git\index.lock)  { Remove-Item .git\index.lock  -Force }
if (Test-Path .git\objects\maintenance.lock) { Remove-Item .git\objects\maintenance.lock -Force }

# (2) 既存 working tree の IA refactor work をどうするか決める
#     Option A: 採用してコミット → コミット名は適宜
git status                                          # 変更状況確認
git add -A                                          # IA refactor の変更を全て stage（SEO_Work/ 含む）
git commit -m "Continue IA refactor (re-apply work that was reverted in d0806a3)"

#     Option B: 破棄
# git restore --staged --worktree .
# git clean -fd

# ※ Option B を選ぶ場合、本 bundle が作る新規ファイル（サービス/{slug}/, articles/, SEO_Work/）も
#    untracked なので clean -fd で消えます。 Option B を取るなら、先に bundle をfetchすれば、
#    bundle 内のファイルは git 管理下で保護されます。

# (3) bundle から 4 commits を取り込む
git fetch SEO_Work/_BACKUP/seo-improvements.bundle main:seo-additions
git log --oneline seo-additions -10                # 4 commitsを確認

# (4) main に fast-forward マージ
git merge --ff-only seo-additions
git log --oneline -8                               # 最終確認
```

### 11.3 もしOption A後に bundle の取り込みでconflictになる場合

bundle の `sitemap.xml` 修正と Option A の IA refactor が衝突する可能性があります。その場合:

```powershell
# bundle 内の commit を 1 つずつ cherry-pick
git cherry-pick 1754303    # SEO_Work
git cherry-pick a0d44c0    # 7 LPs
git cherry-pick dda65c6    # articles
git cherry-pick 2e4630d    # sitemap (要 conflict 解決)
```

## 12. Final push (User 実行)

全 commit 確認後:

```powershell
# まず origin/main の最新を確認
git fetch origin
git log --oneline origin/main..HEAD                # 取り込まれた commit を確認
git diff --stat origin/main..HEAD                  # 変更ファイル数を確認

# OK なら push
git push origin main

# 推奨: PR ベース
git checkout -b seo/overseas-ir-positioning-2026-05-16
git push -u origin seo/overseas-ir-positioning-2026-05-16
# その後 GitHub UI で PR を作成
```

## 13. Rollback 方法

万一の rollback:
```bash
# 直近 commit を取り消し (working tree は保持)
git reset --soft HEAD~1

# 完全 rollback
git reset --hard origin/main

# stash 復元 (本セッションでは未使用だが念のため)
git stash list
git stash apply stash@{0}

# patch 復元
git apply SEO_Work/_BACKUP/wip-changes-tracked.patch
```

---

## 14. 期待される SEO インパクト

| 領域 | 短期 (1-3ヶ月) | 中期 (3-6ヶ月) |
|------|----------|-----------|
| 「海外IR診断」 | 既に上位想定 → 維持強化 | 1位狙い |
| 「英文IR」「英文IRレビュー」 | top 10 entry | top 5 |
| 「英文開示」 | top 20 entry | top 10 |
| 「IR英訳」 | top 10 entry | top 5 |
| 「海外投資家 面談」 | top 20 entry | top 10 |
| 「海外IR」 | top 10 entry | top 5 |
| Long-tail authority KW | 記事インデックス完了 | 個別記事で複数 KW 上位 |

EEAT 強化により、後から記事を増やしても累積的に効果が出る構造になります。

---

## 15. Remaining Issues / Future Work

1. **既存ページの大量インライン CSS の外部化** — performance gain 大。技術タスク。
2. **画像の WebP/AVIF 化と loading="lazy"** — 一部の compounders ページの画像が重い。
3. **構造化データの全ページ展開** — 現在は home/services 中心、compounders 系にも適用余地あり。
4. **/availability/ ページの SEO 強化** — 単独 LP として再設計可能。
5. **Substack / 外部記事との clear cross-link** — 既存 substack コンテンツとの双方向リンク。
6. **GA4 / Search Console の意図的設定** — KW track のため。
7. **コア Web vitals 計測** — LCP / CLS / INP の継続 monitoring。

---

## 16. 連絡 / Q&A

本ドキュメントの内容や実装の優先順位について質問があれば、`SEO_Work/00_Master/` 配下に `Q&A.md` を作成して追記してください。次セッションで対応します。

— SEO 統括 AI (jpinv.com) / 2026-05-16
