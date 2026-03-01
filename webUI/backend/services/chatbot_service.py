"""
Chatbot service with Gemini 2.5-pro integration and financial data tools.
Uses proper function calling with Gemini as the main orchestrator.
"""

import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional
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
                    genai.protos.Tool(
                        function_declarations=[
                            genai.protos.FunctionDeclaration(
                                name='extract_entities',
                                description='Extract company names and stock symbols from user query',
                                parameters=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        'query': genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description='User query to analyze for companies/stocks'
                                        )
                                    },
                                    required=['query']
                                )
                            ),
                            genai.protos.FunctionDeclaration(
                                name='get_stock_data',
                                description='Get current stock data including price, market cap, P/E ratio',
                                parameters=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        'symbol': genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description='Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                        )
                                    },
                                    required=['symbol']
                                )
                            ),
                            genai.protos.FunctionDeclaration(
                                name='get_technical_analysis',
                                description='Get technical analysis and chart data for a stock',
                                parameters=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        'symbol': genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description='Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                        ),
                                        'period': genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description='Time period for analysis (3mo, 6mo, 1y)'
                                        )
                                    },
                                    required=['symbol']
                                )
                            ),
                            genai.protos.FunctionDeclaration(
                                name='predict_stock_price',
                                description='Generate future price predictions using Prophet model',
                                parameters=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        'symbol': genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description='Stock symbol (e.g., AAPL, MSFT, NVDA)'
                                        ),
                                        'forecast_days': genai.protos.Schema(
                                            type=genai.protos.Type.INTEGER,
                                            description='Number of days to forecast (default 30)'
                                        )
                                    },
                                    required=['symbol']
                                )
                            )
                        ]
                    )
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
        """
        try:
            response_data = {
                "message": message,
                "response": "",
                "tool_calls": [],
                "chart_data": None,
                "entities": None
            }
            
            logger.info(f"🤖 CHATBOT: Processing user message: '{message}'")
            
            # System prompt for financial assistant
            system_prompt = """You are an expert financial assistant with access to real-time stock data and prediction tools.

CONTEXT AWARENESS:
- Pay attention to conversation history - if previously discussing a company, maintain that context
- For follow-up questions like "what is their forecast?" refer to the most recent company discussed
- If unclear which company is referenced, ask for clarification instead of guessing

MANDATORY WORKFLOW for ALL stock-related queries:
1. ALWAYS call extract_entities(query="full user query") first to identify companies
2. IMMEDIATELY after, call get_stock_data(symbol="SYMBOL") to get current price and data
3. IMMEDIATELY after, call get_technical_analysis(symbol="SYMBOL") for comprehensive analysis

CRITICAL RULES:
- For questions like "What's Apple's current stock price?", you MUST call ALL THREE functions:
  extract_entities → get_stock_data → get_technical_analysis
- NEVER stop after just extract_entities - always continue with the full sequence
- Use these symbol mappings: Apple=AAPL, Microsoft=MSFT, Google=GOOGL, Amazon=AMZN, Tesla=TSLA, NVIDIA=NVDA
- For prediction queries, add predict_stock_price as the 4th function call
- For follow-up questions about the same company, use the previous context to identify the symbol
- Provide concise but comprehensive analysis - aim for clarity over length

Example sequence for "What's Apple's stock price?":
1. extract_entities(query="What's Apple's stock price?")  
2. get_stock_data(symbol="AAPL")
3. get_technical_analysis(symbol="AAPL")

