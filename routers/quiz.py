from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_database_session
from models import UserAccount
from security import get_authenticated_user, get_optional_authenticated_user
from schemas import (
    GenerateQuizRequest,
    QuizQuestionItemResponse,
    SubmitQuizAttemptRequest,
    QuizAttemptResultResponse,
    QuizHistoryResponse
)
from services.quiz_service import QuizEngineService

router = APIRouter(prefix="/api/quiz", tags=["Quiz Engine"])

@router.post("/generate", response_model=List[QuizQuestionItemResponse])
async def generate_quiz_for_document(
    request_payload: GenerateQuizRequest,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        created_questions = await QuizEngineService.generate_quiz_questions(
            document_id=request_payload.document_id,
            number_of_questions=request_payload.number_of_questions,
            difficulty=request_payload.difficulty or "medium",
            database_session=database_session
        )
        return created_questions
    except ValueError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(validation_error)
        )
    except Exception as general_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(general_error)}"
        )

@router.get("/questions/{document_id}", response_model=List[QuizQuestionItemResponse])
async def get_questions_for_document(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    questions = await QuizEngineService.get_document_questions(
        document_id=document_id,
        database_session=database_session
    )
    return questions

@router.post("/submit", response_model=QuizAttemptResultResponse)
async def submit_quiz_attempt(
    request_payload: SubmitQuizAttemptRequest,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    try:
        formatted_answers = [
            {"question_id": a.question_id, "selected_option": a.selected_option}
            for a in request_payload.answers
        ]
        attempt_result = await QuizEngineService.submit_quiz_attempt(
            user_id=authenticated_user.id,
            document_id=request_payload.document_id,
            submitted_answers=formatted_answers,
            database_session=database_session
        )
        return attempt_result
    except Exception as submission_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz evaluation failed: {str(submission_error)}"
        )

@router.get("/history/{document_id}", response_model=QuizHistoryResponse)
async def get_user_quiz_history(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    history_data = await QuizEngineService.get_quiz_history(
        user_id=authenticated_user.id,
        document_id=document_id,
        database_session=database_session
    )
    return history_data

@router.get("/spaced-review/{document_id}", response_model=List[QuizQuestionItemResponse])
async def get_spaced_repetition_review(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    review_questions = await QuizEngineService.get_spaced_repetition_review(
        user_id=authenticated_user.id,
        document_id=document_id,
        database_session=database_session
    )
    return review_questions
