import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.exercises.schemas import (
    CreateExerciseRequest,
    ExerciseListParams,
    ExerciseLogEntry,
    ExerciseLogParameterValue,
    ExerciseResponse,
    GymFacilityInput,
    GymFacilityListParams,
    GymFacilityResponse,
    GymMaterialInput,
    GymMaterialListParams,
    GymMaterialResponse,
    MediaUploadRequest,
    MediaUploadResponse,
    ParameterInput,
    ParameterResponse,
    RelatedExerciseInput,
    RelatedExerciseResponse,
    UpdateExerciseRequest,
)
from app.models import (
    Exercise,
    ExerciseGymFacility,
    ExerciseGymMaterial,
    ExerciseParameter,
    ExerciseRelation,
    GymFacility,
    GymMaterial,
    SessionLog,
    SessionLogAction,
    SessionLogEntry,
    SessionLogParameterValue,
    User,
)
from app.pagination import Page, PaginationParams
from app.storage import MEDIA_CONSTRAINTS, create_presigned_upload, public_url

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Gym materials are managed inline through the exercise form, but get their own
# read endpoint for the autocomplete suggestions.
gym_materials_router = APIRouter(prefix="/gym-materials", tags=["gym-materials"])


@gym_materials_router.get("", response_model=Page[GymMaterialResponse])
async def list_gym_materials(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[GymMaterialListParams, Query()],
) -> Page[GymMaterialResponse]:
    """Gym materials, filterable by name — for the exercise form's autocomplete."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(GymMaterial.name.ilike(f"%{params.search.strip()}%"))
    total = await session.scalar(select(func.count()).select_from(GymMaterial).where(*filters))
    rows = await session.scalars(
        select(GymMaterial)
        .where(*filters)
        .order_by(GymMaterial.name)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[GymMaterialResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


# Gym facilities are managed inline through the exercise form, but get their own
# read endpoint for the autocomplete suggestions.
gym_facilities_router = APIRouter(prefix="/gym-facilities", tags=["gym-facilities"])


@gym_facilities_router.get("", response_model=Page[GymFacilityResponse])
async def list_gym_facilities(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[GymFacilityListParams, Query()],
) -> Page[GymFacilityResponse]:
    """Gym facilities, filterable by name — for the exercise form's autocomplete."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(GymFacility.name.ilike(f"%{params.search.strip()}%"))
    total = await session.scalar(select(func.count()).select_from(GymFacility).where(*filters))
    rows = await session.scalars(
        select(GymFacility)
        .where(*filters)
        .order_by(GymFacility.name)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[GymFacilityResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


def _serialize(exercise: Exercise) -> ExerciseResponse:
    """Build the response, flattening each relation to {id, name, note}. Requires
    `related` and each relation's `related_exercise` to be loaded."""
    return ExerciseResponse(
        id=exercise.id,
        name=exercise.name,
        description=exercise.description,
        type=exercise.type,
        created_at=exercise.created_at,
        thumbnail_key=exercise.thumbnail_key,
        video_key=exercise.video_key,
        related_exercises=[
            RelatedExerciseResponse(
                related_exercise_id=relation.related_exercise_id,
                related_exercise_name=relation.related_exercise.name,
                related_exercise_thumbnail_url=public_url(relation.related_exercise.thumbnail_key),
                note=relation.note,
            )
            for relation in exercise.related
        ],
        parameters=[ParameterResponse.model_validate(param) for param in exercise.parameters],
        gym_materials=[
            GymMaterialResponse.model_validate(link.gym_material) for link in exercise.gym_materials
        ],
        gym_facilities=[
            GymFacilityResponse.model_validate(link.gym_facility)
            for link in exercise.gym_facilities
        ],
    )


async def _load_exercise(session: AsyncSession, exercise_id: uuid.UUID) -> Exercise | None:
    """Fetch an exercise with its relations (and each relation's target), parameters,
    and gym-material/facility links (with each material/facility) loaded."""
    exercise: Exercise | None = await session.scalar(
        select(Exercise)
        .where(Exercise.id == exercise_id)
        .options(
            selectinload(Exercise.related).selectinload(ExerciseRelation.related_exercise),
            selectinload(Exercise.parameters),
            selectinload(Exercise.gym_materials).selectinload(ExerciseGymMaterial.gym_material),
            selectinload(Exercise.gym_facilities).selectinload(ExerciseGymFacility.gym_facility),
        )
    )
    return exercise


async def _build_relations(
    session: AsyncSession,
    owner_id: uuid.UUID,
    related: list[RelatedExerciseInput],
) -> list[ExerciseRelation]:
    """Validate the related-exercise inputs and build ExerciseRelation rows. Rejects
    self-references, duplicates, and unknown targets."""
    relations: list[ExerciseRelation] = []
    seen: set[uuid.UUID] = set()
    for position, item in enumerate(related):
        target_id = item.related_exercise_id
        if target_id == owner_id:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_related_exercise,
                "An exercise cannot be related to itself",
            )
        if target_id in seen:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_related_exercise,
                "Duplicate related exercise",
            )
        if await session.get(Exercise, target_id) is None:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_related_exercise,
                "Related exercise not found",
            )
        seen.add(target_id)
        note = item.note.strip() if item.note else None
        relations.append(
            ExerciseRelation(related_exercise_id=target_id, note=note or None, position=position)
        )
    return relations


