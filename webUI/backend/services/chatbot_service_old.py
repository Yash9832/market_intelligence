"""
Chatbot service with Gemini 2.5-pro integration and financial data tools.
Uses proper function calling with Gemini as the main orchestrator.
"""

import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
import logging

# Import our services
from .ner_service import ner_service
from .stock_service import StockService
from .prediction_service import PredictionService

# Get the GEMINI API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCMil_XRE20uMZPkT2X5BOKLSUDKgVVXl0')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)

class ChatbotService:
    """Service for handling chatbot interactions with Gemini 2.5-pro and financial tools"""
    
    def __init__(self):
        """Initialize the chatbot service with Gemini 2.5-pro"""
        try:
            # Initialize Gemini 2.5-pro model with function calling
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-pro",
                tools=[
                    {
                        'name': 'extract_entities',
                        'description': 'Extract company names and stock symbols from user query',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'query': {
                                    'type': 'string',
                                    'description': 'User query to analyze for companies/stocks'
                                }
                            },
                            'required': ['query']
                        }
                    },
                    {
                        'name': 'get_stock_data',
                        'description': 'Get current stock data including price, market cap, P/E ratio',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'symbol': {
                                    'type': 'string',
                                    'description': 'Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                }
                            },
                            'required': ['symbol']
                        }
                    },
                    {
                        'name': 'get_technical_analysis',
                        'description': 'Get technical analysis and chart data for a stock',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'symbol': {
                                    'type': 'string',
                                    'description': 'Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                },
                                'period': {
                                    'type': 'string',
                                    'description': 'Time period for analysis (3mo, 6mo, 1y)',
                                    'default': '3mo'
                                }
                            },
                            'required': ['symbol']
                        }
                    },
                    {
                        'name': 'predict_stock_price',
                        'description': 'Generate future price predictions using Prophet model',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'symbol': {
                                    'type': 'string',
                                    'description': 'Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                },
                                'forecast_days': {
                                    'type': 'integer',
                                    'description': 'Number of days to forecast (default 30)',
                                    'default': 30
                                }
                            },
                            'required': ['symbol']
                        }
                    }
                ]
            )
            
            self.conversation_history = []
            logger.info("Chatbot service initialized with Gemini 2.5-pro and financial tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize chatbot service: {e}")
            raise
    
    async def process_message(self, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process a user message using Gemini 2.5-pro with function calling
        
        Args:
            message: User's input message
            conversation_history: Previous conversation context
            
        Returns:
            Dict containing response, tool calls, and chart data
        """
        try:
            response_data = {
                "message": message,
                "response": "",
                "tool_calls": [],
                "chart_data": None,
                "entities": None
            }
            
            # System prompt for financial assistant
            system_prompt = """You are an expert financial assistant with access to real-time stock data and prediction tools.
            
Your capabilities:
1. Extract company names/stock symbols from user queries
2. Get current stock data (price, market cap, P/E ratio, etc.)
3. Perform technical analysis with chart data
4. Generate future price predictions using Prophet ML model

Guidelines:
- Always use the available tools to get accurate, real-time data
- For queries about stock performance, get both current data and technical analysis
- For prediction requests, use the predict_stock_price tool
- Provide comprehensive, actionable insights
- If you don't recognize a company name, still try common variations (Apple->AAPL, Microsoft->MSFT)
"""

            # Build conversation context
            conversation = []
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 messages for context
                    conversation.extend([
                        {"role": "user", "parts": [msg.get("message", "")]},
                        {"role": "model", "parts": [msg.get("response", "")]}
                    ])
            
            # Add current message
            conversation.append({"role": "user", "parts": [f"{system_prompt}\n\nUser query: {message}"]})
            
            # Get response from Gemini with function calling
            chat = self.model.start_chat(history=conversation[:-1])
            response = chat.send_message(conversation[-1]["parts"][0])
            
            # Process function calls if any
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        await self._handle_function_call(part.function_call, response_data)
                    elif hasattr(part, 'text') and part.text:
                        response_data["response"] += part.text
            
            # If Gemini didn't make function calls but we detect financial intent, help it out
            if not response_data["tool_calls"] and self._has_financial_intent(message):
                await self._fallback_financial_processing(message, response_data)
            
            # If we have tool results but no response text, generate one
            if response_data["tool_calls"] and not response_data["response"]:
                response_data["response"] = await self._generate_response_from_tools(message, response_data["tool_calls"])
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": message,
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "tool_calls": [],
                "chart_data": None,
                "entities": None
            }

    async def _handle_function_call(self, function_call, response_data: Dict[str, Any]):
        """Handle function calls from Gemini"""
        try:
            function_name = function_call.name
            args = {key: value for key, value in function_call.args.items()}
            
            logger.info(f"Executing function: {function_name} with args: {args}")
            
            if function_name == "extract_entities":
                result = ner_service.extract_entities(args["query"])
                response_data["entities"] = result
                response_data["tool_calls"].append({
                    "tool": "ner_extraction",
                    "input": args["query"],
                    "output": result
                })
                
            elif function_name == "get_stock_data":
                symbol = args["symbol"].upper()
                stock_data, company_info = StockService.get_stock_info(symbol)
                if stock_data:
                    result = {
                        "symbol": symbol,
                        "stock_data": stock_data.dict(),
                        "company_info": company_info.dict() if company_info else None
                    }
                    response_data["tool_calls"].append({
                        "tool": "stock_data",
                        "input": symbol,
                        "output": result
                    })
                
            elif function_name == "get_technical_analysis":
                symbol = args["symbol"].upper()
                period = args.get("period", "3mo")
                analysis_data = StockService.get_technical_analysis(symbol, period)
                if analysis_data:
                    if not response_data["chart_data"]:
                        response_data["chart_data"] = {}
                    response_data["chart_data"][symbol] = analysis_data
                    response_data["tool_calls"].append({
                        "tool": "technical_analysis",
                        "input": f"{symbol}, {period}",
                        "output": analysis_data
                    })
                
            elif function_name == "predict_stock_price":
                symbol = args["symbol"].upper()
                forecast_days = args.get("forecast_days", 30)
                prediction_data = PredictionService.predict_stock_price(symbol, forecast_days)
                if prediction_data:
                    result = {
                        "symbol": symbol,
                        "forecast_days": forecast_days,
                        "prediction": prediction_data.dict()
                    }
                    response_data["tool_calls"].append({
                        "tool": "price_prediction",
                        "input": f"{symbol}, {forecast_days} days",
                        "output": result
                    })
                    
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")

    def _has_financial_intent(self, message: str) -> bool:
        """Check if message has financial/stock intent"""
        financial_keywords = [
            "stock", "price", "invest", "buy", "sell", "market", "trading", 
            "performance", "prediction", "forecast", "apple", "microsoft", 
            "nvidia", "tesla", "google", "amazon", "meta", "going"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in financial_keywords)

    async def _fallback_financial_processing(self, message: str, response_data: Dict[str, Any]):
        """Fallback processing when Gemini doesn't make function calls but should"""
        try:
            # Extract entities first
            ner_result = ner_service.extract_entities(message)
            response_data["entities"] = ner_result
            response_data["tool_calls"].append({
                "tool": "ner_extraction",
                "input": message,
                "output": ner_result
            })
            
            # Get stock symbols
            symbols = set()
            if ner_result.get("potential_stock_symbols"):
                symbols.update(ner_result["potential_stock_symbols"])
            
            # If we found symbols, get their data
            if symbols:
                chart_data = {}
                for symbol in list(symbols)[:3]:  # Limit to 3 symbols
                    try:
                        # Get stock data
                        stock_data, company_info = StockService.get_stock_info(symbol)
                        if stock_data:
                            result = {
                                "symbol": symbol,
                                "stock_data": stock_data.dict(),
                                "company_info": company_info.dict() if company_info else None
                            }
                            response_data["tool_calls"].append({
                                "tool": "stock_data",
                                "input": symbol,
                                "output": result
                            })
                            
                            # Get technical analysis
                            analysis_data = StockService.get_technical_analysis(symbol, "3mo")
                            if analysis_data:
                                chart_data[symbol] = analysis_data
                                response_data["tool_calls"].append({
                                    "tool": "technical_analysis",
                                    "input": f"{symbol}, 3mo",
                                    "output": analysis_data
                                })
                    except Exception as e:
                        logger.warning(f"Could not get data for {symbol}: {e}")
                
                response_data["chart_data"] = chart_data if chart_data else None
                
        except Exception as e:
            logger.error(f"Fallback processing error: {e}")

    async def _generate_response_from_tools(self, message: str, tool_calls: List[Dict]) -> str:
        """Generate response text based on tool results"""
        try:
            # Create a summary of tool results
            context_parts = [f"User asked: {message}", "\nTool results:"]
            
            for tool_call in tool_calls:
                tool_name = tool_call["tool"]
                tool_input = tool_call["input"]
                tool_output = tool_call.get("output", {})
                
                if tool_name == "stock_data" and tool_output:
                    stock_data = tool_output.get("stock_data", {})
                    symbol = tool_output.get("symbol", tool_input)
                    context_parts.append(f"\n{symbol}: ${stock_data.get('current_price', 'N/A')} "
                                       f"({stock_data.get('price_change_percent', 'N/A')}%)")
            
            context = "\n".join(context_parts)
            
            # Use a simple Gemini call to generate response
            simple_model = genai.GenerativeModel("gemini-2.5-pro")
            prompt = f"""Based on the following financial data, provide a helpful and insightful response:

{context}

Provide a concise, professional response focusing on the key insights from the data."""
            
            response = simple_model.generate_content(prompt)
            return response.text if response.text else "I've gathered the requested financial data for you."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I've gathered the requested financial information for you."
                if stock_data_results:
                    gemini_response = await self._generate_gemini_response(
                        message, stock_data_results, ner_result, conversation_history
                    )
                    response_data["response"] = gemini_response
                else:
                    response_data["response"] = "I couldn't find specific stock data for the entities mentioned. Could you provide a specific stock symbol or company name?"
            
            else:
                # No symbols found, ask for clarification
                clarification_prompt = f"""
                User Query: "{message}"
                
                I identified some entities but couldn't map them to specific stock symbols. 
                Please provide a helpful response asking the user to be more specific about which company or stock they want to analyze.
                Keep it conversational and suggest some popular companies they might be interested in.
                """
                
                try:
                    messages = [SystemMessage(content="You are a helpful financial assistant."), 
                              HumanMessage(content=clarification_prompt)]
                    result = self.llm(messages)
                    response_data["response"] = result.content
                except Exception as e:
                    response_data["response"] = "I didn't identify any specific stocks or companies in your query. Could you mention a specific company name or stock symbol you'd like to analyze? For example: Apple, Microsoft, NVDA, TSLA, etc."
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I've gathered the requested financial information for you."


# Global instance
chatbot_service = ChatbotService()
    
    async def _generate_gemini_response(self, query: str, stock_data_results: List[Dict], ner_result: Dict, conversation_history: List[Dict] = None) -> str:
        """Generate intelligent response using Gemini"""
        try:
            # Prepare context for Gemini
            context = f"""
            User Query: "{query}"
            
            Entities Identified: {ner_result.get('summary', '')}
            
            Stock Data Retrieved:
            """
            
            for stock_info in stock_data_results:
                symbol = stock_info["symbol"]
                data = stock_info["stock_data"]
                company = stock_info.get("company_info", {})
                
                context += f"""
                
                {symbol} - {company.get('longName', symbol)}:
                • Current Price: ${data['current_price']:.2f}
                • Change: ${data['price_change']:.2f} ({data['price_change_percent']:.2f}%)
                • Market Cap: ${data.get('market_cap', 0):,} if data.get('market_cap') else 'N/A'
                • P/E Ratio: {data.get('pe_ratio', 'N/A')}
                • 52 Week Range: ${data.get('week_52_low', 'N/A')} - ${data.get('week_52_high', 'N/A')}
                """
            
            # Add conversation history if available
            history_context = ""
            if conversation_history:
                history_context = "\nRecent Conversation:\n"
                for msg in conversation_history[-3:]:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    history_context += f"{role}: {content}\n"
            
            system_prompt = """You are a knowledgeable financial assistant. Provide comprehensive, insightful analysis based on the stock data provided. 
            
            Guidelines:
            - Be conversational and helpful
            - Highlight key metrics and trends
            - Use emojis appropriately (📈 for gains, 📉 for losses)
            - Provide actionable insights
            - Keep response concise but informative
            - If multiple stocks are analyzed, compare them briefly
            """
            
            prompt = f"""
            {system_prompt}
            
            {context}
            {history_context}
            
            Please provide a comprehensive analysis addressing the user's query. Include key insights about the company's performance, current valuation, and any notable trends.
            """
            
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
            result = self.llm(messages)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(stock_data_results)
    
    def _generate_fallback_response(self, stock_data_results: List[Dict]) -> str:
        """Generate a fallback response without Gemini"""
        if not stock_data_results:
            return "I couldn't find data for the requested stocks."
        
        response_parts = []
        response_parts.append("Here's what I found:")
        
        for stock_info in stock_data_results:
            symbol = stock_info["symbol"]
            data = stock_info["stock_data"]
            company = stock_info.get("company_info", {})
            
            response_parts.append(f"\n**{symbol}** - {company.get('longName', symbol)}")
            response_parts.append(f"• Current Price: ${data['current_price']:.2f}")
            
            change_color = "📈" if data['price_change'] >= 0 else "📉"
            response_parts.append(f"• Change: {change_color} ${data['price_change']:.2f} ({data['price_change_percent']:.2f}%)")
            
            if data.get('market_cap'):
                response_parts.append(f"• Market Cap: ${data['market_cap']:,}")
            
            if data.get('pe_ratio'):
                response_parts.append(f"• P/E Ratio: {data['pe_ratio']:.2f}")
        
        return "\n".join(response_parts)

# Global instance
chatbot_service = ChatbotService()