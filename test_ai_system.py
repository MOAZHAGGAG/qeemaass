#!/usr/bin/env python3
"""
Comprehensive AI System Testing for Event Management App
Tests search relevance, interest extraction, and query building
"""

import sys
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WEAVIATE_URL = 'http://localhost:8085'

def test_weaviate_search_relevance():
    """Test search relevance across different query types"""
    print("\n=== WEAVIATE SEARCH RELEVANCE TESTING ===")
    
    test_queries = [
        {'query': 'cooking classes', 'expected_categories': ['Workshop', 'Cultural']},
        {'query': 'technology events', 'expected_categories': ['Technology', 'Academic']},
        {'query': 'sports activities', 'expected_categories': ['Sports', 'Entertainment']},
        {'query': 'social networking', 'expected_categories': ['Social', 'Entertainment']},
        {'query': 'academic conferences', 'expected_categories': ['Academic', 'Technology']},
        {'query': 'cultural festivals', 'expected_categories': ['Cultural', 'Entertainment']},
        {'query': 'career development', 'expected_categories': ['Career', 'Academic']},
        {'query': 'health and wellness', 'expected_categories': ['Health', 'Workshop']},
    ]

    total_tests = 0
    low_relevance_tests = 0
    results = []

    for test in test_queries:
        query = test['query']
        expected = test['expected_categories']
        
        print(f"\nTesting: \"{query}\"")
        print(f"Expected categories: {expected}")
        
        try:
            # Build GraphQL query
            gql_query = {
                'query': '''
                {
                    Get {
                        Event(
                            nearText: {concepts: ["%s"]}
                            limit: 3
                        ) {
                            title
                            category
                            description
                            postgres_id
                            _additional { score }
                        }
                    }
                }
                ''' % query
            }
            
            response = requests.post(f'{WEAVIATE_URL}/v1/graphql', json=gql_query, timeout=10)
            result = response.json()
            
            if 'errors' in result:
                print(f"  Error: {result['errors']}")
                continue
                
            events = result.get('data', {}).get('Get', {}).get('Event', [])
            
            if events:
                print("Current results:")
                found_categories = []
                for i, event in enumerate(events[:3]):
                    score = event.get('_additional', {}).get('score', 0)
                    category = event['category']
                    found_categories.append(category)
                    print(f"  {i+1}. {event['title']} ({category}) - Score: {score:.3f}")
                    
                # Check relevance
                relevant_count = sum(1 for cat in found_categories if cat in expected)
                relevance_score = relevant_count / len(events) * 100
                print(f"  Relevance: {relevance_score:.1f}% ({relevant_count}/{len(events)} relevant)")
                
                total_tests += 1
                test_result = {
                    'query': query,
                    'expected': expected,
                    'found_categories': found_categories,
                    'relevance_score': relevance_score,
                    'events': events
                }
                results.append(test_result)
                
                if relevance_score < 50:
                    print("  ⚠️  LOW RELEVANCE!")
                    low_relevance_tests += 1
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n=== SEARCH RELEVANCE SUMMARY ===")
    print(f"Total tests: {total_tests}")
    print(f"Low relevance tests: {low_relevance_tests}")
    if total_tests > 0:
        success_rate = (total_tests - low_relevance_tests) / total_tests * 100
        print(f"Overall success rate: {success_rate:.1f}%")
    else:
        print("No tests completed")
        
    return results

