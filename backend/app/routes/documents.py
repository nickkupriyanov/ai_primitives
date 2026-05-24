from fastapi import APIRouter, Request

from app.schemas import QuestionRequest, QuestionResponse, SourceCreate, SourceOut
from app.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(request: Request) -> DocumentService:
    service = getattr(request.app.state, "document_service", None)
    if service is None:
        service = DocumentService()
        request.app.state.document_service = service
    return service


@router.post(
    "/ingest",
    response_model=SourceOut,
    summary="Ingest a document",
    description="Upload and chunk a document for Q&A.",
)
async def ingest_document(
    payload: SourceCreate,
    request: Request,
) -> SourceOut:
    service = get_document_service(request)
    return await service.ingest(payload)


@router.post(
    "/query",
    response_model=QuestionResponse,
    summary="Query documents",
    description="Ask a question and get an answer with citations from ingested documents.",
)
async def query_documents(
    payload: QuestionRequest,
    request: Request,
) -> QuestionResponse:
    service = get_document_service(request)
    return await service.query(payload)


@router.get(
    "/sources",
    response_model=list[SourceOut],
    summary="List sources",
    description="List all ingested document sources.",
)
async def list_sources(request: Request) -> list[SourceOut]:
    service = get_document_service(request)
    return service.list_sources()


@router.delete(
    "/sources/{source_id}",
    summary="Delete a source",
    description="Delete a document source and all its chunks.",
)
async def delete_source(source_id: str, request: Request) -> dict:
    service = get_document_service(request)
    service.delete_source(source_id)
    return {"deleted": True}


@router.post(
    "/demo/{scenario}",
    response_model=list[SourceOut],
    summary="Load demo scenario",
    description="Load a pre-built demo scenario with documents.",
)
async def load_demo_scenario(
    scenario: str,
    request: Request,
) -> list[SourceOut]:
    service = get_document_service(request)
    return await service.load_demo_scenario(scenario)
