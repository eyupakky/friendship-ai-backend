"""
API Route'ları

Tüm API endpoint'lerini içerir.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

from ..models.personality import PersonalityProfile, MatchScore, ConversationSession
from ..services.conversation_ai import ConversationAI
from ..services.matching_engine import MatchingEngine
from ..config.settings import settings


# Router'ı oluştur
router = APIRouter()

# Servis instance'ları (gerçek uygulamada dependency injection kullanılmalı)
conversation_ai: Optional[ConversationAI] = None
matching_engine: Optional[MatchingEngine] = None


def get_conversation_ai() -> ConversationAI:
    global conversation_ai
    if conversation_ai is None:
        conversation_ai = ConversationAI(
            ollama_url=settings.OLLAMA_URL,
            model=settings.OLLAMA_MODEL
        )
    return conversation_ai


def get_matching_engine() -> MatchingEngine:
    global matching_engine
    if matching_engine is None:
        matching_engine = MatchingEngine()
    return matching_engine


# Request/Response modelleri
class StartSessionRequest(BaseModel):
    user_id: str


class StartSessionResponse(BaseModel):
    session_id: str
    welcome_message: str


class SendMessageRequest(BaseModel):
    user_id: str
    message: str


class SendMessageResponse(BaseModel):
    ai_response: str
    analysis_phase: int
    total_messages: int
    is_analysis_complete: bool
    confidence: float


class ProfileResponse(BaseModel):
    user_id: str
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    interests: List[str]
    communication_style: Optional[str]
    is_complete: bool
    confidence: float


class MatchResponse(BaseModel):
    user_id: str
    overall_score: float
    friendship_type: str
    reasons: List[str]
    challenges: List[str]


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int


# Health Check
@router.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# Konuşma Endpoint'leri
@router.post("/conversation/start", response_model=StartSessionResponse)
async def start_conversation(
    request: StartSessionRequest,
    ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Yeni bir konuşma oturumu başlat.

    Kullanıcı AI ile konuşmaya başlar ve kişilik analizi süreci başlar.
    """
    try:
        session = await ai.start_session(request.user_id)

        # İlk mesajı oluştur
        welcome_message = (
            "Merhaba! Ben senin arkadaşlık asistanınım. "
            "Seni tanımak ve en uygun arkadaşları bulmana yardımcı olmak için buradayım. "
            "Biraz sohbet edelim mi? Bana kendinden bahseder misin?"
        )

        return StartSessionResponse(
            session_id=session.session_id,
            welcome_message=welcome_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oturum başlatılamadı: {str(e)}"
        )


