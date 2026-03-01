from transformers import pipeline
import json

def ner_extraction(text: str):
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
    
    ner_results = ner_pipeline(text)
    
    entities = []
    for ent in ner_results:
        entity = {
            "entity": ent['entity_group'],
            "word": ent['word'],
            "start": ent['start'],
            "end": ent['end'],
            "score": float(ent['score'])  # Convert to Python float here
        }
        entities.append(entity)
    
    return json.dumps({"text": text, "entities": entities}, indent=2)


# if __name__ == "__main__":
#     statement = "What’s the opportunity outlook for Quantum Computing?"
#     output_json = ner_extraction(statement)
#     print(output_json)