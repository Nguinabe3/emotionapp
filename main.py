from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from transformers import pipeline
import logging
from fastapi.exceptions import RequestValidationError  # Import RequestValidationError

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
    classifier = None  # Ensure classifier is set to None if loading fails

# Define request and response models
class TextRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=500)

    @validator('text')
    def text_must_not_be_whitespace(cls, v):
        if v.strip() == '':
            raise ValueError('Text must not be empty or whitespace only.')
        return v

class ClassificationResult(BaseModel):
    label: str
    score: float

# Define the classify endpoint
@app.post("/classify", response_model=ClassificationResult)
def classify_text(request: TextRequest):
    if classifier is None:
        logging.error("Classifier model not loaded.")
        raise HTTPException(status_code=500, detail="Classifier model not loaded.")
    try:
        outputs = classifier(request.text)
        # Since outputs is a list of dictionaries, pick the highest-scoring emotion
        best_prediction = max(outputs[0], key=lambda x: x['score'])
        return ClassificationResult(label=best_prediction['label'], score=best_prediction['score'])
    except Exception as e:
        logging.error(f"Error in classify_text: {e}")
        # It's better to raise an HTTPException here
        raise HTTPException(status_code=500, detail="An error occurred during classification.")

# Custom exception handler for request validation errors
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    errors = exc.errors()
    # Construct custom error messages
    error_messages = []
    for error in errors:
        # Log the error details
        logging.error(f"Validation error detail: {error}")
        error_type = error['type']
        msg = error['msg']
        if error_type == 'value_error.any_str.min_length':
            error_messages.append("Please enter at least 20 characters.")
        elif error_type == 'value_error.any_str.max_length':
            error_messages.append("Please limit your journal entry to 500 characters.")
        elif error_type == 'value_error':
            # This captures custom validator errors like 'Text must not be empty or whitespace only.'
            error_messages.append(msg)
        else:
            error_messages.append(msg)
    return JSONResponse(
        status_code=422,
        content={"detail": error_messages},
    )