def _build_parameters(parameters: list[ParameterInput]) -> list[ExerciseParameter]:
    """Validate the parameter inputs and build ExerciseParameter rows. Rejects
    blank and duplicate (case-insensitive) names within the exercise."""
    rows: list[ExerciseParameter] = []
    seen: set[str] = set()
    for item in parameters:
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_parameter,
                "Parameter name is required",
            )
        if name.casefold() in seen:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_parameter,
                "Duplicate parameter name",
            )
        seen.add(name.casefold())
        description = item.description.strip() if item.description else None
        rows.append(ExerciseParameter(name=name, description=description or None))
    return rows


async def _build_gym_materials(
    session: AsyncSession, materials: list[GymMaterialInput]
) -> list[ExerciseGymMaterial]:
    """Build the exercise→material links, finding each material by name
    (case-insensitive) or creating it. Rejects blank and duplicate names within the
    same exercise. Materials are shared, so the same name across exercises reuses one row."""
    links: list[ExerciseGymMaterial] = []
    seen: set[str] = set()
    for position, item in enumerate(materials):
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_gym_material,
                "Material name is required",
            )
        if name.casefold() in seen:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_gym_material,
                "Duplicate material",
            )
        seen.add(name.casefold())
        # Find an existing material by case-insensitive name, else create it.
        material = await session.scalar(
            select(GymMaterial).where(func.lower(GymMaterial.name) == name.lower())
        )
        if material is None:
            material = GymMaterial(name=name)
            session.add(material)
            await session.flush()  # assign its id before linking
        links.append(ExerciseGymMaterial(gym_material_id=material.id, position=position))
    return links


async def _build_gym_facilities(
    session: AsyncSession, facilities: list[GymFacilityInput]
) -> list[ExerciseGymFacility]:
    """Build the exercise→facility links, finding each facility by name
    (case-insensitive) or creating it. Rejects blank and duplicate names within the
    same exercise. Facilities are shared, so the same name across exercises reuses one row."""
    links: list[ExerciseGymFacility] = []
    seen: set[str] = set()
    for position, item in enumerate(facilities):
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_gym_facility,
                "Facility name is required",
            )
        if name.casefold() in seen:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_gym_facility,
                "Duplicate facility",
            )
        seen.add(name.casefold())
        # Find an existing facility by case-insensitive name, else create it.
        facility = await session.scalar(
            select(GymFacility).where(func.lower(GymFacility.name) == name.lower())
        )
        if facility is None:
            facility = GymFacility(name=name)
            session.add(facility)
            await session.flush()  # assign its id before linking
        links.append(ExerciseGymFacility(gym_facility_id=facility.id, position=position))
    return links


@router.post("/media-uploads", response_model=MediaUploadResponse)
async def create_media_upload(
    body: MediaUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> MediaUploadResponse:
    """Mint a presigned POST so the admin's browser can upload a thumbnail or
    video straight to S3. Returns the object key to store on save."""
    allowed_types, _max_size = MEDIA_CONSTRAINTS[body.kind]
    if body.content_type not in allowed_types:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_media_type,
            f"Unsupported content type for {body.kind.value}",
        )
    upload = create_presigned_upload(body.kind, body.content_type)
    return MediaUploadResponse(key=upload.key, url=upload.url, fields=upload.fields)


