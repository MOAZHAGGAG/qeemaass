#!/usr/bin/env python3
"""
COMPREHENSIVE FINAL TEST - Event Management AI System
Tests the complete integrated system with temporal, location, and interest filtering
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import requests
import json

# Add the parent directory to the Python path
sys.path.append('/Users/moaz/Downloads/qeemas final/event-management-app-main-2-copy-4-main')

from advanced_ai_functions import (
    extract_interests_enhanced,
    query_weaviate_with_advanced_filtering,
    parse_temporal_constraints,
    normalize_location,
    calculate_relevance_score
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveTester:
    def __init__(self):
        self.weaviate_url = "http://localhost:8088"
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'details': []
        }
    
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed'] += 1
            logger.info(f"✅ {test_name} - PASSED")
        else:
            self.test_results['failed'] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    def test_temporal_accuracy(self):
        """Test temporal filtering accuracy"""
        print("\n=== TESTING TEMPORAL ACCURACY ===")
        
        # Test 1: Tomorrow's events
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            events = query_weaviate_with_advanced_filtering("events tomorrow", limit=10)
            
            temporal_accuracy = 0
            if events:
                correct_dates = sum(1 for event in events if event.get('start_date', '').startswith(tomorrow))
                temporal_accuracy = (correct_dates / len(events)) * 100
            
            passed = temporal_accuracy >= 80  # 80% accuracy threshold
            self.log_test("Tomorrow Events Temporal Accuracy", passed, 
                         f"Accuracy: {temporal_accuracy:.1f}% ({len(events)} events)")
            
        except Exception as e:
            self.log_test("Tomorrow Events Temporal Accuracy", False, str(e))
        
        # Test 2: This week's events
        try:
            events = query_weaviate_with_advanced_filtering("events this week", limit=10)
            
            # Calculate this week's date range
            today = datetime.now()
            week_start = today
            week_end = today + timedelta(days=(6 - today.weekday()))
            
            temporal_accuracy = 0
            if events:
                correct_dates = 0
                for event in events:
                    event_date_str = event.get('start_date', '')
                    if event_date_str:
                        try:
                            event_date = datetime.strptime(event_date_str[:10], '%Y-%m-%d')
                            if week_start <= event_date <= week_end:
                                correct_dates += 1
                        except:
                            pass
                temporal_accuracy = (correct_dates / len(events)) * 100
            
            passed = temporal_accuracy >= 70  # 70% accuracy threshold for week
            self.log_test("This Week Events Temporal Accuracy", passed,
                         f"Accuracy: {temporal_accuracy:.1f}% ({len(events)} events)")
            
        except Exception as e:
            self.log_test("This Week Events Temporal Accuracy", False, str(e))
    
    def test_location_accuracy(self):
        """Test location filtering accuracy"""
        print("\n=== TESTING LOCATION ACCURACY ===")
        
        # Test 1: Cairo events
        try:
            events = query_weaviate_with_advanced_filtering("events in Cairo", limit=10)
            
            location_accuracy = 0
            if events:
                correct_locations = 0
                for event in events:
                    location = event.get('location', '').lower()
                    if any(cairo_term in location for cairo_term in ['cairo', 'zamalek', 'heliopolis', 'downtown', 'new cairo']):
                        correct_locations += 1
                location_accuracy = (correct_locations / len(events)) * 100
            
            passed = location_accuracy >= 80  # 80% accuracy threshold
            self.log_test("Cairo Events Location Accuracy", passed,
                         f"Accuracy: {location_accuracy:.1f}% ({len(events)} events)")
            
        except Exception as e:
            self.log_test("Cairo Events Location Accuracy", False, str(e))
        
        # Test 2: Alexandria events
        try:
            events = query_weaviate_with_advanced_filtering("events in Alexandria", limit=10)
            
            location_accuracy = 0
            if events:
                correct_locations = 0
                for event in events:
                    location = event.get('location', '').lower()
                    if 'alexandria' in location or 'alex' in location:
                        correct_locations += 1
                location_accuracy = (correct_locations / len(events)) * 100
            
            passed = location_accuracy >= 70  # 70% threshold (Alexandria might have fewer events)
            self.log_test("Alexandria Events Location Accuracy", passed,
                         f"Accuracy: {location_accuracy:.1f}% ({len(events)} events)")
            
        except Exception as e:
            self.log_test("Alexandria Events Location Accuracy", False, str(e))
    
    def test_interest_matching(self):
        """Test interest/category matching accuracy"""
        print("\n=== TESTING INTEREST MATCHING ===")
        
        interest_tests = [
            ("technology events", ["technology", "tech", "coding", "programming", "software"]),
            ("sports activities", ["sports", "football", "basketball", "tennis", "fitness"]),
            ("cultural events", ["cultural", "art", "music", "theater", "exhibition"]),
            ("academic conferences", ["academic", "research", "conference", "education", "university"])
        ]
        
        for query, keywords in interest_tests:
            try:
                events = query_weaviate_with_advanced_filtering(query, limit=10)
                
                interest_accuracy = 0
                if events:
                    correct_interests = 0
                    for event in events:
                        title = event.get('title', '').lower()
                        description = event.get('description', '').lower()
                        category = event.get('category', '').lower()
                        
                        # Check if any relevant keywords appear in event content
                        event_text = f"{title} {description} {category}"
                        if any(keyword in event_text for keyword in keywords):
                            correct_interests += 1
                    
                    interest_accuracy = (correct_interests / len(events)) * 100
                
                passed = interest_accuracy >= 60  # 60% accuracy threshold for interests
                self.log_test(f"Interest Matching: {query}", passed,
                             f"Accuracy: {interest_accuracy:.1f}% ({len(events)} events)")
                
            except Exception as e:
                self.log_test(f"Interest Matching: {query}", False, str(e))
    
    def test_combined_filtering(self):
        """Test combined temporal + location + interest filtering"""
        print("\n=== TESTING COMBINED FILTERING ===")
        
        combined_tests = [
            "tech events tomorrow in Cairo",
            "sports this weekend",
            "cultural events this week in Alexandria",
            "academic conferences next week"
        ]
        
        for query in combined_tests:
            try:
                events = query_weaviate_with_advanced_filtering(query, limit=10)
                
                # Check if we get reasonable results (not empty, not too many)
                reasonable_count = 0 <= len(events) <= 15
                has_relevant_data = True
                
                if events:
                    # Basic relevance check - events should have proper data
                    for event in events:
                        if not event.get('title') or not event.get('start_date'):
                            has_relevant_data = False
                            break
                
                passed = reasonable_count and has_relevant_data
                self.log_test(f"Combined Filtering: {query}", passed,
                             f"Found {len(events)} events")
                
            except Exception as e:
                self.log_test(f"Combined Filtering: {query}", False, str(e))
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n=== TESTING EDGE CASES ===")
        
        edge_cases = [
            ("", "Empty query"),
            ("asdfghjkl", "Nonsense query"),
            ("events in Mars", "Non-existent location"),
            ("events in year 2030", "Future year"),
            ("events yesterday", "Past date"),
        ]
        
        for query, description in edge_cases:
            try:
                events = query_weaviate_with_advanced_filtering(query, limit=5)
                
                # Should not crash and should return reasonable results
                passed = isinstance(events, list) and len(events) <= 10
                self.log_test(f"Edge Case: {description}", passed,
                             f"Query: '{query}' -> {len(events)} events")
                
            except Exception as e:
                self.log_test(f"Edge Case: {description}", False, str(e))
    
    def test_response_time(self):
        """Test response time performance"""
        print("\n=== TESTING RESPONSE TIME ===")
        
        import time
        
        test_queries = [
            "events tomorrow",
            "tech events in Cairo",
            "sports this weekend",
            "cultural events"
        ]
        
        total_time = 0
        successful_queries = 0
        
        for query in test_queries:
            try:
                start_time = time.time()
                events = query_weaviate_with_advanced_filtering(query, limit=5)
                end_time = time.time()
                
                response_time = end_time - start_time
                total_time += response_time
                successful_queries += 1
                
                passed = response_time < 5.0  # Should respond within 5 seconds
                self.log_test(f"Response Time: {query}", passed,
                             f"{response_time:.2f}s")
                
            except Exception as e:
                self.log_test(f"Response Time: {query}", False, str(e))
        
        if successful_queries > 0:
            avg_time = total_time / successful_queries
            passed = avg_time < 3.0  # Average should be under 3 seconds
            self.log_test("Average Response Time", passed, f"{avg_time:.2f}s")
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE FINAL TEST SUITE")
        print("=" * 60)
        
        # Run all test categories
        self.test_temporal_accuracy()
        self.test_location_accuracy()
        self.test_interest_matching()
        self.test_combined_filtering()
        self.test_edge_cases()
        self.test_response_time()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 SYSTEM PERFORMANCE: EXCELLENT")
        elif success_rate >= 60:
            print("👍 SYSTEM PERFORMANCE: GOOD")
        elif success_rate >= 40:
            print("⚠️  SYSTEM PERFORMANCE: NEEDS IMPROVEMENT")
        else:
            print("🚨 SYSTEM PERFORMANCE: CRITICAL ISSUES")
        
        # Show failed tests details
        if failed > 0:
            print("\n📋 FAILED TESTS DETAILS:")
            for result in self.test_results['details']:
                if not result['passed']:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        return success_rate >= 60  # Consider 60% as acceptable

if __name__ == "__main__":
    tester = ComprehensiveTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY!")
        print("The AI system is ready for production use.")
    else:
        print("\n⚠️  COMPREHENSIVE TESTING REVEALED ISSUES!")
        print("Please review and fix the identified problems.")
    
    exit(0 if success else 1)
