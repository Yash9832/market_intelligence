from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

def finbert_sentiment_analysis(statement: str):
    model_name = "ProsusAI/finbert"
    
    # Load pretrained model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # Create pipeline for sentiment-analysis
    sentiment_pipeline = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
    
    # Get sentiment result
    result = sentiment_pipeline(statement)

    return result


# if __name__ == "__main__":
#     text = "The company's quarterly earnings exceeded expectations, and the stock surged."
#     results = finbert_sentiment_analysis(text)
#     print(f"Input statement: {text}")
#     print(f"Predicted sentiment: {results}")