@router.get("")
async def list_exercises(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[ExerciseListParams, Query()],
) -> Page[ExerciseResponse]:
    """All exercises, filterable by name search and type. Visible to any user."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(Exercise.name.ilike(f"%{params.search.strip()}%"))
    if params.type is not None:
        filters.append(Exercise.type == params.type)

    total = await session.scalar(select(func.count()).select_from(Exercise).where(*filters))
    rows = await session.scalars(
        select(Exercise)
        .where(*filters)
        .options(
            selectinload(Exercise.related).selectinload(ExerciseRelation.related_exercise),
            selectinload(Exercise.parameters),
            selectinload(Exercise.gym_materials).selectinload(ExerciseGymMaterial.gym_material),
            selectinload(Exercise.gym_facilities).selectinload(ExerciseGymFacility.gym_facility),
        )
        .order_by(Exercise.name)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[_serialize(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseResponse:
    """A single exercise by id. Visible to any authenticated user."""
    exercise = await _load_exercise(session, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )
    return _serialize(exercise)


@router.get("/{exercise_id}/logs", response_model=Page[ExerciseLogEntry])
async def list_exercise_logs(
    exercise_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[ExerciseLogEntry]:
    """The current athlete's past occurrences of doing this exercise, most recent
    first — when, in which training, and the parameter values recorded each time.
    A reference for what they used last time."""
    base = (
        select(SessionLogEntry.id)
        .join(SessionLog, SessionLogEntry.log_id == SessionLog.id)
        .where(
            SessionLogEntry.performed_exercise_id == exercise_id,
            SessionLogEntry.action == SessionLogAction.done,
            SessionLog.athlete_id == user.id,
        )
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    entries = list(
        await session.scalars(
            select(SessionLogEntry)
            .join(SessionLog, SessionLogEntry.log_id == SessionLog.id)
            .where(
                SessionLogEntry.performed_exercise_id == exercise_id,
                SessionLogEntry.action == SessionLogAction.done,
                SessionLog.athlete_id == user.id,
            )
            .order_by(SessionLog.performed_at.desc())
            .offset(params.offset)
            .limit(params.page_size)
            .options(
                selectinload(SessionLogEntry.log).selectinload(SessionLog.training_session),
                selectinload(SessionLogEntry.planned_exercise),
                selectinload(SessionLogEntry.parameter_values).selectinload(
                    SessionLogParameterValue.parameter
                ),
            )
        )
    )

    items = []
    for entry in entries:
        training = entry.log.training_session
        # The exercise stood in as an alternative when it isn't the planned one.
        as_alternative_for = (
            entry.planned_exercise.name if entry.planned_exercise_id != exercise_id else None
        )
        items.append(
            ExerciseLogEntry(
                log_id=entry.log_id,
                training_id=entry.log.training_session_id,
                training_title=training.title if training else None,
                performed_at=entry.log.performed_at,
                as_alternative_for=as_alternative_for,
                parameter_values=[
                    ExerciseLogParameterValue(name=value.parameter.name, value=value.value)
                    for value in entry.parameter_values
                ],
            )
        )
    return Page(items=items, total_count=total or 0)


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: CreateExerciseRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseResponse:
    name = body.name.strip()

    existing = await session.scalar(select(Exercise).where(Exercise.name == name))
    if existing is not None:
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.exercise_already_exists,
            "An exercise with this name already exists",
        )

    description = body.description.strip() if body.description else None
    exercise = Exercise(
        name=name,
        description=description or None,
        type=body.type,
        thumbnail_key=body.thumbnail_key,
        video_key=body.video_key,
    )
    exercise.related = await _build_relations(session, exercise.id, body.related_exercises)
    exercise.parameters = _build_parameters(body.parameters)
    exercise.gym_materials = await _build_gym_materials(session, body.gym_materials)
    exercise.gym_facilities = await _build_gym_facilities(session, body.gym_facilities)
    session.add(exercise)
    await session.commit()

    reloaded = await _load_exercise(session, exercise.id)
    assert reloaded is not None
    return _serialize(reloaded)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: uuid.UUID,
    body: UpdateExerciseRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseResponse:
    exercise = await _load_exercise(session, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )

    name = body.name.strip()
    clash = await session.scalar(
        select(Exercise).where(Exercise.name == name, Exercise.id != exercise_id)
    )
    if clash is not None:
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.exercise_already_exists,
            "An exercise with this name already exists",
        )

    description = body.description.strip() if body.description else None
    exercise.name = name
    exercise.description = description or None
    exercise.type = body.type
    # The request carries the desired final keys (kept, replaced, or cleared).
    exercise.thumbnail_key = body.thumbnail_key
    exercise.video_key = body.video_key
    # Replace the related list wholesale. Validate the new set first, then flush the
    # removal of the old rows before inserting — otherwise re-adding the same target
    # races the orphan delete and trips the (exercise_id, related_exercise_id) unique
    # constraint.
    new_relations = await _build_relations(session, exercise.id, body.related_exercises)
    new_parameters = _build_parameters(body.parameters)
    exercise.related.clear()
    exercise.parameters.clear()
    exercise.gym_materials.clear()
    exercise.gym_facilities.clear()
    # Flush the removals before inserting, so re-using a name/target doesn't race the
    # orphan delete and trip a unique constraint. Build the material/facility links
    # after this flush too, so re-linking the same one doesn't race its orphan delete.
    await session.flush()
    exercise.related = new_relations
    exercise.parameters = new_parameters
    exercise.gym_materials = await _build_gym_materials(session, body.gym_materials)
    exercise.gym_facilities = await _build_gym_facilities(session, body.gym_facilities)
    await session.commit()

    reloaded = await _load_exercise(session, exercise_id)
    assert reloaded is not None
    return _serialize(reloaded)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    exercise = await session.get(Exercise, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )
    await session.delete(exercise)
    await session.commit()
