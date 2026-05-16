# Positioning 修正方針 — jpinv.com

## 1. 現状ポジショニング (2026-05-16 時点)

サイトは既に「**海外IR診断カード**」を中核ブランドとして整理されており、「翻訳会社」感は**ほぼない**。
ただし、以下のレイヤーで強化余地がある:

1. サービス LP の **粒度** — 現在は `/サービス/` 一枚で「診断カード」を説明。検索KWごとの LP がない。
2. 「**翻訳との違い**」をより明確に — 検索流入が「英訳」「翻訳」KW から発生したときの **転換**設計。
3. EEAT — 屋山テディ氏の **実務経験** を Person schema と About ページで強化。
4. 内部リンクの **semantic ハブ&スポーク** — authority 記事から LP への self-reinforcing 構造。

---

## 2. 排除/置換ガイドライン

### 2.1 直接排除する語 (現在の copy で発見されたら削除)
| 排除 | 理由 |
|------|------|
| 翻訳代行 | 翻訳会社認定リスク |
| 英訳代行 | 同上 |
| 格安翻訳 | brand 毀損 |
| 多言語対応 | 翻訳会社の常套句 |
| AI翻訳後編集 | 同上 |
| ネイティブチェック | 「品質保証」の翻訳業界用語 |
| ポストエディット | 翻訳業界用語 |
| 文字単価 | 翻訳業界の見積り体系 |
| 短納期 | 翻訳業界の常套句 |
| 翻訳料金 | 翻訳業界 |

### 2.2 置換ペア
| 旧 | 新 |
|----|----|
| 英訳 (動作) | 英文IRレビュー / 英文IR点検 |
| 翻訳 (名詞) | 英文IR資料 / 英文開示 |
| 翻訳サービス | IRコミュニケーション支援 |
| 翻訳品質 | 投資家伝達力 |
| ネイティブが対応 | 海外投資家との面談経験を持つ担当者 |
| 翻訳依頼 (CTA) | IRの伝わり方を相談 |
| 翻訳の流れ | 診断・レビューの進め方 |
| 翻訳実績 | 支援領域 |
| 多言語 | 海外投資家対応 |
| 専門用語の正確な訳 | 投資家フレームでの意味の正確性 |

### 2.3 強化すべき語
| 語 | 配置箇所 |
|----|----------|
| 海外投資家との対話 | Home Hero / About |
| IRコミュニケーション | Service LP / Footer tagline |
| 投資家視点 | 全 LP / 記事 |
| IRストーリー | Earnings / Disclosure LP |
| 英文開示品質 | Disclosure LP |
| 外国人投資家理解 | Meeting / IR support LP |
| IR伝達力 | English review / Diagnostic LP |
| 海外IR readiness | Diagnostic LP / Article |
| 投資家との情報非対称 | About / Authority Article |
| 資本市場ストーリー | About / IR support LP |
| capital allocation narrative | Articles, EN content |
| unit economics | Articles |
| capital market dialogue | EN content |

---

## 3. ページ別 positioning 調整

### 3.1 Home (`/`)
**現状の H1**: 「海外IR診断カード」(ブランド型)
**追加方針**: H1 はそのまま (ブランド浸透中)。sub-headline に
> 「海外投資家との対話を、可視化する」
を入れて IR communication 軸を明示。

Hero CTA は「診断を申し込む」「相談する」を維持。secondary に「英文IRレビューを見る」「面談支援を見る」を追加して新 LP への流入を作る。

### 3.2 `/サービス/` (Service overview)
**現状**: 海外IR診断カードの内容と進め方
**修正方針**: 7 つのサブ LP への **ハブページ** に再構成。各サブ LP へのカード型リンクを追加。
- 海外IR診断 → /サービス/diagnostic/
- 英文IRレビュー → /サービス/english-review/
- 海外投資家面談支援 → /サービス/meeting-support/
- ...etc

### 3.3 `/料金/`
positioning OK。CTA文言を「プランを相談する」→「**IRの伝わり方を相談する**」に微調整。

### 3.4 `/会社概要/`
EEAT 強化のため:
- Person schema (屋山テディ) を追加
- 「IR現場での実務観察」セクションを追加 (具体ケース、匿名化)
- 「個別 NDA / 案件は匿名化のみで公開」明記

### 3.5 `/お問い合わせ/`
RFQ form 前文を「翻訳依頼」表現から「IRの伝わり方相談」表現に転換 (master summary §9.2 参照)。

