## 高度なGAQLクエリ例

### 1. 地理とデバイスのセグメンテーションによる多段階パフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  segments.geo_target_region,
  segments.device,
  segments.day_of_week,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.cost_per_conversion,
  metrics.conversion_rate,
  metrics.return_on_ad_spend
FROM ad_group
WHERE
  campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND segments.date DURING LAST_90_DAYS
  AND metrics.impressions > 100
ORDER BY
  segments.geo_target_region,
  segments.device,
  metrics.return_on_ad_spend DESC
LIMIT 1000
```

このクエリは、地理、デバイスタイプ、曜日別の包括的なパフォーマンス内訳を提供し、最高の広告費用対効果（ROAS）を牽引している特定の組み合わせを特定するのに役立ちます。

### 2. 入札戦略の効果分析

```sql
SELECT
  campaign.id,
  campaign.name,
  campaign.bidding_strategy_type,
  bidding_strategy.id,
  bidding_strategy.name,
  bidding_strategy.type,
  campaign.target_cpa.target_cpa_micros,
  campaign.target_roas.target_roas,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.average_cpc,
  metrics.cost_per_conversion
FROM campaign
WHERE
  campaign.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
  AND metrics.impressions > 0
ORDER BY
  campaign.bidding_strategy_type,
  segments.date
```

このクエリは、さまざまな自動入札アプローチを使用するキャンペーン間で主要パフォーマンス指標を比較することで、異なる入札戦略の効果を分析するのに役立ちます。

### 3. 品質スコア分析を含むランディングページ別広告パフォーマンス

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  ad_group_ad.ad.id,
  ad_group_ad.ad.final_urls,
  ad_group_ad.ad.type,
  ad_group_ad.ad.expanded_text_ad.headline_part1,
  ad_group_ad.ad.expanded_text_ad.headline_part2,
  ad_group_criterion.keyword.text,
  ad_group_criterion.quality_info.quality_score,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.post_click_quality_score,
  ad_group_criterion.quality_info.search_predicted_ctr,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.average_cpc,
  metrics.ctr
FROM ad_group_ad
WHERE
  campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND ad_group_ad.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
  AND metrics.impressions > 100
ORDER BY
  metrics.conversion_value DESC,
  ad_group_criterion.quality_info.quality_score DESC
```

このクエリは、ランディングページと品質スコアに関連した広告パフォーマンスを調査し、高パフォーマンスの広告クリエイティブとそれに関連するランディングページを特定するのに役立ちます。

### 4. インプレッションシェアと掲載位置指標を含むキーワードパフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  ad_group_criterion.criterion_id,
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.absolute_top_impression_percentage,
  metrics.top_impression_percentage,
  metrics.search_impression_share,
  metrics.search_rank_lost_impression_share,
  metrics.search_budget_lost_impression_share
FROM keyword_view
WHERE
  campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND ad_group_criterion.status = 'ENABLED'
  AND segments.date DURING LAST_90_DAYS
  AND metrics.impressions > 10
ORDER BY
  metrics.conversion_value DESC,
  metrics.search_impression_share ASC
```

このクエリは、パフォーマンスは良いがインプレッションシェアで制限されている可能性のあるキーワードを特定し、入札や予算調整の機会を示すのに役立ちます。

### 5. 複合オーディエンスセグメンテーションパフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  segments.audience.id,
  segments.audience.name,
  segments.audience.type,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.average_cpc,
  metrics.ctr,
  metrics.conversion_rate,
  metrics.value_per_conversion
FROM ad_group
WHERE
  campaign.advertising_channel_type = 'DISPLAY'
  AND campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND segments.date DURING LAST_90_DAYS
  AND segments.audience.id IS NOT NULL
ORDER BY
  segments.audience.type,
  metrics.conversion_value DESC
```

このクエリは、ディスプレイキャンペーン全体で異なるオーディエンスセグメントのパフォーマンスを分析し、最も価値のあるオーディエンスタイプを特定するのに役立ちます。

### 6. ショッピングキャンペーン商品パフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  segments.product_item_id,
  segments.product_title,
  segments.product_type_l1,
  segments.product_type_l2,
  segments.product_type_l3,
  segments.product_type_l4,
  segments.product_type_l5,
  segments.product_brand,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.ctr,
  metrics.conversion_rate,
  metrics.return_on_ad_spend