Complete ALL steps for accurate financial analysis."""

            # Build conversation context for follow-up understanding
            conversation_context = []
            if conversation_history and len(conversation_history) > 0:
                # Add recent conversation history for context (last 2-3 exchanges)
                recent_messages = conversation_history[-4:]  # Last 4 messages (2 exchanges)
                
                for msg in recent_messages:
                    if isinstance(msg, dict):
                        # Handle frontend format: {role: 'user'/'assistant', content: '...'}
                        if msg.get("role") == "user":
                            conversation_context.append({"role": "user", "parts": [msg.get("content", "")]})
                        elif msg.get("role") == "assistant":
                            # Truncate long assistant responses but keep key context
                            content = msg.get("content", "")
                            if len(content) > 300:
                                content = content[:300] + "..."
                            conversation_context.append({"role": "model", "parts": [content]})
                        
                        # Handle backend format: {message: '...', response: '...'}  
                        elif msg.get("message"):
                            conversation_context.append({"role": "user", "parts": [msg["message"]]})
                            if msg.get("response"):
                                response = msg["response"][:300] + "..." if len(msg["response"]) > 300 else msg["response"]
                                conversation_context.append({"role": "model", "parts": [response]})
            
            # Start chat with conversation context
            chat = self.model.start_chat(history=conversation_context)
            
            # Send user message with clear instructions
            user_message = f"User query: {message}\n\nRemember: For stock analysis, call extract_entities with the full query, then get_stock_data and get_technical_analysis with the symbol."
            logger.info(f"🧠 GEMINI: Sending message to Gemini 2.5-pro...")
            
            response = chat.send_message(f"{system_prompt}\n\n{user_message}")
            logger.info(f"🧠 GEMINI: Received response from Gemini")
            
            # Process the response
            has_function_calls = False
            gemini_text_response = ""
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        logger.info(f"🔧 TOOL CALL: {part.function_call.name} with args {dict(part.function_call.args)}")
                        await self._handle_function_call(part.function_call, response_data)
                    elif hasattr(part, 'text') and part.text:
                        gemini_text_response += part.text
                        logger.info(f"💬 GEMINI TEXT: {part.text[:100]}...")
            
            # If Gemini made function calls, we need to send the results back to get a proper response
            if has_function_calls and response_data["tool_calls"]:
                logger.info(f"🔄 FUNCTION RESULTS: Sending tool results back to Gemini for final response")
                
                # Build tool results summary
                tool_results = []
                for tool_call in response_data["tool_calls"]:
                    if tool_call["tool"] == "stock_data" and tool_call["output"]:
                        stock_data = tool_call["output"]["stock_data"]
                        symbol = tool_call["output"]["symbol"]
                        tool_results.append(f"{symbol}: Price ${stock_data.get('current_price', 'N/A')}, Change {stock_data.get('price_change_percent', 'N/A')}%")
                    elif tool_call["tool"] == "technical_analysis":
                        symbol = tool_call["input"].split(",")[0]
                        tool_results.append(f"Technical analysis for {symbol} completed")
                    elif tool_call["tool"] == "price_prediction":
                        symbol = tool_call["input"].split(",")[0]
                        tool_results.append(f"Prediction for {symbol} completed")
                    elif tool_call["tool"] == "ner_extraction":
                        entities = tool_call["output"].get("entities", [])
                        if entities:
                            tool_results.append(f"Extracted entities: {', '.join([e['word'] for e in entities])}")
                
                # Send tool results back to Gemini for analysis
                results_message = f"Tool results: {'; '.join(tool_results)}. Now provide a comprehensive analysis and investment recommendation based on this data."
                logger.info(f"📊 SENDING RESULTS: {results_message}")
                
                try:
                    final_response = chat.send_message(results_message)
                    logger.info(f"📊 FINAL RESPONSE RECEIVED, type: {type(final_response)}")
                    
                    # Try to extract text from the final response
                    final_text = ""
                    if hasattr(final_response, 'candidates') and final_response.candidates:
                        for candidate in final_response.candidates:
                            if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        final_text = part.text
                                        break
                                if final_text:
                                    break
                    
                    if final_text:
                        response_data["response"] = final_text
                        logger.info(f"✅ FINAL RESPONSE EXTRACTED: {len(final_text)} characters")
                    else:
                        # Fallback if we can't extract text
                        logger.warning(f"⚠️  Could not extract text from final response")
                        response_data["response"] = "Based on the data analysis, I can provide you with a comprehensive stock assessment. Please try the query again for detailed results."
                        
                except Exception as e:
                    logger.error(f"❌ ERROR in final response handling: {e}")
                    response_data["response"] = "I've analyzed the stock data but encountered an issue generating the final response. Please try again."
                
            elif gemini_text_response:
                # Direct text response from Gemini
                response_data["response"] = gemini_text_response
                logger.info(f"📝 DIRECT RESPONSE: Using Gemini's direct text response")
            
            # Fallback if no function calls but financial intent detected
            if not response_data["tool_calls"] and self._has_financial_intent(message):
                logger.info("🔧 FALLBACK: Gemini didn't use tools, applying fallback processing")
                await self._fallback_financial_processing(message, response_data, conversation_history)
                
                # Generate response based on tool results
                if response_data["tool_calls"]:
                    response_data["response"] = await self._generate_summary_response(message, response_data["tool_calls"])
                    logger.info(f"📝 FALLBACK RESPONSE: Generated from tool results")
            
            # Enhanced fallback: Check if we only called extract_entities but not the full chain
            elif (len(response_data["tool_calls"]) == 1 and 
                  response_data["tool_calls"][0]["tool"] == "ner_extraction" and 
                  self._has_financial_intent(message)):
                logger.info("🔄 INCOMPLETE CHAIN: Only extract_entities called, completing the workflow")
                
                # Extract the symbol from entities
                entities = response_data["entities"]
                if entities and entities.get("potential_stock_symbols"):
                    # Try to find a valid stock symbol
                    symbols = entities["potential_stock_symbols"]
                    # Common company mappings
                    company_mappings = {
                        "APPLE": "AAPL", "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", 
                        "AMAZON": "AMZN", "TESLA": "TSLA", "NVIDIA": "NVDA"
                    }
                    
                    target_symbol = None
                    # Check if any organization matches our mappings
                    for org in entities.get("organizations", []):
                        if org.upper() in company_mappings:
                            target_symbol = company_mappings[org.upper()]
                            break
                    
                    # If not found, try the symbol list
                    if not target_symbol:
                        for symbol in symbols:
                            if symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]:
                                target_symbol = symbol
                                break
                    
                    # Complete the workflow with stock_data and technical_analysis
                    if target_symbol:
                        logger.info(f"🎯 COMPLETING WORKFLOW: Getting data for {target_symbol}")
                        
                        # Get stock data
                        stock_data, company_info = StockService.get_stock_info(target_symbol)
                        if stock_data:
                            stock_result = {
                                "symbol": target_symbol,
                                "stock_data": stock_data.dict(),
                                "company_info": company_info.dict() if company_info else None
                            }
                            response_data["tool_calls"].append({
                                "tool": "stock_data",
                                "input": target_symbol,
                                "output": stock_result
                            })
                            logger.info(f"✅ STOCK DATA: Retrieved for {target_symbol}")
                        
                        # Get technical analysis
                        analysis_data = StockService.get_technical_analysis(target_symbol, "3mo")
                        if analysis_data:
                            if not response_data["chart_data"]:
                                response_data["chart_data"] = {}
                            response_data["chart_data"][target_symbol] = analysis_data
                            response_data["tool_calls"].append({
                                "tool": "technical_analysis",
                                "input": f"{target_symbol}, 3mo",
                                "output": analysis_data
                            })
                            logger.info(f"✅ TECHNICAL ANALYSIS: Retrieved for {target_symbol}")
                        
                        # Generate comprehensive response
                        response_data["response"] = await self._generate_summary_response(message, response_data["tool_calls"])
                        logger.info(f"✅ WORKFLOW COMPLETED: Generated comprehensive response for {target_symbol}")
            
            # Final fallback if still no response
            if not response_data["response"]:
                response_data["response"] = "I'm here to help with stock analysis and financial questions. Try asking about a specific company like 'How is Apple performing?' or 'What's Microsoft's stock price?'"
                logger.warning("⚠️ DEFAULT RESPONSE: No proper response generated, using default message")
            
            # Log final summary
            logger.info(f"📊 SUMMARY: Tools called: {len(response_data['tool_calls'])}, Response length: {len(response_data['response'])}, Has charts: {response_data['chart_data'] is not None}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ ERROR: Processing message failed: {e}")
            return {
                "message": message,
                "response": f"I encountered an error: {str(e)}. Please try asking about a specific stock or company.",
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
            "nvidia", "tesla", "google", "amazon", "meta", "going", "how is",
            "forecast", "next week", "future", "predict", "analysis", "recommendation"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in financial_keywords)

    async def _fallback_financial_processing(self, message: str, response_data: Dict[str, Any], conversation_history: List[Dict] = None):
        """Fallback processing when Gemini doesn't make function calls"""
        try:
            # First, try to extract context from conversation history for follow-up questions
            context_symbols = set()
            if conversation_history:
                logger.info("🔍 CONTEXT: Checking conversation history for stock context")
                for msg in conversation_history[-3:]:  # Last 3 messages
                    if msg.get("tool_calls"):
                        for tool_call in msg["tool_calls"]:
                            if tool_call["tool"] in ["stock_data", "technical_analysis", "price_prediction"]:
                                # Extract symbol from tool input
                                input_str = tool_call["input"]
                                if isinstance(input_str, str) and len(input_str.split()) > 0:
                                    potential_symbol = input_str.split()[0].upper()
                                    if len(potential_symbol) <= 5:  # Stock symbols are usually 1-5 chars
                                        context_symbols.add(potential_symbol)
                                        logger.info(f"📈 CONTEXT FOUND: {potential_symbol} from previous conversation")
            
            # Extract entities from current message
            ner_result = ner_service.extract_entities(message)
            response_data["entities"] = ner_result
            response_data["tool_calls"].append({
                "tool": "ner_extraction",
                "input": message,
                "output": ner_result
            })
            
            # Get stock symbols from NER and context
            symbols = set()
            if ner_result.get("potential_stock_symbols"):
                symbols.update(ner_result["potential_stock_symbols"])
            
            # If no symbols found in current message but we have context, use context symbols
            if not symbols and context_symbols:
                symbols = context_symbols
                logger.info(f"🔄 USING CONTEXT: No symbols in current message, using context symbols: {symbols}")
            
            # Check for prediction keywords
            is_prediction_query = any(word in message.lower() for word in ["predict", "forecast", "future", "will", "expected", "next week", "next month"])
            
            # Process symbols
            if symbols:
                chart_data = {}
                for symbol in list(symbols)[:2]:  # Limit to 2 symbols
                    try:
                        # Always get stock data
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
                            
                            # Get technical analysis for charts
                            analysis_data = StockService.get_technical_analysis(symbol, "3mo")
                            if analysis_data:
                                chart_data[symbol] = analysis_data
                                response_data["tool_calls"].append({
                                    "tool": "technical_analysis",
                                    "input": f"{symbol}, 3mo",
                                    "output": analysis_data
                                })
                            
                            # Add prediction if requested OR if asking about forecast/future
                            if is_prediction_query:
                                # Determine forecast period from query
                                forecast_days = 30  # default
                                if "week" in message.lower():
                                    forecast_days = 7
                                elif "month" in message.lower():
                                    forecast_days = 30
                                
                                logger.info(f"📊 PREDICTION: Running {forecast_days}-day forecast for {symbol}")
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
                        logger.warning(f"Could not get data for {symbol}: {e}")
                
                response_data["chart_data"] = chart_data if chart_data else None
                
        except Exception as e:
            logger.error(f"Fallback processing error: {e}")

    async def _generate_summary_response(self, message: str, tool_calls: List[Dict]) -> str:
        """Generate a comprehensive summary response like Perplexity based on tool results"""
        try:
            logger.info(f"📝 GENERATING SUMMARY: Creating response from {len(tool_calls)} tool calls")
            
            # Organize data by symbol
            symbol_data = {}
            predictions = {}
            
            for tool_call in tool_calls:
                if tool_call["tool"] == "stock_data" and tool_call["output"]:
                    symbol = tool_call["output"]["symbol"]
                    symbol_data[symbol] = tool_call["output"]["stock_data"]
                elif tool_call["tool"] == "price_prediction" and tool_call["output"]:
                    symbol = tool_call["output"]["symbol"]
                    predictions[symbol] = tool_call["output"]["prediction"]
            
            if not symbol_data:
                return "I couldn't retrieve stock data for your query. Please try with a specific company name or stock symbol."
            
            # Build comprehensive response using Gemini for analysis
            context_parts = [f"User asked: {message}"]
            context_parts.append("\nStock Data Analysis:")
            
            for symbol, stock_data in symbol_data.items():
                current_price = stock_data.get("current_price", 0)
                price_change = stock_data.get("price_change", 0)
                price_change_percent = stock_data.get("price_change_percent", 0)
                market_cap = stock_data.get("market_cap", 0)
                pe_ratio = stock_data.get("pe_ratio", "N/A")
                volume = stock_data.get("volume", 0)
                
                context_parts.append(f"\n{symbol} Financial Metrics:")
                context_parts.append(f"- Current Price: ${current_price:.2f}")
                context_parts.append(f"- Change: ${price_change:.2f} ({price_change_percent:.2f}%)")
                if market_cap:
                    context_parts.append(f"- Market Cap: ${market_cap:,}")
                context_parts.append(f"- P/E Ratio: {pe_ratio}")
                if volume:
                    context_parts.append(f"- Volume: {volume:,}")
                
                # Add prediction data if available
                if symbol in predictions:
                    pred_data = predictions[symbol]
                    if isinstance(pred_data, dict):
                        current_pred = pred_data.get("current_price", current_price)
                        predicted_price = pred_data.get("predicted_price", 0)
                        if predicted_price:
                            change_pred = ((predicted_price - current_pred) / current_pred) * 100
                            context_parts.append(f"- 30-day Prediction: ${predicted_price:.2f} ({change_pred:+.1f}%)")
            
            context = "\n".join(context_parts)
            
            # Use Gemini to generate comprehensive analysis
            analysis_prompt = f"""Based on this financial data, provide a comprehensive stock analysis similar to a professional financial report:

{context}

Please provide:
1. **Performance Summary**: Current performance and key highlights
2. **Financial Analysis**: Key metrics analysis (price, market cap, P/E, etc.)
3. **Market Position**: How the stock is performing relative to market trends
4. **Investment Perspective**: Analysis for potential investors
5. **Key Takeaways**: Most important points for decision making

If predictions are available, include future outlook. Write in a professional but accessible tone, similar to financial news reports. Focus on actionable insights and be specific about numbers and percentages."""

            try:
                simple_model = genai.GenerativeModel("gemini-2.5-pro")
                analysis_response = simple_model.generate_content(analysis_prompt)
                
                if analysis_response.text:
                    logger.info(f"✅ ANALYSIS GENERATED: {len(analysis_response.text)} characters")
                    return analysis_response.text
                else:
                    logger.warning("⚠️ No text in Gemini analysis response")
                    return self._fallback_basic_response(symbol_data, predictions)
                    
            except Exception as e:
                logger.error(f"❌ Gemini analysis failed: {e}")
                return self._fallback_basic_response(symbol_data, predictions)
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            return "I've gathered the requested stock information for you."

    def _fallback_basic_response(self, symbol_data: Dict, predictions: Dict) -> str:
        """Fallback response when Gemini analysis fails"""
        response_parts = ["## Stock Analysis Summary\n"]
        
        for symbol, stock_data in symbol_data.items():
            current_price = stock_data.get("current_price", 0)
            price_change = stock_data.get("price_change", 0)
            price_change_percent = stock_data.get("price_change_percent", 0)
            market_cap = stock_data.get("market_cap", 0)
            
            trend = "📈" if price_change >= 0 else "📉"
            trend_word = "up" if price_change >= 0 else "down"
            
            response_parts.append(f"### {symbol} Analysis")
            response_parts.append(f"**Current Performance**: ${current_price:.2f}, {trend_word} {abs(price_change_percent):.2f}% {trend}")
            
            if market_cap:
                market_cap_b = market_cap / 1_000_000_000
                response_parts.append(f"**Market Capitalization**: ${market_cap_b:.1f}B")
            
            # Add prediction if available
            if symbol in predictions:
                pred_data = predictions[symbol]
                if isinstance(pred_data, dict) and pred_data.get("predicted_price"):
                    predicted_price = pred_data["predicted_price"]
                    change_pred = ((predicted_price - current_price) / current_price) * 100
                    response_parts.append(f"**30-day Forecast**: ${predicted_price:.2f} (Expected {change_pred:+.1f}% change)")
            
            response_parts.append("")
        
        return "\n".join(response_parts)


# Global instance
chatbot_service = ChatbotService()