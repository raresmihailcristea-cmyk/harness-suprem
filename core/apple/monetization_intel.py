# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Universal App Competitor & Monetization Intelligence Advisor
# Applicable to ANY iOS, iPadOS, macOS, watchOS, or visionOS project.

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("core.apple.monetization")

SWIFT_SAMPLE_CODE = """```swift
import SwiftUI
import StoreKit

struct ProUpgradePaywallView: View {
    @Environment(\\.dismiss) private var dismiss
    
    var body: some View {
        SubscriptionStoreView(groupID: "__GROUP_ID__") {
            VStack(spacing: 8) {
                Image(systemName: "sparkles")
                    .font(.system(size: 44))
                    .foregroundColor(.yellow)
                Text("Unlock __APP_NAME__ Pro")
                    .font(.title2.bold())
                Text("Get full access to all advanced features, priority updates & sync.")
                    .multilineTextAlignment(.center)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 20)
        }
        .subscriptionStorePolicyDestination(url: URL(string: "__PRIVACY_URL__")!, for: .privacyPolicy)
        .subscriptionStorePolicyDestination(url: URL(string: "__TERMS_URL__")!, for: .termsOfService)
    }
}
```"""

@dataclass
class MonetizationStrategy:
    app_name: str
    category: str
    bundle_id: str
    competitor_benchmarks: List[Dict[str, Any]]
    pricing_model: Dict[str, Any]
    marketing_plan: Dict[str, Any]
    in_app_purchases: List[Dict[str, Any]]
    subscriptions: List[Dict[str, Any]]
    subscription_groups: List[Dict[str, Any]]
    billing_grace_period: Dict[str, Any]
    streamlined_purchasing: Dict[str, Any]

    def to_markdown(self) -> str:
        """Renders a comprehensive, universal monetization report in English."""
        sub_rows = "\n".join([
            f"| `{s['product_id']}` | **{s['name']}** | {s['price']} | {s['billing_period']} | {s['trial']} |"
            for s in self.subscriptions
        ])
        iap_rows = "\n".join([
            f"| `{p['product_id']}` | **{p['name']}** | {p['type']} | {p['price']} | {p['description']} |"
            for p in self.in_app_purchases
        ])
        comp_rows = "\n".join([
            f"| **{c['name']}** | {c['model']} | {c['typical_price']} | {c['strengths']} | {c['our_advantage']} |"
            for c in self.competitor_benchmarks
        ])

        swift_code = (
            SWIFT_SAMPLE_CODE
            .replace("__GROUP_ID__", self.subscription_groups[0]['group_id'])
            .replace("__APP_NAME__", self.app_name)
            .replace("__PRIVACY_URL__", f"https://example.com/{self.bundle_id}/privacy")
            .replace("__TERMS_URL__", f"https://example.com/{self.bundle_id}/terms")
        )

        return f"""# Universal App Competitor & Monetization Intelligence Report
**Application**: {self.app_name} | **Bundle ID**: `{self.bundle_id}`  
**Category**: {self.category} | **Architecture**: Native Apple (SwiftUI + StoreKit 2)

---

## 1. Competitor Benchmark Analysis
| Competitor | Business Model | Market Price | Key Strengths | Our Differentiating Advantage |
| :--- | :--- | :--- | :--- | :--- |
{comp_rows}

---

## 2. Recommended Pricing Strategy
* **Overall Model**: {self.pricing_model.get('model_type', 'Freemium with Hybrid Subscription & Lifetime Unlock')}
* **Free Tier Capabilities**:
{chr(10).join([f"  - {f}" for f in self.pricing_model.get('free_tier_features', [])])}
* **Pro Tier Value Proposition**:
{chr(10).join([f"  - {f}" for f in self.pricing_model.get('pro_tier_features', [])])}
* **Recommended Price Points**:
  - **Monthly Subscription**: `{self.pricing_model.get('monthly_price')}` / month
  - **Annual Subscription**: `{self.pricing_model.get('annual_price')}` / year (~33% savings, includes {self.pricing_model.get('trial_days', '7-day')} free trial)
  - **Lifetime Non-Consumable**: `{self.pricing_model.get('lifetime_price')}` (captures users who resist recurring subscriptions)

---

## 3. Marketing & Go-To-Market (GTM) Plan
* **App Store Optimization (ASO)**:
  - **Target Primary Keywords**: {', '.join(self.marketing_plan.get('aso_keywords', []))}
  - **Localization**: Localize store page into top Apple markets (US, UK, DE, FR, JP, KR, CN, BR).
* **Acquisition Channels**:
{chr(10).join([f"  - **{ch['channel']}**: {ch['strategy']}" for ch in self.marketing_plan.get('channels', [])])}
* **Conversion Optimization**:
  - Soft paywall introduced upon encountering advanced pro feature.
  - Transparent value presentation with StoreKit 2 native sheet.

---

## 4. In-App Purchases (IAP) Specification
| Product ID | Product Name | Type | Price | Description |
| :--- | :--- | :--- | :--- | :--- |
{iap_rows}

---

## 5. Auto-Renewable Subscriptions
| Product ID | Subscription Tier | Price | Period | Free Trial |
| :--- | :--- | :--- | :--- | :--- |
{sub_rows}

---

## 6. Subscription Groups Architecture
* **Group Name**: `{self.subscription_groups[0]['group_name']}`
* **Group ID**: `{self.subscription_groups[0]['group_id']}`
* **Hierarchy & Upgrades**:
{chr(10).join([f"  - **Level {lvl['level']} ({lvl['name']})**: `{lvl['product_id']}` - {lvl['behavior']}" for lvl in self.subscription_groups[0]['levels']])}
* Apple seamlessly manages upgrades, downgrades, and cross-grades with prorated refunds.

---

## 7. Billing Grace Period (Preventing Involuntary Churn)
* **Status in App Store Connect**: **Enabled** (Crucial Apple Best Practice)
* **Recommended Duration**:
  - **Annual Subscriptions**: `{self.billing_grace_period.get('annual_grace_days', 16)} days`
  - **Monthly Subscriptions**: `{self.billing_grace_period.get('monthly_grace_days', 16)} days`
* **Mechanics & Benefits**:
  - If a user's payment method fails (e.g. expired card), Apple attempts recovery for 16 days while maintaining subscriber access.
  - In-app notification gently guides the user to update billing credentials in Settings.
  - Prevents an estimated **35% - 57%** of involuntary subscriber cancellations.

---

## 8. Streamlined Purchasing (StoreKit 2 Native Implementation)
* **Framework**: Apple **StoreKit 2** (iOS 17+ / macOS 14+).
* **Native Views**:
  - `SubscriptionStoreView` with custom branding, privacy/terms links.
  - `ProductView` for standalone lifetime purchase cards.
* **Win-Back Offers**:
  - Configured in App Store Connect: 50% discount for first 3 billing cycles for churned users within 90 days.
* **SwiftUI Implementation Snippet**:
{swift_code}

---
*Auto-generated by Universal Monetization Intelligence Engine (Scion Frontiers & Antigravity).*
"""


