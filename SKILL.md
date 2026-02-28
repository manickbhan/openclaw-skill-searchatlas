---
name: searchatlas
description: "Agentic Omnichannel Marketing MCP — 112 AI-driven marketing tools across SEO, GEO, Google Ads, local SEO, GMB, content generation, digital PR, link building, and website creation. One MCP endpoint. Every marketing channel."
homepage: https://searchatlas.com
metadata: { "openclaw": { "emoji": "🔍", "requires": { "env": ["MCP_API_KEY"] }, "primaryEnv": "MCP_API_KEY" } }
---

# SearchAtlas — Agentic Omnichannel Marketing MCP

The first agentic omnichannel marketing platform powered by the Model Context Protocol. 112 AI-driven marketing tools across SEO, GEO, Google Ads, local SEO, GMB optimization, content generation, digital PR, link building, and website creation — all through one MCP endpoint.

**One marketing agent. Every channel. Total automation.**

## MCP Server

```
Endpoint: https://mcp.searchatlas.com/api/v1/mcp
Protocol: JSON-RPC 2.0
Auth:     X-API-KEY header (set MCP_API_KEY env var)
```

### Calling a Tool

```bash
curl -s -X POST "https://mcp.searchatlas.com/api/v1/mcp" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"<TOOL_NAME>","arguments":{"op":"<OPERATION>","params":{...}}}}'
```

### Listing All 112 Tools

