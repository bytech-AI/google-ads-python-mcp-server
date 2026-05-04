---
description: より良いGAQLクエリを書くために使用
globs: 
alwaysApply: false
---
# Google広告クエリ言語（GAQL）ガイドライン

## 概要

Google広告クエリ言語（GAQL）は、Google Ads APIをクエリするための強力なツールで、以下を取得できます：

1. **リソース**とその関連する属性、セグメント、指標を`GoogleAdsService.Search`または`GoogleAdsService.SearchStream`を使用して取得
2. **メタデータ**：利用可能なフィールドとリソースに関する情報を`GoogleAdsFieldService`を使用して取得

## フィールドカテゴリ

効果的なGAQLクエリを構築するには、フィールドカテゴリを理解することが重要です：

1. **RESOURCE**：FROM句で使用できる主要エンティティ（例：`campaign`、`ad_group`）
2. **ATTRIBUTE**：リソースのプロパティ（例：`campaign.id`、`campaign.name`）。これらを含めると、リソースの関係に応じて結果がセグメント化される場合があります
3. **SEGMENT**：検索クエリを常にセグメント化するフィールド（例：`segments.date`、`segments.device`）
4. **METRIC**：検索クエリをセグメント化しないパフォーマンスデータフィールド（例：`metrics.impressions`、`metrics.clicks`）

## クエリ構造

GAQLクエリは以下のコンポーネントで構成されます：

```
SELECT
  <field_1>,
  <field_2>,
  ...
FROM <resource>
WHERE <condition_1> AND <condition_2> AND ...
ORDER BY <field_1> [ASC|DESC], <field_2> [ASC|DESC], ...
LIMIT <number_of_results>
```

### SELECT句

`SELECT`句はクエリ結果で返されるフィールドを指定します：

```
SELECT
  campaign.id,
  campaign.name,
  metrics.impressions,
  segments.device
```

`GoogleAdsField`メタデータで`selectable: true`とマークされているフィールドのみがSELECT句で使用できます。

### FROM句

`FROM`句はクエリ対象のプライマリリソースタイプを指定します。指定できるリソースは1つのみで、カテゴリが`RESOURCE`である必要があります。

```
FROM campaign
```

### WHERE句（オプション）

`WHERE`句は結果をフィルタリングする条件を指定します。`GoogleAdsField`メタデータで`filterable: true`とマークされているフィールドのみがフィルタリングに使用できます。

```
WHERE 
  campaign.status = 'ENABLED'
  AND metrics.impressions > 1000
  AND segments.date DURING LAST_30_DAYS
```

### ORDER BY句（オプション）

`ORDER BY`句は結果のソート方法を指定します。`GoogleAdsField`メタデータで`sortable: true`とマークされているフィールドのみがソートに使用できます。

```
ORDER BY metrics.impressions DESC, campaign.id
```

### LIMIT句（オプション）

`LIMIT`句は返される結果の数を制限します。

```
LIMIT 100
```

## フィールドメタデータの調査

利用可能なフィールドとそのプロパティを調査するには、`GoogleAdsFieldService`を使用します：

```
SELECT
  name,
  category,
  selectable,
  filterable,
  sortable,
  selectable_with,
  attribute_resources,
  metrics,
  segments,
  data_type,
  enum_values,
  is_repeated
WHERE name = "campaign.id"
```

理解すべき主要なメタデータプロパティ：

- **`selectable`**：フィールドがSELECT句で使用できるかどうか
- **`filterable`**：フィールドがWHERE句で使用できるかどうか
- **`sortable`**：フィールドがORDER BY句で使用できるかどうか
- **`selectable_with`**：このフィールドと一緒に選択可能なリソース、セグメント、指標のリスト
- **`attribute_resources`**：RESOURCEフィールドの場合、このリソースと一緒に選択可能でメトリクスをセグメント化しないリソースのリスト
- **`metrics`**：RESOURCEフィールドの場合、このリソースがFROM句にある時に選択可能な指標のリスト
- **`segments`**：RESOURCEフィールドの場合、このリソースを使用する時にメトリクスをセグメント化するフィールドのリスト
- **`data_type`**：WHERE句でフィールドと一緒に使用できる演算子を決定
- **`enum_values`**：ENUM型フィールドの可能な値のリスト
- **`is_repeated`**：フィールドが複数の値を含むことができるかどうか