class CompetitorMonetizationAdvisor:
    """
    Universal Competitor & Monetization Intelligence Advisor.
    Inspects ANY iOS, iPadOS, macOS, watchOS, or visionOS project, detects its
    real domain and category, and formulates competitive pricing, marketing,
    subscriptions, grace periods, and StoreKit 2 blueprints.
    """

    COMPETITOR_DATABASE: Dict[str, List[Dict[str, str]]] = {
        "Developer Tools": [
            {"name": "Cursor", "model": "Subscription ($20/mo)", "typical_price": "$20 - $40/mo", "strengths": "AI code agent autocomplete", "our_advantage": "Privacy-first local execution, native Apple Silicon optimization"},
            {"name": "Raycast Pro", "model": "Freemium ($8 - $16/mo)", "typical_price": "$96 - $192/yr", "strengths": "Large extension ecosystem", "our_advantage": "Automated workflow orchestration & specialized tool integration"},
            {"name": "Tower / GitKraken", "model": "Subscription ($69 - $149/yr)", "typical_price": "$69/yr", "strengths": "Git history visualization", "our_advantage": "Autonomous candidate branch evaluation and automated verification"},
            {"name": "Postman / Proxyman", "model": "Freemium ($14 - $29/mo)", "typical_price": "$168/yr", "strengths": "API inspection & mocking", "our_advantage": "Deep integration with native Swift frameworks & offline reliability"}
        ],
        "Productivity": [
            {"name": "Notion", "model": "Freemium ($10 - $18/mo)", "typical_price": "$120/yr", "strengths": "Collaborative modular workspace", "our_advantage": "Offline-first native speed, zero cloud telemetry, instant launch"},
            {"name": "Things 3", "model": "Paid Upfront ($10 - $50)", "typical_price": "$49.99 lifetime", "strengths": "Award-winning native Apple HIG design", "our_advantage": "AI-assisted scheduling, automated task decomposition"},
            {"name": "Craft", "model": "Subscription ($8 - $15/mo)", "typical_price": "$96/yr", "strengths": "Structured native document authoring", "our_advantage": "Open file formats, local encryption, modular extensions"},
            {"name": "Obsidian", "model": "Freemium + Sync ($4/mo)", "typical_price": "$48/yr", "strengths": "Local Markdown knowledge graph", "our_advantage": "Native SwiftUI fluid interface with zero Electron overhead"}
        ],
        "Health & Fitness": [
            {"name": "Strava", "model": "Freemium ($11.99/mo, $79.99/yr)", "typical_price": "$79.99/yr", "strengths": "Social activity feeds & leaderboards", "our_advantage": "Deeper local analytics, privacy-guaranteed health metrics"},
            {"name": "MyFitnessPal", "model": "Subscription ($19.99/mo, $79.99/yr)", "typical_price": "$79.99/yr", "strengths": "Huge food database", "our_advantage": "Fast barcode and on-device computer vision recognition without ads"},
            {"name": "Whoop", "model": "Hardware + Subscription ($30/mo)", "typical_price": "$239/yr", "strengths": "Recovery & strain continuous monitoring", "our_advantage": "No proprietary hardware lock-in, uses Apple Watch sensor suite"},
            {"name": "Calm / Headspace", "model": "Subscription ($14.99/mo, $69.99/yr)", "typical_price": "$69.99/yr", "strengths": "Rich audio content & mindfulness library", "our_advantage": "Personalized adaptive sessions, zero repetitive subscriptions"}
        ],
        "Medical": [
            {"name": "Epocrates", "model": "Freemium ($174/yr)", "typical_price": "$174/yr", "strengths": "Comprehensive clinical drug reference", "our_advantage": "On-device search, zero delay, offline emergency access"},
            {"name": "Complete Anatomy", "model": "Subscription ($39.99/yr)", "typical_price": "$39.99/yr", "strengths": "3D interactive anatomical models", "our_advantage": "Fluid Metal rendering, visionOS native spatial integration"}
        ],
        "Photo & Video": [
            {"name": "VSCO", "model": "Subscription ($29.99/yr)", "typical_price": "$29.99/yr", "strengths": "Curated film aesthetic presets", "our_advantage": "Real-time RAW processing, non-destructive GPU pipeline"},
            {"name": "Adobe Lightroom Mobile", "model": "Subscription ($9.99/mo)", "typical_price": "$119.88/yr", "strengths": "Cloud synchronization across devices", "our_advantage": "One-time purchase option, native Apple Photos library integration"},
            {"name": "Halide", "model": "Subscription ($11.99/yr) or $59.99 Lifetime", "typical_price": "$59.99 lifetime", "strengths": "Manual camera controls & tactile design", "our_advantage": "Integrated smart post-processing with CoreML"}
        ],
        "Finance": [
            {"name": "YNAB (You Need A Budget)", "model": "Subscription ($14.99/mo, $99/yr)", "typical_price": "$99/yr", "strengths": "Zero-based budgeting methodology", "our_advantage": "On-device bank statement parsing, zero sensitive data leaks"},
            {"name": "Copilot Money", "model": "Subscription ($13/mo, $95/yr)", "typical_price": "$95/yr", "strengths": "Stunning Mac/iPhone UI & machine learning classification", "our_advantage": "Cross-platform flexibility, lifetime license fallback option"}
        ],
        "Games": [
            {"name": "Monument Valley", "model": "Premium ($3.99 - $4.99)", "typical_price": "$4.99", "strengths": "Artistic level design & audio atmosphere", "our_advantage": "Infinite procedural puzzle challenges, Metal performance"},
            {"name": "Slay the Spire", "model": "Premium ($9.99)", "typical_price": "$9.99", "strengths": "Deep deck-building replayability", "our_advantage": "Modern responsive touch controls and Game Center achievements"}
        ]
    }

    @classmethod
    def analyze_project_monetization(
        cls,
        project_dir: str,
        output_file: Optional[str] = None
    ) -> Tuple[MonetizationStrategy, str]:
        from core.apple.app_store_distribution import AppStoreDistributionGenerator

        abs_path = os.path.abspath(os.path.expanduser(project_dir))

        # 1. Discover app identity and category universally
        app_name, bundle_id = AppStoreDistributionGenerator._discover_identity(abs_path)
        signals = AppStoreDistributionGenerator._deep_scan_project(abs_path, app_name)
        category = signals.get("primary_category", "Productivity")

        # 2. Select Competitor Benchmark for this specific category
        competitors = cls.COMPETITOR_DATABASE.get(category, cls.COMPETITOR_DATABASE["Productivity"])

        # 3. Formulate Category-Tailored Pricing Model
        pricing_model = cls._build_pricing_model(category, signals)

        # 4. Formulate Marketing & ASO Plan
        marketing_plan = cls._build_marketing_plan(app_name, category, signals)

        # 5. Build Dynamic IAPs & Subscriptions
        in_app_purchases, subscriptions, sub_groups = cls._build_storekit_products(app_name, bundle_id, pricing_model)

        # 6. Billing Grace Period Configuration (Apple 16-day standard)
        billing_grace_period = {
            "enabled": True,
            "annual_grace_days": 16,
            "monthly_grace_days": 16,
            "in_app_messaging": "Subscribers maintain full access for 16 days while Apple retries failed billing attempts."
        }

        # 7. Streamlined Purchasing Details
        streamlined_purchasing = {
            "storekit_version": "StoreKit 2",
            "swiftui_views": ["SubscriptionStoreView", "ProductView", "StoreView"],
            "win_back_offers_enabled": True,
            "family_sharing_enabled": True,
            "in_app_refund_sheet": True,
            "manage_subscriptions_sheet": True
        }

        strategy = MonetizationStrategy(
            app_name=app_name,
            category=category,
            bundle_id=bundle_id,
            competitor_benchmarks=competitors,
            pricing_model=pricing_model,
            marketing_plan=marketing_plan,
            in_app_purchases=in_app_purchases,
            subscriptions=subscriptions,
            subscription_groups=sub_groups,
            billing_grace_period=billing_grace_period,
            streamlined_purchasing=streamlined_purchasing
        )

        md_content = strategy.to_markdown()

        if output_file:
            target_path = os.path.abspath(output_file)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"Universal monetization blueprint written to: {target_path}")

        return strategy, md_content

    @classmethod
    def _build_pricing_model(cls, category: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates optimal price points based on market category norms."""
        if category in ["Developer Tools", "Finance"]:
            return {
                "model_type": "Freemium with Pro Subscription & Lifetime Unlock",
                "monthly_price": "$14.99",
                "annual_price": "$119.99",
                "lifetime_price": "$249.00",
                "trial_days": "7-day",
                "free_tier_features": [
                    "Core workspace and viewer features",
                    "Standard file import/export",
                    "Community support"
                ],
                "pro_tier_features": [
                    "Unlimited advanced execution & automation",
                    "Parallel background processing",
                    "Cloud sync & cross-device continuity",
                    "Priority developer support"
                ]
            }
        elif category in ["Health & Fitness", "Medical", "Lifestyle"]:
            return {
                "model_type": "Free Trial with Auto-Renewable Subscription",
                "monthly_price": "$9.99",
                "annual_price": "$59.99",
                "lifetime_price": "$149.00",
                "trial_days": "14-day",
                "free_tier_features": [
                    "Basic health activity logging",
                    "Daily overview metrics",
                    "Standard charts"
                ],
                "pro_tier_features": [
                    "Personalized health insights & trend forecasting",
                    "Comprehensive export for healthcare professionals",
                    "Custom workout and recovery plans"
                ]
            }
        elif category in ["Photo & Video", "Graphics & Design"]:
            return {
                "model_type": "Freemium with Creative Pro Pack",
                "monthly_price": "$6.99",
                "annual_price": "$49.99",
                "lifetime_price": "$99.00",
                "trial_days": "7-day",
                "free_tier_features": [
                    "Essential editing tools and standard filters",
                    "Export in standard resolution"
                ],
                "pro_tier_features": [
                    "Full RAW editing & GPU-accelerated rendering",
                    "Unlimited premium presets and overlays",
                    "Batch export and 4K/ProRes output"
                ]
            }
        elif category == "Games":
            return {
                "model_type": "Premium or Free with Content Unlocks",
                "monthly_price": "N/A",
                "annual_price": "N/A",
                "lifetime_price": "$4.99",
                "trial_days": "N/A",
                "free_tier_features": ["First world / 10 tutorial levels included"],
                "pro_tier_features": ["Unlock all worlds, infinite endless mode, no third-party ads"]
            }
        else:
            return {
                "model_type": "Freemium with Pro Subscription",
                "monthly_price": "$9.99",
                "annual_price": "$79.99",
                "lifetime_price": "$179.00",
                "trial_days": "7-day",
                "free_tier_features": ["Basic usage with daily limits"],
                "pro_tier_features": ["Unlimited usage, power user workflows, premium themes"]
            }

    @classmethod
    def _build_marketing_plan(cls, app_name: str, category: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Generates dynamic ASO keywords and channel strategy tailored to category."""
        base_keywords = [app_name.lower(), category.lower(), "ios", "mac", "apple"]
        if category == "Developer Tools":
            base_keywords.extend(["swift", "code", "git", "xcode", "automation"])
            channels = [
                {"channel": "Hacker News & Product Hunt", "strategy": f"Launch with technical deep-dive demonstrating {app_name}'s native speed and developer ergonomics."},
                {"channel": "Developer Communities (X, Reddit, Swift Forums)", "strategy": "Share open-source utilities and case studies highlighting time saved."},
                {"channel": "GitHub Funnel", "strategy": "Free open-source CLI/core with native macOS/iOS companion for advanced workflows."}
            ]
        elif category in ["Health & Fitness", "Medical"]:
            base_keywords.extend(["workout", "health", "tracker", "wellness", "fitness"])
            channels = [
                {"channel": "Instagram & TikTok Short-form Video", "strategy": "User-generated transformation stories and UI showcase with Apple Health integration."},
                {"channel": "Apple App Store Featuring", "strategy": "Pitch to Apple Editorial team for 'New Apps We Love' highlighting HealthKit & Watch integration."}
            ]
        elif category in ["Photo & Video", "Graphics & Design"]:
            base_keywords.extend(["photo", "editor", "video", "creative", "camera"])
            channels = [
                {"channel": "Creator & Photography Influencers", "strategy": "Sponsor creative YouTubers and photographers with before/after workflows."},
                {"channel": "Visual Social Media", "strategy": "Daily showcase of edits, color grades, and community artwork."}
            ]
        else:
            base_keywords.extend(["productivity", "organizer", "planner", "focus"])
            channels = [
                {"channel": "Productivity Communities", "strategy": "Highlight minimalism, keyboard shortcuts, and workflow efficiencies."},
                {"channel": "Content Marketing & SEO", "strategy": "Articles on modern productivity systems and workflow automation."}
            ]

        return {
            "aso_keywords": list(dict.fromkeys(base_keywords))[:10],
            "channels": channels
        }

    @classmethod
    def _build_storekit_products(
        cls,
        app_name: str,
        bundle_id: str,
        pricing: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Dynamically generates StoreKit 2 product definitions and subscription groups."""
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", app_name)
        group_id_hash = str(int(hashlib.md5(bundle_id.encode()).hexdigest()[:8], 16))[:8]

        in_app_purchases = [
            {
                "product_id": f"{bundle_id}.iap.lifetime",
                "name": f"{app_name} Lifetime Pro",
                "type": "Non-Consumable",
                "price": pricing.get("lifetime_price", "$199.00"),
                "description": f"Permanent, one-time unlock for all current and future {app_name} Pro features."
            }
        ]

        subscriptions = [
            {
                "product_id": f"{bundle_id}.sub.pro.monthly",
                "name": f"{app_name} Pro Monthly",
                "price": pricing.get("monthly_price", "$14.99"),
                "billing_period": "Monthly",
                "trial": "None"
            },
            {
                "product_id": f"{bundle_id}.sub.pro.annual",
                "name": f"{app_name} Pro Annual",
                "price": pricing.get("annual_price", "$119.99"),
                "billing_period": "Annual (Best Value)",
                "trial": f"{pricing.get('trial_days', '7-day')} Free Trial"
            }
        ]

        subscription_groups = [
            {
                "group_name": f"{clean_name}ProSubscriptions",
                "group_id": group_id_hash,
                "levels": [
                    {
                        "level": 1,
                        "name": "Pro Annual",
                        "product_id": f"{bundle_id}.sub.pro.annual",
                        "behavior": "Top tier - Annual billing with free trial and maximum discount"
                    },
                    {
                        "level": 2,
                        "name": "Pro Monthly",
                        "product_id": f"{bundle_id}.sub.pro.monthly",
                        "behavior": "Standard tier - Flexible monthly billing"
                    }
                ]
            }
        ]

        return in_app_purchases, subscriptions, subscription_groups