FROM shopping_performance_view
WHERE
  campaign.advertising_channel_type = 'SHOPPING'
  AND campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
  AND metrics.impressions > 0
ORDER BY
  metrics.return_on_ad_spend DESC
```

このクエリは、商品属性別のショッピングキャンペーンパフォーマンスの詳細な内訳を提供し、高パフォーマンスの商品と商品カテゴリを特定するのに役立ちます。

### 7. 入札調整分析を含む広告スケジュールパフォーマンス

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  ad_schedule_view.day_of_week,
  ad_schedule_view.start_hour,
  ad_schedule_view.end_hour,
  campaign_criterion.bid_modifier,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.ctr,
  metrics.conversion_rate,
  metrics.value_per_conversion
FROM ad_schedule_view
WHERE
  campaign.status = 'ENABLED' 
  AND segments.date DURING LAST_14_DAYS
ORDER BY
  ad_schedule_view.day_of_week,
  ad_schedule_view.start_hour
```

このクエリは、異なる広告スケジュール全体でパフォーマンスを分析し、適用されている入札調整と比較することで、スケジュールベースの入札調整の機会を特定するのに役立ちます。

### 8. クロスキャンペーンアセットパフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  asset.id,
  asset.type,
  asset.name,
  asset.text_asset.text,
  asset.image_asset.full_size.url,
  asset_performance_label,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.cost_micros,
  metrics.ctr
FROM asset_performance_label_view
WHERE
  campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY
  asset.type,
  metrics.conversions DESC
```

このクエリは、キャンペーン全体でアセット（画像、テキストなど）のパフォーマンスを分析し、高パフォーマンスのクリエイティブ要素を特定するのに役立ちます。

### 9. 地域入札調整分析を含む地理パフォーマンス

```sql
SELECT
  campaign.id,
  campaign.name,
  geographic_view.country_criterion_id,
  geographic_view.location_type,
  geographic_view.geo_target_constant,
  campaign_criterion.bid_modifier,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_micros,
  metrics.ctr,
  metrics.conversion_rate
FROM geographic_view
WHERE
  campaign.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY
  geographic_view.country_criterion_id,
  metrics.conversion_value DESC
```

このクエリは、異なる地理的位置全体でパフォーマンスを分析し、地域入札調整と比較することで、地理ベースの入札調整の機会を特定するのに役立ちます。

### 10. 高度な予算活用とパフォーマンス分析

```sql
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  campaign_budget.amount_micros,
  campaign_budget.total_amount_micros,
  campaign_budget.delivery_method,
  campaign_budget.reference_count,
  campaign_budget.has_recommended_budget,
  campaign_budget.recommended_budget_amount_micros,
  segments.date,
  metrics.cost_micros,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.conversion_value,
  (metrics.cost_micros * 1.0) / (campaign_budget.amount_micros * 1.0) AS budget_utilization_rate
FROM campaign
WHERE
  campaign.status IN ('ENABLED', 'PAUSED')
  AND segments.date DURING LAST_30_DAYS
ORDER BY
  segments.date DESC,
  budget_utilization_rate DESC
```

このクエリは、キャンペーン全体の予算活用を分析し、予算活用率の計算フィールドを使用して、常に予算を使い切っているキャンペーンや予算調整が必要なキャンペーンを特定するのに役立ちます。

## これらのクエリの実用的な活用方法

これらの高度なGAQLクエリは以下に役立ちます：

1. **パフォーマンストレンドの特定**：異なるディメンション（地理、時間、デバイスベース）でのトレンドを把握
2. **入札戦略の最適化**：さまざまな自動入札アプローチ間でパフォーマンスを比較
3. **品質スコアの改善**：ランディングページ、広告クリエイティブ、パフォーマンス指標の関係を分析
4. **インプレッションシェアの最大化**：高パフォーマンスのキーワードと広告グループ向け
5. **オーディエンスターゲティングの精緻化**：最も価値のあるオーディエンスセグメントを特定
6. **商品フィードの最適化**：商品レベルでパフォーマンスを分析してショッピングキャンペーンを改善
7. **広告スケジュールの微調整**：曜日と時間帯のパフォーマンス分析に基づく
8. **クリエイティブアセットの改善**：高パフォーマンスの画像、テキスト、その他のクリエイティブ要素を特定
9. **地理ターゲティングの調整**：異なる地域間のパフォーマンス差異に基づく
10. **予算配分の最適化**：広告費用対効果を最大化