## データ型と演算子

異なるフィールドデータ型は、WHERE句で異なる演算子をサポートします：

### 文字列フィールド
- `=`、`!=`、`IN`、`NOT IN`
- `LIKE`、`NOT LIKE`（大文字小文字を区別する文字列マッチング）
- `CONTAINS ANY`、`CONTAINS ALL`、`CONTAINS NONE`（繰り返しフィールド用）

### 数値フィールド
- `=`、`!=`、`<`、`<=`、`>`、`>=`
- `IN`、`NOT IN`

### 日付フィールド
- `=`、`!=`、`<`、`<=`、`>`、`>=`
- `DURING`（名前付き日付範囲と共に）
- `BETWEEN`（日付リテラルと共に）

### Enumフィールド
- `=`、`!=`、`IN`、`NOT IN`
- 値は`enum_values`にリストされているものと正確に一致する必要があります

### Booleanフィールド
- `=`、`!=`
- 値は`TRUE`または`FALSE`である必要があります

## 日付範囲

### リテラル日付範囲
```
WHERE segments.date BETWEEN '2020-01-01' AND '2020-01-31'
```

### 名前付き日付範囲
```
WHERE segments.date DURING LAST_7_DAYS
WHERE segments.date DURING LAST_14_DAYS
WHERE segments.date DURING LAST_30_DAYS
WHERE segments.date DURING LAST_90_DAYS
WHERE segments.date DURING THIS_MONTH
WHERE segments.date DURING LAST_MONTH
WHERE segments.date DURING THIS_QUARTER
```

### 日付関数
```
WHERE segments.date = YESTERDAY
WHERE segments.date = TODAY
```

## 大文字小文字の区別ルール

1. **フィールドとリソース名**：大文字小文字を区別（`campaign.id`であり`Campaign.Id`ではない）
2. **列挙値**：大文字小文字を区別（`'ENABLED'`であり`'enabled'`ではない）
3. **条件内の文字列リテラル**：
   - デフォルトでは大文字小文字を区別しない（`WHERE campaign.name = 'brand campaign'`）
   - 大文字小文字を区別するマッチングには`LIKE`を使用（`WHERE campaign.name LIKE 'Brand Campaign'`）

## 結果の並び替えと制限

### 並び替え
- 結果は1つ以上のフィールドで並び替え可能
- `ASC`（デフォルト）または`DESC`で方向を指定
- `sortable: true`とマークされているフィールドのみ使用可能

```
ORDER BY metrics.impressions DESC, campaign.id ASC
```

### 制限
- LIMITを使用して返される行数を制限
- 一貫したページネーションにはLIMITと一緒にORDER BYを常に使用
- 最大値はシステムに依存

```
LIMIT 100
```

## クエリ例

### 基本的なキャンペーンクエリ
```
SELECT
  campaign.id,
  campaign.name,
  campaign.status
FROM campaign
ORDER BY campaign.id
```

### 指標とフィルタリングを含むクエリ
```
SELECT
  campaign.id,
  campaign.name,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros
FROM campaign
WHERE 
  campaign.status = 'ENABLED'
  AND metrics.impressions > 1000
ORDER BY metrics.impressions DESC
LIMIT 10
```

### セグメントを含むクエリ
```
SELECT
  campaign.id,
  campaign.name,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions
FROM campaign
WHERE 
  segments.date DURING LAST_30_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY segments.date DESC, metrics.impressions DESC
```

### 属性リソースを含むクエリ
```
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  bidding_strategy.id,
  bidding_strategy.name,
  bidding_strategy.type
FROM campaign
WHERE campaign.status = 'ENABLED'
```

### フィールドメタデータクエリ
```
SELECT
  name,
  category,
  selectable,
  filterable,
  sortable,
  data_type,
  enum_values
WHERE name LIKE 'campaign.%'
```

## アセットクエリ

### アセットエンティティクエリ

