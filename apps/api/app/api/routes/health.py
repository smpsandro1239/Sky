from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Verifica a disponibilidade da API")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sky-api", "version": "0.1.0"}
