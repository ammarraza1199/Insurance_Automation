# Automated Medical Billing & Information Extraction Workflow

This document outlines the workflow and architecture for an automated medical billing information system. The system extracts diagnostic codes (ICD-10) from insurance documents using open-source Object Character Recognition (OCR) and utilizes an open-source Large Language Model (LLM) to fetch and describe Current Procedural Terminology (CPT) codes, behaving similarly to the OpenAI API but using entirely open-source components.

## 1. System Workflow Overview

1. **Document Upload**: The user uploads a medical or insurance document (PDF, Image).
2. **OCR Processing**: An open-source OCR engine scans the document to extract raw text.
3. **Information Extraction (ICD-10 Search)**: An NLP processor or Regex rule engine identifies and extracts the required user information, specifically the Diagnose (ICD-10) codes.
4. **CPT Code Input & Query**: The user (or the system) inputs specific CPT codes into the system.
5. **Open-Source LLM (OpenAI API Alternative)**: The system queries a locally hosted open-source LLM (configured to have a drop-in OpenAI-compatible API) to fetch the accurate medical description and context for the provided CPT codes.
6. **Data Storage**: Processed patient data, extracted ICD-10 codes, and CPT AI descriptions are stored securely in a MongoDB database.
7. **Dashboard & Filtering**: The frontend UI presents a dashboard where users can view records and dynamically filter patient data by Patient Name, ICD Code, or CPT Code.

## 2. Step-by-Step Architecture & Open Source Tools

### Step 1: Document Ingestion & OCR
*   **Objective**: Extract raw, readable text from scanned images, PDFs, or faxes.
*   **Open-Source Tools**:
    *   **EasyOCR** or **PaddleOCR**: Excellent open-source models for extracting text from images with high accuracy, even for complicated layouts.
    *   **Tesseract OCR**: A highly reliable, traditional open-source OCR engine maintained by Google.
*   **Workflow**: Document -> Image Preprocessing (OpenCV) -> OCR Engine -> Raw Text.

### Step 2: Information Extraction (ICD-10 Codes)
*   **Objective**: Sift through the raw text to find patient information and Diagnosis codes (ICD-10).
*   **Open-Source Tools**:
    *   **Regular Expressions (Regex)**: ICD-10 codes follow a strict format (e.g., A00.0 - Z99.9). Regex is highly efficient for pattern matching this.
    *   **spaCy (en_core_web_sm)**: An open-source NLP library for Named Entity Recognition (NER) to extract Patient Name, Date of Birth, and Insurance ID.
    *   **Hugging Face Transformers**: Open-source Zero-shot classification models (like `BART-large-MNLI`) to identify context around the codes.

### Step 3: CPT Code Description via Open-Source LLM
*   **Objective**: The user inputs CPT codes, and the system looks up their descriptions using an open-source model, substituting the need for a paid OpenAI API.
*   **Open-Source Tools**:
    *   **Ollama Toolkit / vLLM**: Tools to run open-source Large Language Models locally. They provide an **OpenAI-compatible API server**. This means your code can still use the standard `openai` Python library, but requests are routed to your local free model.
    *   **Recommended Open-Source Models**:
        *   **Llama-3 (8B)** by Meta: Fast, highly capable, and easily runs on consumer hardware.
        *   **Mistral-7B-Instruct**: Excellent at instruction following and medical terminology decoding.
        *   **BioMistral / Meditron**: Specialized open-source models trained specifically on medical data for higher clinical accuracy.
*   **Workflow**: User submits CPT Codes (e.g., 99213) -> Request sent to local `http://localhost:11434/v1` (Ollama/vLLM) -> LLM generates the medical billing description -> Returned to user.

### Step 4: Data Storage (MongoDB)
*   **Objective**: Securely store and index the parsed patient demographic data, diagnostic codes, and procedural information so it is rapidly queryable.
*   **Tools**:
    *   **MongoDB**: A highly flexible NoSQL document database perfect for storing varying structures of medical JSON data (like nested patient infos, lists of codes, and AI generated descriptions).
    *   **Motor / PyMongo**: Async Python drivers for interacting with MongoDB from the FastAPI backend.
*   **Workflow**: Evaluated Patient Data + ICD-10 + CPT + LLM Details -> Saved as a JSON Document in the MongoDB Collection.

### Step 5: Frontend Dashboard & Filtering
*   **Objective**: Provide an interactive interface for administrators or billers to upload files and search existing patient records using specific parameters.
*   **Tools**:
    *   **React.js / Vue.js**: For building the responsive frontend Dashboard interface.
    *   **Data Grids / Table Libraries**: For clean dashboard aesthetics and sortable data tables (e.g., AG Grid, MUI DataGrid).
*   **Workflow**: User opens Dashboard -> Inputs filter parameter (e.g., `Patient Name = "John Doe"`, `ICD-10 = "E11.9"`, or `CPT = "99213"`) -> Frontend queries FastAPI backend search endpoints -> Dashboard Data Table updates with matching records in real-time.

## 3. Technology Stack

*   **Frontend**: React.js / Vue.js (for user dashboard and document upload).
*   **Backend / API**: FastAPI (Python) - highly performant and great for serving ML models.
*   **Database**: MongoDB (NoSQL) for flexible JSON document storage and querying.
*   **OCR Engine**: EasyOCR / Tesseract OCR.
*   **NLP & Extraction**: Python `re` (Regex) + spaCy.
*   **LLM Serving**: Ollama / vLLM.
*   **LLM Model**: Llama-3 8B / Mistral 7B.

## 4. API Endpoint Example (FastAPI + Local LLM)

Even though you are using an open-source model, the code resembles standard OpenAI API usage because of Ollama/vLLM's compatibility:

```python
from openai import OpenAI
from fastapi import FastAPI

app = FastAPI()

# Pointing the OpenAI client to the local Open-Source server (e.g., Ollama)
client = OpenAI(base_url="http://localhost:11434/v1", api_key="not-needed")

@app.post("/get_cpt_description")
def get_cpt_description(cpt_code: str):
    response = client.chat.completions.create(
        model="llama3", # Or mistral
        messages=[
            {"role": "system", "content": "You are a helpful medical billing assistant. Provide the detailed description for the provided CPT code."},
            {"role": "user", "content": f"What is the medical description for CPT code: {cpt_code}?"}
        ]
    )
    return {"cpt_code": cpt_code, "description": response.choices[0].message.content}
```

## 5. Summary of Benefits
1. **Cost-Effective**: No recurring costs for API calls (unlike the official OpenAI API).
2. **Data Privacy / HIPAA Compliant**: Since the OCR and LLM both run locally or on your private cloud, sensitive Personal Health Information (PHI) never leaves your servers.
3. **Customizable**: You can fine-tune the open-source LLM specifically on medical coding guidelines.
