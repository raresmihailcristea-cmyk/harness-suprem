# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Test Suite for App Store Connect Distribution Generator & Competitor Monetization Advisor

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.apple.app_store_distribution import AppStoreDistributionGenerator, AppStoreMetadata
from core.apple.monetization_intel import CompetitorMonetizationAdvisor, MonetizationStrategy
from plugins.plugin_manager import PluginManager

class TestDistributionAndMonetization(unittest.TestCase):

    def test_app_store_distribution_generator(self):
        meta, md = AppStoreDistributionGenerator.analyze_and_generate(BASE_DIR)
        
        self.assertIsInstance(meta, AppStoreMetadata)
        self.assertIn(meta.app_name, ["Harness Suprem", "Harness-Suprem"])
        self.assertLessEqual(len(meta.app_name), 30)
        self.assertLessEqual(len(meta.app_subtitle), 30)
        self.assertLessEqual(len(meta.promotional_text), 170)
        self.assertLessEqual(len(meta.description), 4000)
        self.assertLessEqual(len(meta.keywords), 100)
        self.assertLessEqual(len(meta.app_review_notes), 4000)
        self.assertLessEqual(len(meta.app_encryption_doc), 300)
        self.assertLessEqual(len(meta.beta_app_description), 4000)
        
        # Validate constraints checker
        errors = meta.validate_constraints()
        self.assertEqual(errors, [])

        # Check markdown content
        self.assertIn("# App Store Connect Distribution Specification", md)
        self.assertIn("Localizable Information", md)
        self.assertIn("App Review Notes", md)
        self.assertIn("Age Ratings", md)
        self.assertIn("Routing App Coverage", md)
        self.assertIn("Regulated Medical Devices", md)

    def test_competitor_monetization_advisor(self):
        strategy, md = CompetitorMonetizationAdvisor.analyze_project_monetization(BASE_DIR)

        self.assertIsInstance(strategy, MonetizationStrategy)
        self.assertIn(strategy.app_name, ["Harness Suprem", "Harness-Suprem"])
        self.assertGreater(len(strategy.competitor_benchmarks), 0)
        
        # Subscriptions
        self.assertIn("monthly_price", strategy.pricing_model)
        self.assertIn("annual_price", strategy.pricing_model)
        self.assertEqual(len(strategy.subscriptions), 2)
        
        # Subscription Groups
        self.assertEqual(len(strategy.subscription_groups), 1)
        self.assertEqual(strategy.subscription_groups[0]["group_name"], "HarnessSupremProSubscriptions")
        
        # Billing Grace Period
        self.assertTrue(strategy.billing_grace_period["enabled"])
        self.assertEqual(strategy.billing_grace_period["annual_grace_days"], 16)
        self.assertEqual(strategy.billing_grace_period["monthly_grace_days"], 16)
        
        # Streamlined Purchasing (StoreKit 2)
        self.assertEqual(strategy.streamlined_purchasing["storekit_version"], "StoreKit 2")
        self.assertIn("SubscriptionStoreView", strategy.streamlined_purchasing["swiftui_views"])
        self.assertTrue(strategy.streamlined_purchasing["win_back_offers_enabled"])

        # Check markdown content
        self.assertIn("Competitor & Monetization Intelligence Report", md)
        self.assertIn("Competitor Benchmark Analysis", md)
        self.assertIn("Billing Grace Period", md)
        self.assertIn("Streamlined Purchasing", md)

    def test_arbitrary_project_dynamic_analysis(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock HealthKit project
            app_dir = os.path.join(temp_dir, "CardioMax Tracker")
            os.makedirs(app_dir, exist_ok=True)
            dummy_swift = os.path.join(app_dir, "ContentView.swift")
            with open(dummy_swift, "w") as f:
                f.write("""
                import SwiftUI
                import HealthKit
                import CoreMotion

                struct ContentView: View {
                    let healthStore = HKHealthStore()
                    var body: some View {
                        Text("Cardio Tracker")
                    }
                }
                """)
            
            # 1. Distribution Engine on arbitrary project
            meta, md = AppStoreDistributionGenerator.analyze_and_generate(app_dir)
            self.assertIn(meta.app_name, ["CardioMax Tracker", "Cardiomax Tracker"])
            self.assertEqual(meta.primary_category, "Health & Fitness")
            self.assertIn("Health tracking", md)
            self.assertEqual(meta.validate_constraints(), [])
            
            # 2. Monetization Engine on arbitrary project
            strategy, m_md = CompetitorMonetizationAdvisor.analyze_project_monetization(app_dir)
            self.assertIn(strategy.app_name, ["CardioMax Tracker", "Cardiomax Tracker"])
            self.assertEqual(strategy.category, "Health & Fitness")
            benchmarks = [b["name"] for b in strategy.competitor_benchmarks]
            self.assertIn("Strava", benchmarks)
            self.assertIn("Cardio", strategy.subscription_groups[0]["group_name"])
            self.assertEqual(strategy.billing_grace_period["annual_grace_days"], 16)

    def test_plugin_manager_has_monetization_plugin(self):
        pm = PluginManager()
        names = [p.name for p in pm.list_plugins()]
        self.assertIn("app-monetization-intel", names)
        
        p = pm.get_plugin("app-monetization-intel")
        self.assertIsNotNone(p)
        res = p.analyze_monetization(BASE_DIR)
        self.assertIn("pricing_model", res)
        self.assertIn("billing_grace_period", res)

    def test_apple_developer_plugin_has_distribution_generator(self):
        pm = PluginManager()
        apple_p = pm.get_plugin("apple-developer")
        self.assertIsNotNone(apple_p)
        res = apple_p.generate_distribution_metadata(BASE_DIR)
        self.assertIn("app_name", res)
        self.assertIn("promotional_text", res)
        self.assertIn("report_markdown", res)


if __name__ == "__main__":
    unittest.main()