@router.post("/conversation/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    AI'a mesaj gönder ve cevap al.

    Her mesaj kişilik analizi için işlenir.
    """
    try:
        ai_response, session, profile = await ai.process_message(
            request.user_id,
            request.message
        )

        user_message_count = len([m for m in session.messages if not m.is_from_ai])

        return SendMessageResponse(
            ai_response=ai_response,
            analysis_phase=session.analysis_phase,
            total_messages=user_message_count,
            is_analysis_complete=session.is_analysis_complete,
            confidence=round(profile.analysis_confidence, 2)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mesaj işlenemedi: {str(e)}"
        )


@router.get("/conversation/summary/{user_id}")
async def get_conversation_summary(
    user_id: str,
    ai: ConversationAI = Depends(get_conversation_ai)
):
    """Konuşma özetini getir"""
    summary = await ai.get_session_summary(user_id)
    if "error" in summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=summary["error"]
        )
    return summary


@router.post("/conversation/end/{user_id}")
async def end_conversation(
    user_id: str,
    ai: ConversationAI = Depends(get_conversation_ai),
    engine: MatchingEngine = Depends(get_matching_engine)
):
    """
    Konuşmayı sonlandır ve profili eşleştirme havuzuna ekle.
    """
    profile = await ai.end_session(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aktif oturum bulunamadı"
        )

    # Profili eşleştirme motoruna ekle
    if profile.is_complete:
        engine.add_profile(profile)

    return {
        "message": "Konuşma sonlandırıldı",
        "profile_complete": profile.is_complete,
        "can_match": profile.is_complete and profile.analysis_confidence >= settings.MIN_CONFIDENCE_FOR_MATCHING
    }


# Profil Endpoint'leri
@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    ai: ConversationAI = Depends(get_conversation_ai)
):
    """Kullanıcının kişilik profilini getir"""
    profile = ai.get_profile(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil bulunamadı"
        )

    return ProfileResponse(
        user_id=profile.user_id,
        openness=round(profile.openness, 2),
        conscientiousness=round(profile.conscientiousness, 2),
        extraversion=round(profile.extraversion, 2),
        agreeableness=round(profile.agreeableness, 2),
        neuroticism=round(profile.neuroticism, 2),
        interests=profile.interests,
        communication_style=profile.communication_style,
        is_complete=profile.is_complete,
        confidence=round(profile.analysis_confidence, 2)
    )


@router.get("/profile/{user_id}/traits")
async def get_profile_traits(
    user_id: str,
    ai: ConversationAI = Depends(get_conversation_ai)
):
    """Kullanıcının kişilik özelliklerini detaylı getir"""
    profile = ai.get_profile(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil bulunamadı"
        )

    # Özellikleri açıklamalarıyla birlikte döndür
    traits = {
        "openness": {
            "score": round(profile.openness, 2),
            "label": "Deneyime Açıklık",
            "description": _get_trait_description("openness", profile.openness)
        },
        "conscientiousness": {
            "score": round(profile.conscientiousness, 2),
            "label": "Sorumluluk",
            "description": _get_trait_description("conscientiousness", profile.conscientiousness)
        },
        "extraversion": {
            "score": round(profile.extraversion, 2),
            "label": "Dışadönüklük",
            "description": _get_trait_description("extraversion", profile.extraversion)
        },
        "agreeableness": {
            "score": round(profile.agreeableness, 2),
            "label": "Uyumluluk",
            "description": _get_trait_description("agreeableness", profile.agreeableness)
        },
        "neuroticism": {
            "score": round(profile.neuroticism, 2),
            "label": "Duygusal Hassasiyet",
            "description": _get_trait_description("neuroticism", profile.neuroticism)
        }
    }

    return {
        "user_id": user_id,
        "traits": traits,
        "dominant_traits": [t.value for t in profile.get_dominant_traits()],
        "analysis_confidence": round(profile.analysis_confidence, 2)
    }


def _get_trait_description(trait: str, score: float) -> str:
    """Kişilik özelliği için açıklama oluştur"""
    descriptions = {
        "openness": {
            "high": "Yaratıcı, meraklı ve yeni deneyimlere çok açıksın.",
            "medium": "Yeni fikirlere açık ama geleneksel değerleri de önemsiyorsun.",
            "low": "Pratik düşünmeyi ve kanıtlanmış yöntemleri tercih ediyorsun."
        },
        "conscientiousness": {
            "high": "Çok organize, disiplinli ve hedef odaklısın.",
            "medium": "Dengeli bir yaklaşımın var - hem planlı hem esnek olabiliyorsun.",
            "low": "Spontan ve esnek bir yapın var, katı planlara bağlı kalmıyorsun."
        },
        "extraversion": {
            "high": "Sosyal, enerjik ve insanlarla olmayı seviyorsun.",
            "medium": "Hem sosyal hem de kendi başına zaman geçirmekten keyif alıyorsun.",
            "low": "Daha sakin ortamları ve derin bire bir ilişkileri tercih ediyorsun."
        },
        "agreeableness": {
            "high": "Çok anlayışlı, yardımsever ve empatiksin.",
            "medium": "Dengeli bir yaklaşımın var - hem işbirlikçi hem de kendi fikirlerinde kararlısın.",
            "low": "Analitik ve eleştirel düşünüyorsun, bağımsız kararlar veriyorsun."
        },
        "neuroticism": {
            "high": "Duygusal olarak hassassın ve derin hissediyorsun.",
            "medium": "Duygularını dengeli bir şekilde yönetebiliyorsun.",
            "low": "Duygusal olarak çok kararlı ve sakinsin."
        }
    }

    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return descriptions.get(trait, {}).get(level, "")


# Eşleştirme Endpoint'leri
@router.get("/matches/{user_id}", response_model=MatchListResponse)
async def get_matches(
    user_id: str,
    limit: int = 10,
    min_score: float = 0.5,
    ai: ConversationAI = Depends(get_conversation_ai),
    engine: MatchingEngine = Depends(get_matching_engine)
):
    """
    Kullanıcı için en uygun eşleşmeleri getir.

    Args:
        user_id: Eşleşme aranan kullanıcı
        limit: Maksimum eşleşme sayısı
        min_score: Minimum uyumluluk skoru (0-1)
    """
    # Kullanıcının profili var mı kontrol et
    profile = ai.get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil bulunamadı. Önce AI ile konuşma yapmalısınız."
        )

    if not profile.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profiliniz henüz tamamlanmadı. Lütfen AI ile konuşmaya devam edin."
        )

    # Profili eşleştirme motoruna ekle (eğer yoksa)
    engine.add_profile(profile)

    # Eşleşmeleri bul
    matches = engine.find_best_matches(
        user_id,
        limit=min(limit, settings.MAX_MATCHES_PER_USER),
        min_score=min_score
    )

    match_responses = []
    for match in matches:
        other_user_id = match.user_id_2 if match.user_id_1 == user_id else match.user_id_1
        match_responses.append(MatchResponse(
            user_id=other_user_id,
            overall_score=match.overall_score,
            friendship_type=match.predicted_friendship_type,
            reasons=match.match_reasons,
            challenges=match.potential_challenges
        ))

    return MatchListResponse(
        matches=match_responses,
        total=len(match_responses)
    )


@router.get("/matches/{user_id}/{other_user_id}")
async def get_match_details(
    user_id: str,
    other_user_id: str,
    ai: ConversationAI = Depends(get_conversation_ai),
    engine: MatchingEngine = Depends(get_matching_engine)
):
    """İki kullanıcı arasındaki eşleşme detaylarını getir"""
    profile1 = ai.get_profile(user_id)
    profile2 = ai.get_profile(other_user_id)

    if profile1 is None or profile2 is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bir veya her iki profil bulunamadı"
        )

    match = engine.calculate_match_score(profile1, profile2)
    explanation = engine.get_compatibility_explanation(match)

    return {
        "match": {
            "overall_score": match.overall_score,
            "trait_compatibility": match.trait_compatibility,
            "interest_overlap": match.interest_overlap,
            "communication_compatibility": match.communication_compatibility,
            "friendship_type": match.predicted_friendship_type,
            "reasons": match.match_reasons,
            "challenges": match.potential_challenges
        },
        "explanation": explanation
    }


# Admin Endpoint'leri (gerçek uygulamada auth gerekli)
@router.get("/admin/stats")
async def get_stats(
    ai: ConversationAI = Depends(get_conversation_ai),
    engine: MatchingEngine = Depends(get_matching_engine)
):
    """Sistem istatistiklerini getir"""
    return {
        "active_sessions": len(ai.active_sessions),
        "total_profiles": len(ai.user_profiles),
        "complete_profiles": sum(
            1 for p in ai.user_profiles.values() if p.is_complete
        ),
        "matchable_profiles": len(engine.user_profiles)
    }