### 3.6 `/faq/`
- FAQPage schema を追加
- Q「翻訳会社との違いは？」「ネイティブチェックではないのか？」を新規追加 → 検索流入対策
- Q「英文IRレビューと英文IR診断の違いは？」を追加

### 3.7 `/compounders/`
positioning OK。authority section として維持。新 articles ハブとの **相互リンク** を追加:
- 「海外投資家との対話に関する考察」 → /articles/
- compounders 個別ページ末尾に「投資家フレームの解説」 → /articles/first-10-minutes-overseas-investor/

### 3.8 `/availability/`
positioning OK。footer link で他LPへの誘導を強化。

---

## 4. Footer (全ページ共通) の再構成

現状 footer の文言を確認できていないため、以下を**追加するべき**:

```
[サービス]               [Articles]                    [JIIについて]
- 海外IR診断             - なぜ正しい英語でも...       - 会社概要
- 英文IRレビュー         - 海外投資家が最初の10分... - 個別 NDA / 匿名化方針
- 英文開示レビュー       - 海外IRでよく起きる失敗     - お問い合わせ
- 海外投資家面談支援     - 英文IR資料で起きやすい... - 料金
- 決算説明資料レビュー   - IR readiness checklist    - FAQ
- 海外投資家向けIR支援   - 決算説明会通訳で変わる...
- IRミーティング通訳支援
```

`Japan Investor Interface Co., Ltd.` の正式社名 + 代表者 + 所在地は既に footer 内にある想定。

---

## 5. Hero copy 推奨 (Home)

```
EYEBROW: 海外IRコミュニケーション支援

H1 (mincho, large):
  海外投資家との対話を、
  可視化する。

SUB (smaller, mincho/sans-serif mix):
  海外投資家から見た自社IRを12項目・24点で診断。
  英文開示、投資家面談、資本市場ストーリーの改善点を、
  一枚のカードで可視化します。

CTA primary: 海外IR診断を依頼する
CTA secondary: 英文IRレビューを見る
```

H1 ブランド (海外IR診断カード) はナビ / セクション / OGP に維持しつつ、Hero H1 を **意図検索者向け** に調整するというハイブリッド。

---

## 6. Trust 信号 (EEAT 表面化)

各 LP / Home / About に共通する trust 表現:
- 「海外機関投資家との面談を、最も近くで観察してきた」 (既存)
- 「全プロジェクトで個別 NDA。案件は実名公開しません」
- 「翻訳の前段階で、何を伝えるべきかを整理する」 (差別化 statement)
- 「IR担当・経営企画・CFO・社長と一緒に進めます」 (対象明示)
- 「東京・大阪・オンライン対応」 (地理的補足)

---

## 7. Anti-pattern 集 (やってはいけない)

- 「最新AI翻訳エンジン搭載」「精度99%」型の数値マーケ
- 「最短即日対応」型のスピード訴求 (機関投資家相手の信頼は速度ではない)
- 競合翻訳会社との **直接比較表** (検索意図とずれる + 翻訳会社の土俵に降りる)
- 文字単価表示 (翻訳業界の価格表)
- 「お客様の声」型の architectural-style testimonial (匿名化が出来ない場合は不要)
- 多言語アイコン (英・中・韓...) 並びの表示 (多言語翻訳業者っぽくなる)

---

## 8. Tone & voice

全 LP / 記事 / Home に共通するトーン:
- **落ち着き**: 過剰な装飾、感嘆符、煽り文を避ける
- **実務感**: 「12項目・24点」「初回診断は10営業日」など具体的数値
- **観察者性**: 「〜と感じます」「〜と観察しています」型の文 (断定しすぎない)
- **二人称回避**: 「お客様」「皆様」より「上場企業のIR担当者」「面談に立ち会う社長」など実名カテゴリー
- **英文混在 OK**: capital allocation, unit economics, mgmt commentary などは敢えて英語表記 (投資家フレームの語であることを示す)

---

## 9. Title 戦略まとめ

各ページのtitle pattern:
- LP: `{KW}｜{差別化statement}｜JII`
- 記事: `{Title}｜{副題}｜JII`
- Home: `海外IR診断カード｜海外投資家目線のIR診断｜JII` (現状維持)

`JII` ブランド略号を全 title 末尾につける (ブランド学習)。

---
