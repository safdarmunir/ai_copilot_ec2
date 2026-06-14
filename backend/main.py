import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from analytics_agent import AnalyticsAgent
from parser import extract_text
from chunker import chunk_text
from vector_store import VectorStore
from rag import RAGPipeline
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from report_generator import ReportGenerator
from router_agent import RouterAgent
report_generator = ReportGenerator()
from fastapi import UploadFile, File, HTTPException
from s3_service import S3Service
from fastapi import Depends
from sqlalchemy.orm import Session

from rds_database import engine, get_rds_db
from rds_models import Base, UploadedFile

from database import (
    init_db,
    save_chat,
    get_chat_history,
    clear_chat_history,
    save_report,
    get_reports
)

app = FastAPI(title="AI Business Copilot API")
init_db()
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
CHARTS_DIR = BASE_DIR / "data" / "charts"

REPORTS_DIR = BASE_DIR / "data" / "reports"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

app.mount(
    "/charts",
    StaticFiles(directory=CHARTS_DIR),
    name="charts"
)
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

vector_store = VectorStore()
rag = RAGPipeline()

analytics_agent = AnalyticsAgent()

router_agent = RouterAgent(
    rag_pipeline=rag,
    analytics_agent=analytics_agent,
    upload_dir=UPLOAD_DIR
)

class DashboardRequest(BaseModel):
    filename: str


class AskRequest(BaseModel):
    question: str
    filename: str | None = None

class AnalyzeRequest(BaseModel):
    filename: str
    question: str

class CopilotRequest(BaseModel):
    question: str
    filename: str | None = None


class ReportRequest(BaseModel):
    filename: str
    question: str
    answer: str
    table: list
    chart_path: str | None = None

@app.get("/")
def root():
    return {
        "message": "AI Business Operations Copilot API is running"
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    allowed_extensions = [".pdf", ".docx", ".txt", ".csv", ".xlsx"]

    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    file_path = UPLOAD_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Analytics files
        if file_ext in [".csv", ".xlsx"]:
            return {
                "message": "Data file uploaded successfully",
                "filename": file.filename,
                "type": "analytics"
            }

        # Document files
        text = extract_text(file_path)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from this document"
            )

        chunks = chunk_text(text)

        vector_store.add_chunks(
            chunks=chunks,
            filename=file.filename
        )

        return {
            "message": "Document uploaded and indexed successfully",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "type": "document"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/ask")
def ask_question(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        result = rag.answer_question(
        question=request.question,
        filename=request.filename
    )


        return {
            "question": request.question,
            "filename": request.filename,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/documents")
def list_documents():
    try:
        files = []

        for file in UPLOAD_DIR.iterdir():
            if file.is_file():
                files.append({
                    "filename": file.name,
                    "size_kb": round(file.stat().st_size / 1024, 2)
                })

        return {
            "documents": files,
            "total": len(files)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.delete("/document/{filename}")
def delete_document(filename: str):
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        os.remove(file_path)

        vector_store.delete_by_filename(filename)

        return {
            "message": "Document deleted successfully",
            "filename": filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )   
    

@app.post("/clear-memory")
def clear_memory():
    rag.clear_memory()
    return {"message": "Chat memory cleared successfully"}


@app.post("/analyze")
def analyze_data(request: AnalyzeRequest):
    file_path = UPLOAD_DIR / request.filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        result = analytics_agent.analyze(
            file_path=str(file_path),
            question=request.question
        )

        return {
            "filename": request.filename,
            "question": request.question,
            "answer": result["answer"],
            "analysis_type": result["analysis_type"],
            "chart_path": result["chart_path"],
            "table": result["table"],
            "columns": result["columns"],
            "rows": result["rows"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.post("/generate-report")
def generate_report(request: ReportRequest):
    try:
        report_path = report_generator.generate_report(
            filename=request.filename,
            question=request.question,
            answer=request.answer,
            table=request.table,
            chart_path=request.chart_path
        )

        save_report(
            filename=request.filename,
            question=request.question,
            report_path=report_path
        )

        return {
            "message": "Report generated successfully",
            "report_path": report_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

@app.post("/copilot")
def copilot(request: CopilotRequest):
    try:
        result = router_agent.run(
            question=request.question,
            filename=request.filename
        )

        save_chat(
            role="user",
            content=request.question,
            route=result.get("route"),
            filename=request.filename
        )

        if result.get("answer"):
            save_chat(
                role="assistant",
                content=result["answer"],
                route=result.get("route"),
                filename=request.filename
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@app.post("/dashboard")
def dashboard(request: DashboardRequest):

    file_path = UPLOAD_DIR / request.filename

    result = analytics_agent.get_dashboard_metrics(
        str(file_path)
    )

    return result


@app.post("/dashboard-data")
def dashboard_data(request: DashboardRequest):

    file_path = UPLOAD_DIR / request.filename

    return analytics_agent.get_dashboard_data(
        str(file_path)
    )


@app.get("/chat-history")
def chat_history():
    return {
        "history": get_chat_history()
    }


@app.delete("/chat-history")
def delete_chat_history():
    clear_chat_history()
    return {
        "message": "Chat history cleared"
    }


@app.get("/reports")
def reports():
    return {
        "reports": get_reports()
    }


@app.post("/files/upload")
async def upload_file_to_s3(
    file: UploadFile = File(...),
    db: Session = Depends(get_rds_db),
):
    try:
        s3_service = S3Service()
        result = s3_service.upload_file(file)

        uploaded_file = UploadedFile(
            original_filename=result["original_filename"],
            s3_key=result["s3_key"],
            bucket=result["bucket"],
            content_type=result["content_type"],
        )

        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)

        return {
            "message": "File uploaded to S3 and metadata saved to RDS successfully",
            "data": {
                "id": uploaded_file.id,
                "original_filename": uploaded_file.original_filename,
                "s3_key": uploaded_file.s3_key,
                "bucket": uploaded_file.bucket,
                "content_type": uploaded_file.content_type,
                "uploaded_at": uploaded_file.uploaded_at,
            },
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))
    

@app.get("/files")
def list_uploaded_files(db: Session = Depends(get_rds_db)):
    files = db.query(UploadedFile).order_by(UploadedFile.uploaded_at.desc()).all()

    return {
        "count": len(files),
        "data": [
            {
                "id": item.id,
                "original_filename": item.original_filename,
                "s3_key": item.s3_key,
                "bucket": item.bucket,
                "content_type": item.content_type,
                "uploaded_at": item.uploaded_at,
            }
            for item in files
        ],
    }   