def test_query_building_strategies():
    """Test different query building strategies"""
    print("\n=== QUERY BUILDING STRATEGIES TEST ===")
    
    test_cases = [
        {
            'user_input': 'cooking events in Cairo',
            'extracted_interests': ['cooking', 'culinary', 'food'],
            'strategies': [
                'cooking culinary food',  # Simple concatenation
                'cooking OR culinary OR food',  # OR logic
                'cooking classes workshops',  # Context addition
                'culinary events food workshops'  # Enhanced terms
            ]
        },
        {
            'user_input': 'tech meetups for developers',
            'extracted_interests': ['technology', 'programming', 'development'],
            'strategies': [
                'technology programming development',
                'technology OR programming OR development',
                'tech meetups programming',
                'technology conferences programming workshops'
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\nUser input: \"{test_case['user_input']}\"")
        print(f"Extracted interests: {test_case['extracted_interests']}")
        
        for i, strategy in enumerate(test_case['strategies']):
            print(f"\nStrategy {i+1}: \"{strategy}\"")
            
            try:
                gql_query = {
                    'query': '''
                    {
                        Get {
                            Event(
                                nearText: {concepts: ["%s"]}
                                limit: 3
                            ) {
                                title
                                category
                                _additional { score }
                            }
                        }
                    }
                    ''' % strategy
                }
                
                response = requests.post(f'{WEAVIATE_URL}/v1/graphql', json=gql_query, timeout=10)
                result = response.json()
                
                if 'errors' in result:
                    print(f"  Error: {result['errors']}")
                    continue
                    
                events = result.get('data', {}).get('Get', {}).get('Event', [])
                
                if events:
                    avg_score = sum(e.get('_additional', {}).get('score', 0) for e in events) / len(events)
                    print(f"  Results: {len(events)} events, Avg score: {avg_score:.3f}")
                    for j, event in enumerate(events[:2]):
                        score = event.get('_additional', {}).get('score', 0)
                        print(f"    {j+1}. {event['title']} ({event['category']}) - {score:.3f}")
                else:
                    print("  No results")
                    
            except Exception as e:
                print(f"  Error: {e}")

def analyze_current_ai_functions():
    """Analyze the current AI functions in main.py"""
    print("\n=== CURRENT AI FUNCTIONS ANALYSIS ===")
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            
        # Look for AI function definitions
        ai_functions = [
            'extract_interests',
            'merge_interests', 
            'user_asked_for_events',
            'query_weaviate',
            'generate_reply'
        ]
        
        for func in ai_functions:
            if f'def {func}(' in content:
                print(f"✓ Found function: {func}")
                
                # Extract function content
                start = content.find(f'def {func}(')
                if start != -1:
                    # Find the end of the function (next def or class)
                    lines = content[start:].split('\n')
                    func_lines = []
                    indent_level = None
                    
                    for line in lines:
                        if line.strip().startswith('def ') and func_lines:
                            if not line.startswith(' ') and not line.startswith('\t'):
                                break
                        func_lines.append(line)
                        
                        if indent_level is None and line.strip() and not line.strip().startswith('def'):
                            # Determine indentation level
                            indent_level = len(line) - len(line.lstrip())
                            
                    # Analyze the function
                    func_content = '\n'.join(func_lines[:10])  # First 10 lines
                    print(f"  Preview: {func_content[:200]}...")
                    
                    # Check for common issues
                    if 'try:' not in func_content:
                        print("  ⚠️  No error handling")
                    if 'openai' in func_content.lower():
                        print("  ✓ Uses OpenAI")
                    if 'weaviate' in func_content.lower() or 'graphql' in func_content.lower():
                        print("  ✓ Uses Weaviate")
            else:
                print(f"✗ Missing function: {func}")
                
    except Exception as e:
        print(f"Error analyzing AI functions: {e}")

def main():
    """Run comprehensive AI system testing"""
    print("=== COMPREHENSIVE AI SYSTEM TESTING ===")
    print("Testing all AI components for reliability and performance")
    
    # Test 1: Weaviate search relevance
    search_results = test_weaviate_search_relevance()
    
    # Test 2: Query building strategies
    test_query_building_strategies()
    
    # Test 3: Analyze current AI functions
    analyze_current_ai_functions()
    
    # Generate recommendations
    print("\n=== RECOMMENDATIONS ===")
    
    if search_results:
        low_relevance = sum(1 for r in search_results if r['relevance_score'] < 50)
        if low_relevance > 0:
            print(f"1. Fix search relevance: {low_relevance} out of {len(search_results)} queries had low relevance")
            print("   - Implement activity mapping (cooking -> culinary, food, recipes)")
            print("   - Add context-aware query expansion")
            print("   - Use category-based filtering")
            
    print("2. Improve query building:")
    print("   - Use semantic expansion of search terms")
    print("   - Add activity-to-category mapping")
    print("   - Implement query scoring and ranking")
    
    print("3. Enhance error handling:")
    print("   - Add try-catch blocks to all AI functions")
    print("   - Implement fallback strategies")
    print("   - Add logging for debugging")
    
    print("4. Fix interest accumulation:")
    print("   - Use only current message interests")
    print("   - Clear accumulated interests between searches")
    print("   - Implement interest decay")

if __name__ == "__main__":
    main()
