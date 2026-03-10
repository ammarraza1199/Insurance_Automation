# 🏥 Insurance Verification & Authorization Automation Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![AI-Ollama](https://img.shields.io/badge/AI-Ollama_Phi--3-informational?style=flat-square)](https://ollama.com/)
[![OCR-EasyOCR](https://img.shields.io/badge/OCR-EasyOCR-brightgreen?style=flat-square)](https://github.com/JaidedAI/EasyOCR)

A high-performance, privacy-first automated medical billing and information extraction platform. This system leverages state-of-the-art open-source OCR and Local LLMs to automate the ingestion of insurance documents, extracting critical ICD-10 diagnosis codes and enriching them with AI-generated CPT procedure descriptions—all while keeping sensitive Patient Health Information (PHI) entirely local.

---

## 📺 Project Demo

![Demo Video](Demo_Video/Insurnce_Automation_Demo_Video.mp4)

---

## 🚀 Key Features

*   **Automated Document Ingestion**: High-accuracy text extraction from images and PDFs using **EasyOCR**.
*   **Intelligent Data Parsing**: Structured extraction of patient demographics, member IDs, and **ICD-10 codes** using **spaCy NER** and optimized Regex patterns.
*   **Privacy-First AI Insights**: Zero-cost, local inference for CPT code descriptions using **Ollama (Phi-3)**. PHI never leaves your infrastructure.
*   **Asynchronous Relational Storage**: Robust data persistence using **PostgreSQL** with `SQLAlchemy` 2.x and `asyncpg`.
*   **Modern Interactive Dashboard**: A responsive **React 19** frontend featuring advanced real-time record filtering and management.

---

## 🏗️ High-Level Architecture

The platform follows a modern decoupled architecture, ensuring scalability and ease of deployment.

```mermaid
graph TD
    A[User / Client] -->|Upload Document| B[React Frontend]
    B -->|API Request| C[FastAPI Backend]
    C -->|Image Data| D[OCR Service - EasyOCR]
    D -->|Raw Text| E[NLP Analysis - spaCy/Regex]
    E -->|ICD-10 / Demographics| C
    C -->|CPT Code| F[LLM Service - Ollama/Phi-3]
    F -->|Medical Description| C
    C -->|Structured Data| G[(PostgreSQL DB)]
    G --> C
    C -->|Response| B
```

---

## 🔄 System Workflow

```mermaid
flowchart LR
    Start([Start]) --> Upload[Document Upload]
    Upload --> OCR[Text Extraction]
    OCR --> Extraction[Data Parsing & NER]
    Extraction --> AI[AI Context Enrichment]
    AI --> Store[Secure Storage]
    Store --> View[Dashboard Visualization]
    View --> End([End])
```

---

## 🧬 Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Vite/React)
    participant B as Backend (FastAPI)
    participant O as OCR (EasyOCR)
    participant L as LLM (Ollama)
    participant D as DB (PostgreSQL)

    U->>F: Upload Insurance Card/Form
    F->>B: POST /upload (File)
    B->>O: Extract Text from Image
    O-->>B: Raw Text
    B->>B: Parse ICD-10 & Patient Info
    B->>L: Query CPT Description (Ollama)
    L-->>B: JSON Description
    B->>D: Save Record
    D-->>B: Success
    B-->>F: JSON (Parsed Data + AI Insights)
    F-->>U: Display on Dashboard
```

---

## 🛠️ Tech Stack

### Backend
*   **Framework**: FastAPI (Python 3.11+)
*   **Database**: PostgreSQL 16 (Relational)
*   **ORM**: SQLAlchemy 2.0 (Async)
*   **OCR**: EasyOCR (PyTorch based)
*   **NLP**: spaCy (`en_core_web_sm`)
*   **LLM**: Ollama (Phi-3 / Mistral)

### Frontend
*   **Core**: React 19 (Hooks, Context API)
*   **Routing**: React Router 7
*   **Build Tool**: Vite 8
*   **Styling**: Modern CSS3 (Responsive Design)

---

## ⚡ Running Guide

For a detailed step-by-step installation, please refer to the [Full Running Guide](RUNNING_GUIDE.md).

### Quick Start (After Dependencies)

To run the full suite, you must have **4 processes** active:

1.  **Database**: `docker start insurance_postgres` (Port 5432)
2.  **AI Engine**: `ollama run phi3` (Port 11434)
3.  **Backend**: `cd backend && uvicorn main:app --reload` (Port 8000)
4.  **Frontend**: `cd frontend && npm run dev` (Port 5173)

---

## 🔐 Environment Variables

The backend can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/insurance_platform` | SQLAlchemy Connection String |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | URL for the local Ollama server |
| `OLLAMA_MODEL` | `phi3` | The AI model to use for CPT descriptions |

---

## 📂 Project Structure

```text
ocr_with_CPT_openAI/
├── backend/            # FastAPI Application & Services
│   ├── main.py         # Entry point & API routes
│   ├── database.py     # PostgreSQL Connection & Models
│   ├── ocr_service.py  # Image processing & NLP logic
│   └── llm_service.py  # AI Generation logic
├── frontend/           # Vite + React Dashboard
│   ├── src/            # Components & Application Logic
│   └── public/         # Static assets
├── Demo_Video/         # Project demonstration media
└── docs/               # Technical specifications & checklists
```

---

## 🤝 Contributing
Contributions are welcome! Please create an issue or pull request to suggest improvements.

## 📄 License
This project is for internal/educational use. Ensure compliance with medical data regulations (HIPAA/GDPR) when deploying.
