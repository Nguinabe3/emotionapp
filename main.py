from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI()

# Load the emotion detection model
try:
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")

# Define request and response models
class TextRequest(BaseModel):
    text: str

class ClassificationResult(BaseModel):
    label: str
    score: float

# Define the classify endpoint
@app.post("/classify", response_model=ClassificationResult)
def classify_text(request: TextRequest):
    try:
        outputs = classifier(request.text)
        # Since outputs is a list of dictionaries, pick the highest-scoring emotion
        best_prediction = max(outputs[0], key=lambda x: x['score'])
        return ClassificationResult(label=best_prediction['label'], score=best_prediction['score'])
    except Exception as e:
        logging.error(f"Error in classify_text: {e}")
        return ClassificationResult(label="Error", score=0)