```bash
curl -s -X POST "https://mcp.searchatlas.com/api/v1/mcp" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Golden Rules

1. **Schema Discovery First** — Always send an empty call to discover the real schema. Documentation may have wrong parameter names. The MCP server returns the expected schema in error responses.
2. **Read Error Messages** — Distinguish between param validation errors (wrong param names), auth blocks ("credentials not provided"), internal server errors (backend down), and "tool not found" (name changed — use `tools/list`).
3. **Don't Fabricate Timelines** — Use actual API timestamps, never guess durations.
4. **Poll Async Tasks** — Many operations return a `task_id`. Poll with `get_otto_task_status` or `get_otto_ppc_task_status` until status = `SUCCESS`. Poll every 5-10 seconds.
5. **Watch for Tool Name Collisions** — Multiple tools share the same short name. The MCP server routes to the first match. Known collisions: `project_management`, `knowledge_graph`, `content`, `distribution`, `quota`, `projects`.
6. **Never Invent Tool Names** — If `tools/list` doesn't show it, it doesn't exist.

## Tool Arsenal (112 Tools Across 12 Categories)

### OTTO SEO (15 tools)
On-page optimization, schema markup, knowledge graphs, instant indexing, wildfire internal linking, AI recommendations, technical audits.

| Tool | Key Operations |
|------|----------------|
| `project_management` | list_otto_projects, get_otto_project_details, engage/freeze/unfreeze projects, verify installation |
| `seo_analysis` | generate_bulk_recommendations, generate_single_recommendation, get_project_issues_summary |
| `seo_deployment` | deploy_seo_fixes, rollback_seo_fixes |
| `schema_markup` | deploy/edit/generate page-level and domain-level schema |
| `knowledge_graph` | get/update knowledge graph, update_refine_prompt |
| `indexing_management` | add_custom_indexing_urls, select_urls_for_indexing, toggle_sitemap_indexing |
| `wildfire` | deploy/undeploy wildfire links, list pending outlinks and backlinks |
| `suggestion_management` | edit/delete/export SEO suggestions |
| `audit_management` | create_audit, get_site_audit_by_id |
| `OTTO_Installations` | install/uninstall Cloudflare worker, get installation guide |
| `recrawl_management` | trigger_recrawl |
| `quota_management` | get_otto_quota, show_otto_quota |
| `task_management` | get_otto_task_status, otto_wait |
| `image_upload` | upload_image |
| `attachments` | view_uploaded_attachment |

### PPC / Google Ads (13 tools)
Full Google Ads campaign lifecycle: business setup, product discovery, keyword clustering, ad creation, bid management.

| Tool | Key Operations |
|------|----------------|
| `business_crud` | create/list/get/update/delete PPC businesses |
| `business_mgmt` | discover_products, generate_form_suggestions, geo_search, create_products |
| `ads_account_crud` | get/list/update/delete Google Ads accounts |
| `ads_account_mgmt` | connect_new_account, check_conversions, sync_from_google |
| `product_crud` | add_product, generate_product_details, review_products, bulk_create_keyword_clusters |
| `product_mgmt` | bulk_approve/delete/restore products, bulk_create_campaign_budget |
| `campaign` | import_campaigns, list_campaigns_with_metrics, send_to_google_ads_account |
| `keyword_cluster` | bulk_approve/create_ad_contents/delete keyword clusters |
| `keyword` | list_keyword_performance |
| `ad_group` | list ad groups with metrics and performance |
| `ad_content` | bulk_approve/delete ad contents, update_ad_content |
| `task` | get_otto_ppc_task_status, otto_wait |
| `brand_vault` | shared — see BrandVault below |

### Site Explorer (8 tools)
Competitor intelligence, organic keyword gaps, backlink analysis, keyword research.

| Tool | Key Operations |
|------|----------------|
| `projects` | create/delete/get/list site explorers |
| `organic` | get_organic_keywords, get_organic_competitors, get_organic_pages, position_changes |
| `backlinks` | get_site_backlinks, referring_domains, anchor_text_analysis, link_network_graph |
| `analysis` | get_historical_trends, keyword_intent_analysis, position_distribution, serp_features |
| `adwords` | get_adwords_keywords, competitors, copies, pages, position_changes |
| `brand_signals` | retrieve/submit brand_signal_score |
| `holistic_audit` | get_holistic_seo_pillar_scores |
| `keyword_research` | create/list/search keyword research projects, get_serp_overview |

### Content Genius (7 tools)
AI article generation, topical authority maps, DKN, publishing to 11+ CMS platforms.

| Tool | Key Operations |
|------|----------------|
| `content_generation` | auto_generate_article, create_content_instance, generate_complete_article, topic_suggestions |
| `article_management` | edit/export/regenerate articles, run_content_grader, insert_article_links |
| `content_retrieval` | advanced_filter_articles, search_articles, get_high_quality_articles |
| `content_publication` | publish/schedule to WordPress, Shopify, HubSpot, Drupal and 7+ more CMS |
| `topical_maps` | create_topical_map, search_topical_maps |
| `dkn` | Domain Knowledge Network — list/update nodes, generate articles from DKN |
| `folder_management` | create/fetch/list brand vaults |

### GBP — Google Business Profile (16 tools)
Location management, automated posting, AI review responses, categories, services, attributes, media.

| Tool | Key Operations |
|------|----------------|
| `gbp_locations_crud` | get/list/update locations, update hours and special hours |
| `gbp_locations_deployment` | deploy_location, bulk_deploy, suggest_description |
| `gbp_locations_recommendations` | generate/apply/bulk_apply AI recommendations |
| `gbp_locations_categories_crud` | list/replace/remove categories |
| `gbp_locations_services_crud` | bulk_upsert standard/custom services |
| `gbp_locations_attributes_crud` | bulk_upsert/remove attributes |
| `gbp_locations_medias_crud` | list_medias |
| `posts_crud` | create/approve/publish/delete GBP posts |
| `posts_generation` | ai_generate_post_image, bulk_create/generate posts |
| `posts_automation` | enable/disable automated posting, update settings |
| `posts_social` | list Facebook pages, Instagram accounts, Twitter accounts |
| `reviews` | ai_generate_review_reply, publish/update reply, automation settings |
| `connections` | all_available_locations, manage_connections |
| `stats` | bulk_refresh_stats |
| `tasks` | bulk_approve_tasks, list/refresh location tasks |
| `utility` | bulk_import_locations_entity, generate_share_hash |

### Local SEO (7 tools)
Heatmap rank tracking, citation building, AI keyword recommendations.

| Tool | Key Operations |
|------|----------------|
| `business` | create/list/get local SEO businesses, extract business details |
| `grids` | setup/refresh/update heatmap grids |
| `data` | get_grid_details, get_heatmap_preview/snapshot, get_rank |
| `analytics` | competitor_report, location_report |
| `ai` | recommend_keywords |
| `citation` | submit_citation, get_aggregator_networks/details, preview_citation_data |
| `quota` | quota management |

### Press Release (4 tools)
AI content creation, Tier 1 publisher distribution.

| Tool | Key Operations |
|------|----------------|
| `content` | create/write press releases, list content types |
| `distribution` | get categories, publish press release to Tier 1 publishers |
| `knowledge_graph` | press release knowledge graphs |
| `payment` | HDC credit balance and purchase |

### Cloud Stack (4 tools)
Authority backlinks across 14+ cloud providers (AWS, Azure, GCP, etc.).

| Tool | Key Operations |
|------|----------------|
| `content` | cloud stack content creation |
| `distribution` | deploy to 14+ cloud providers |
| `knowledge_graph` | cloud stack knowledge graphs |
| `payment` | credit management |

### Digital PR (4 tools)
Publisher outreach campaigns, email templates, opportunity management.

| Tool | Key Operations |
|------|----------------|
| `campaigns` | create/manage outreach campaigns, update settings |
| `inbox` | monitor inbox, reply to emails, manage sent items |
| `templates` | create/update email templates |
| `opportunities` | list publisher opportunities, schedule bulk outreach |

### LinkLab (4 tools)
Guest post marketplace, editorial link building.

| Tool | Key Operations |
|------|----------------|
| `articles` | create/manage guest post articles |
| `orders` | add_to_cart, checkout, validate_content |
| `publications` | list publications and categories |
| `projects` | manage LinkLab projects |

### LLM Visibility / GEO (8 tools)
Brand visibility across ChatGPT, Gemini, Perplexity, Copilot, Grok. Generative Engine Optimization.

| Tool | Key Operations |
|------|----------------|
| `visibility` | get_brand_overview, competitor_share_of_voice, visibility_trend |
| `sentiment` | get_sentiment_overview, sentiment_trend |
| `citations` | get_citations_overview, citations_urls |
| `prompt_simulator` | submit_prompts, get_prompt_analysis, get_ps_visibility |
| `topics` | add/list/remove topics |
| `queries` | add/list/remove queries |
| `projects` | LLM visibility project management |
| `quota` | quota management |

### BrandVault (1 tool, shared across all categories)

| Tool | Key Operations |
|------|----------------|
| `brand_vault` | create/update brand vault, get_brand_vault_overview (requires `hostname`), ask_brand_vault, list/select voice profiles, update business info and knowledge graph |

### Website Studio (1 tool)

| Tool | Key Operations |
|------|----------------|
| `website_studio_tools` | create_project (modes: free, clone, clone_seo, clone_ppc), publish_project, list/get projects |

### GSC Tools (2 tools)

| Tool | Key Operations |
|------|----------------|
| `GSC_Performance_Tool` | get_keyword_performance, get_page_performance, compare_performance |
| `GSC_Site_Events_Tool` | create site events, list events |

## The 5-Day Omnichannel Marketing Blueprint

| Day | Mission | Arsenal |
|-----|---------|---------|
| **1** | **Establish Your Brand** — Build digital HQ, lock in brand identity, claim territory on Google | Website Studio, Brand Vault, GBP, Local SEO |
| **2** | **Content & SEO Domination** — Flood the SERPs with authority content, own every keyword | Content Genius, OTTO SEO, Site Explorer, GSC, Site Auditor |
| **3** | **Authority & Link Building** — Press releases, cloud stacks, digital PR, guest posts, citations | Press Release, Cloud Stack, Digital PR, LinkLab, Citations |
| **4** | **Paid & Social Amplification** — Agentic PPC campaigns, AI landing pages, GBP post amplification | PPC/Google Ads, Website Studio (clone_ppc), GBP Posts |
| **5** | **AI Visibility & Scale** — Monitor brand across AI search engines, track GEO rankings | LLM Visibility, Site Explorer, Local SEO Heatmaps |

## 28 Ready-to-Run Playbooks

**Day 1 — Establish Your Brand**
1. Launch Your AI-Generated Website (15 min)
2. Build Your Brand Vault — Digital Identity Foundation (10 min)
3. Connect and Optimize Your Google Business Profile (10 min)
4. Set Up Local SEO Heatmap Tracking (10 min)

**Day 2 — Content & SEO Domination**
5. Review & Complete Brand Vault (5 min)
6. Build Topical Map Content Strategy (15 min)
7. Increase Organic Traffic with Quality Content (20 min)
8. Connect GSC and Analyze Search Performance (10 min)
9. Site Explorer: Map Organic Landscape and Competitors (15 min)
10. Run a Full Site Audit (15 min)
11. AI-Optimized Industry Leader Listicle Builder (15 min)
12. AI-Optimized Head-to-Head Content (15 min)
13. AI Optimized About Us Page Creator (10 min)
14. AI-Optimized Industry Leader Content Creation (15 min)
15. Automated GBP Review Response & Amplification Engine (15 min)

**Day 3 — Authority & Link Building**
16. Gain Media Coverage and Brand Mentions (10 min)
17. Deploy Single Cloud Stack Authority Order (10 min)
18. Deploy Link Labs Guest Post Campaign (15 min)
19. Create Local Directory Citations (5 min)
20. Strengthen On-Page SEO for Priority Pages (15 min)
21. Publisher Prospecting Outreach Playbook (15 min)
22. Business Prospecting Outreach Playbook (15 min)

**Day 4 — Paid & Social Amplification**
23. Launch an Agentic PPC Campaign (20 min)
24. Build PPC Landing Pages for Each Ad Campaign (15 min)
25. GBP Post Campaign for Paid Traffic Amplification (10 min)

**Day 5 — AI Visibility & Scale**
26. Track Your Brand Across AI Search Engines (10 min)
27. Analyze Competitive AI Search Share of Voice (15 min)
28. Full 5-Day Results Review and Scale Plan (15 min)

## PPC Campaign Build — Quick Reference

1. `business_mgmt → generate_form_suggestions` (AI suggestions from URL)
2. `business_crud → create` (create PPC business with suggestions)
3. `business_mgmt → discover_products` (auto-discover from website)
4. `product_crud → review_products` → `product_mgmt → bulk_approve_products`
5. `business_mgmt → create_products` (with bidding strategy)
6. `product_crud → bulk_create_keyword_clusters`
7. `keyword_cluster → bulk_approve_keyword_clusters`
8. `keyword_cluster → bulk_create_ad_contents`
9. `ad_content → bulk_approve_ad_contents`
10. `product_mgmt → bulk_create_campaign_budget` (set daily budget)
11. **STOP** — Only `campaign → send_to_google_ads_account` when explicitly told to launch.

## Content Generation Workflow

1. `content_generation → create_content_instance` (set title + keywords)
2. `content_generation → start_information_retrieval` (research SERP)
3. Poll `poll_information_retrieval` until done
4. `content_generation → start_headings_outline` (generate heading structure)
5. Poll `poll_headings_outline` until done
6. `content_generation → generate_complete_article` (produce full article)
7. `article_management → run_content_grader` (score — target 80+)
8. `article_management → insert_article_links` (internal linking)

Or use `auto_generate_article` for faster single-call generation.

## Known Tool Name Collisions

| Name | Conflicts With | Notes |
|------|---------------|-------|
| `project_management` | OTTO (#6) vs Content Genius (#45) | First match = OTTO |
| `knowledge_graph` | OTTO (#3) vs Press Release (#75) vs Cloud Stack (#81) | First match = OTTO |
| `content` | Press Release (#73) vs Cloud Stack (#79) | First match = PR |
| `distribution` | Press Release (#74) vs Cloud Stack (#80) | First match = PR |
| `projects` | Site Explorer (#37) vs LinkLab (#95) vs LLM Visibility (#100) | First match = SE |
| `quota` | Local SEO (#71) vs PR (#77) vs CS (#83) vs LLM (#104) | First match = Local |

## Environment

| Variable | Required | Purpose |
|---|---|---|
| `MCP_API_KEY` | **Yes** | SearchAtlas MCP API key (get from dashboard.searchatlas.com) |