`asset`エンティティをクエリすることで、アセットとその属性のリストを取得できます：

```
SELECT
  asset.id,
  asset.name,
  asset.resource_name,
  asset.type
FROM asset
```

### タイプ固有のアセット属性

アセットにはタイプに基づいてクエリできるタイプ固有の属性があります：

```
SELECT
  asset.id,
  asset.name,
  asset.resource_name,
  asset.youtube_video_asset.youtube_video_id
FROM asset
WHERE asset.type = 'YOUTUBE_VIDEO'
```

### 異なるレベルでのアセット指標

アセット指標は3つの主要なリソースを通じて利用可能です：

1. **ad_group_asset**：広告グループレベルでのアセット指標
2. **campaign_asset**：キャンペーンレベルでのアセット指標
3. **customer_asset**：顧客レベルでのアセット指標

広告グループレベルのアセット指標をクエリする例：

```
SELECT
  ad_group.id,
  asset.id,
  metrics.clicks,
  metrics.impressions
FROM ad_group_asset
WHERE segments.date DURING LAST_MONTH
ORDER BY metrics.impressions DESC
```

### 広告レベルのアセットパフォーマンス

アセットの広告レベルパフォーマンス指標は`ad_group_ad_asset_view`に集約されています。

**注意**：`ad_group_ad_asset_view`はアプリ広告に関連するアセットの情報のみを返します。

このビューには`performance_label`属性が含まれ、以下の値を取ります：
- `BEST`：最もパフォーマンスの良いアセット
- `GOOD`：パフォーマンスの良いアセット
- `LOW`：最もパフォーマンスの悪いアセット
- `LEARNING`：アセットにインプレッションはあるが、統計的に有意な結果はまだ出ていない
- `PENDING`：アセットにはまだパフォーマンス情報がない（審査中の可能性あり）
- `UNKNOWN`：このバージョンでは値が不明
- `UNSPECIFIED`：指定なし

広告レベルアセットパフォーマンスのクエリ例：

```
SELECT
  ad_group_ad_asset_view.ad_group_ad,
  ad_group_ad_asset_view.asset,
  ad_group_ad_asset_view.field_type,
  ad_group_ad_asset_view.performance_label,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions
FROM ad_group_ad_asset_view
WHERE segments.date DURING LAST_MONTH
ORDER BY ad_group_ad_asset_view.performance_label
```

### アセットソース情報

- `Asset.source`は変更可能なアセットに対してのみ正確です
- RSA（レスポンシブ検索広告）アセットのソースについては、`AdGroupAdAsset.source`を使用してください

## ベストプラクティス

1. **フィールド選択**：レスポンスサイズを削減しパフォーマンスを向上させるために、必要なフィールドのみを選択。

2. **フィルタリング**：関連するデータに結果を限定するために`WHERE`句でフィルタを適用。

3. **フィールドプロパティの確認**：クエリでフィールドを使用する前に、必要に応じてそれが選択可能、フィルタ可能、ソート可能であることをメタデータで確認。

4. **結果の並び替え**：一貫した結果を確保するために、特にページネーション使用時は`ORDER BY`を常に使用。

5. **結果の制限**：返される行数を制限しパフォーマンスを向上させるために`LIMIT`を使用。

6. **繰り返しフィールドの処理**：`is_repeated = true`のフィールドには、`CONTAINS ANY`、`CONTAINS ALL`、または`CONTAINS NONE`などの適切な演算子を使用。

7. **セグメンテーションの理解**：セグメントフィールドや特定の属性フィールドを含めると、結果で指標がセグメント化されることに注意。

8. **日付の処理**：日付セグメントでフィルタリングする際は、適切な日付関数と範囲を使用。

9. **ページネーション**：大きな結果セットの場合、レスポンスで提供されるページトークンを使用して後続のページを取得。

10. **Enum値の確認**：enumフィールドの場合、クエリで使用する前に`enum_values`プロパティで許可される値を確認。

これらのガイドラインに従い、GAQLフィールドのメタデータを理解することで、Google広告データを取得・分析するための効果的で効率的なGAQLクエリを作成できます。
