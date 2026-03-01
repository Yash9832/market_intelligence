#!/usr/bin/env python3
"""
Advanced Chatbot Testing Script
Tests the improved Gemini 2.5-pro integration with detailed logging
"""

import asyncio
import requests
import json
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:8000"

def test_chatbot_query(message: str):
    """Test a single chatbot query with detailed output"""
    print(f"\n{'='*80}")
    print(f"🤖 TESTING QUERY: {message}")
    print(f"{'='*80}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chatbot/chat",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 RESPONSE SUMMARY:")
            print(f"   • Response Length: {len(data.get('response', ''))} characters")
            print(f"   • Tool Calls: {len(data.get('tool_calls', []))}")
            print(f"   • Has Charts: {'Yes' if data.get('chart_data') else 'No'}")
            print(f"   • Entities Found: {len(data.get('entities', {}).get('potential_stock_symbols', []))}")
            
            if data.get('tool_calls'):
                print(f"\n🔧 TOOL CALLS EXECUTED:")
                for i, tool_call in enumerate(data['tool_calls'], 1):
                    print(f"   {i}. {tool_call['tool']}: {tool_call['input']}")
            
            if data.get('entities') and data['entities'].get('potential_stock_symbols'):
                print(f"\n🎯 ENTITIES IDENTIFIED:")
                symbols = data['entities']['potential_stock_symbols']
                print(f"   • Stock Symbols: {', '.join(symbols)}")
            
            print(f"\n💬 CHATBOT RESPONSE:")
            print("-" * 60)
            print(data.get('response', 'No response'))
            print("-" * 60)
            
            if data.get('chart_data'):
                print(f"\n📈 CHART DATA AVAILABLE:")
                for symbol in data['chart_data'].keys():
                    chart_points = len(data['chart_data'][symbol].get('price_data', []))
                    print(f"   • {symbol}: {chart_points} data points")
            
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def main():
    """Run comprehensive chatbot tests"""
    print("🚀 ADVANCED CHATBOT TESTING SUITE")
    print("Testing Gemini 2.5-pro Integration with Enhanced Logging")
    
    # Test queries that should work well
    test_queries = [
        "What do you think I should do with my Google stock?",
        "Compare AMD and NVIDIA performance",
        "How is Microsoft going nowadays?",
        "Predict Apple's future price for the next 30 days",
        "Should I invest in Tesla right now?",
        "Tell me about Amazon's recent performance"
    ]
    
    print(f"\n📋 RUNNING {len(test_queries)} TEST QUERIES...")
    print("💡 Check the backend terminal for detailed Gemini interaction logs!")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 TEST {i}/{len(test_queries)}")
        test_chatbot_query(query)
        
        if i < len(test_queries):
            print(f"\n⏳ Waiting 3 seconds before next test...")
            import time
            time.sleep(3)
    
    print(f"\n✅ TESTING COMPLETE!")
    print("Check the backend terminal logs for detailed Gemini processing information.")
    print("Look for logs with emojis like 🤖, 🧠, 🔧, 📊, ✅ to track the full flow.")

if __name__ == "__main__":
    main()