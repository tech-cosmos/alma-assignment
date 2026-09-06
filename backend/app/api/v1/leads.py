import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import EmailStr, ValidationError

from app.api.deps import CurrentUser, EmailDep, SessionDep, SettingsDep, StorageDep
from app.models.lead import Lead, LeadState
from app.repositories.lead import LeadRepository
from app.schemas.lead import LeadCreate, LeadList, LeadRead, LeadStateUpdate
from app.services.lead import InvalidTransition, LeadService
from app.services.notify import LeadNotifier
from app.services.resume import InvalidResume, validate_resume

router = APIRouter(prefix="/leads", tags=["leads"])


async def _get_lead_or_404(session: SessionDep, lead_id: uuid.UUID) -> Lead:
    lead = await LeadRepository(session).get(lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    first_name: Annotated[str, Form(min_length=1, max_length=200)],
    last_name: Annotated[str, Form(min_length=1, max_length=200)],
    email: Annotated[EmailStr, Form()],
    resume: UploadFile,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    settings: SettingsDep,
    storage: StorageDep,
    email_adapter: EmailDep,
) -> LeadRead:
    # Read one byte past the limit so oversized files are rejected without buffering them all.
    data = await resume.read(settings.max_resume_bytes + 1)
    try:
        upload = validate_resume(resume.filename, data, max_bytes=settings.max_resume_bytes)
    except InvalidResume as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    try:
        payload = LeadCreate(
            first_name=first_name.strip(), last_name=last_name.strip(), email=email
        )
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.errors(include_url=False)
        ) from exc
    lead = await LeadService(LeadRepository(session), storage).create(payload, upload)
    snapshot = LeadRead.model_validate(lead)

    # Runs after the response is sent, which is after the commit above.
    notifier = LeadNotifier(email_adapter, settings)
    background_tasks.add_task(notifier.notify_new_lead, snapshot)
    return snapshot


@router.get("", response_model=LeadList)
async def list_leads(
    _: CurrentUser,
    session: SessionDep,
    state: Annotated[LeadState | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeadList:
    items, total = await LeadRepository(session).list(state=state, limit=limit, offset=offset)
    return LeadList(
        items=[LeadRead.model_validate(lead) for lead in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(_: CurrentUser, session: SessionDep, lead_id: uuid.UUID) -> LeadRead:
    return LeadRead.model_validate(await _get_lead_or_404(session, lead_id))


@router.patch("/{lead_id}/state", response_model=LeadRead)
async def update_lead_state(
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
    lead_id: uuid.UUID,
    body: LeadStateUpdate,
) -> LeadRead:
    lead = await _get_lead_or_404(session, lead_id)
    service = LeadService(LeadRepository(session), storage)
    try:
        lead = await service.transition(lead, body.state, user)
    except InvalidTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return LeadRead.model_validate(lead)


@router.get("/{lead_id}/resume", response_model=None)
async def download_resume(
    _: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
    lead_id: uuid.UUID,
) -> RedirectResponse | StreamingResponse:
    lead = await _get_lead_or_404(session, lead_id)
    url = await storage.presigned_url(lead.resume_key, expires_in=settings.resume_url_ttl_seconds)
    if url is not None:
        return RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    try:
        body = storage.stream(lead.resume_key)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Resume file not found") from exc
    safe_name = lead.resume_name.replace('"', "")
    return StreamingResponse(
        body,
        media_type=lead.resume_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )
