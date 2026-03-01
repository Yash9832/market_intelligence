import requests
import json
import time

def test_chatbot():
    print("🤖 Testing Enhanced Chatbot with Gemini 2.5-pro")
    print("=" * 60)
    
    # Test query
    query = "How is Microsoft going nowadays?"
    print(f"Query: {query}")
    
    try:
        response = requests.post(
            'http://localhost:8000/chatbot/chat', 
            json={'message': query}, 
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tool calls made: {len(data.get('tool_calls', []))}")
            print(f"Has chart data: {'Yes' if data.get('chart_data') else 'No'}")
            print(f"Entities found: {data.get('entities', {}).get('potential_stock_symbols', [])}")
            print("\n💬 Response:")
            print("-" * 40)
            print(data.get('response', 'No response'))
            print("-" * 40)
            
            # Show tool calls
            if data.get('tool_calls'):
                print(f"\n🔧 Tool calls executed:")
                for tool in data['tool_calls']:
                    print(f"  • {tool['tool']}: {tool['input']}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - this might indicate Gemini is processing")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chatbot()