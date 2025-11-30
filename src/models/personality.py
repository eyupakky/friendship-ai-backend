"""
Kişilik Analizi Modelleri - Big Five (OCEAN) Modeli

Big Five kişilik özellikleri:
- Openness (Deneyime Açıklık): Yaratıcılık, merak, yeni fikirlere açıklık
- Conscientiousness (Sorumluluk): Düzen, disiplin, hedefe yönelik davranış
- Extraversion (Dışadönüklük): Sosyallik, enerji, olumlu duygular
- Agreeableness (Uyumluluk): İşbirliği, güven, yardımseverlik
- Neuroticism (Nevrotiklik): Duygusal dengesizlik, kaygı, stres
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class PersonalityTrait(str, Enum):
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class PersonalityScore(BaseModel):
    """Tek bir kişilik özelliği için skor"""
    trait: PersonalityTrait
    score: float = Field(ge=0.0, le=1.0, description="0-1 arası normalize edilmiş skor")
    confidence: float = Field(ge=0.0, le=1.0, description="Analiz güven seviyesi")
    evidence_count: int = Field(default=0, description="Bu özellik için toplanan kanıt sayısı")


class PersonalityProfile(BaseModel):
    """Kullanıcının tam kişilik profili"""
    user_id: str
    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    conscientiousness: float = Field(default=0.5, ge=0.0, le=1.0)
    extraversion: float = Field(default=0.5, ge=0.0, le=1.0)
    agreeableness: float = Field(default=0.5, ge=0.0, le=1.0)
    neuroticism: float = Field(default=0.5, ge=0.0, le=1.0)

    # Ek özellikler
    humor_style: Optional[str] = None  # "witty", "sarcastic", "wholesome", "dark"
    communication_style: Optional[str] = None  # "direct", "diplomatic", "expressive", "reserved"
    interests: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)

    # Meta bilgiler
    analysis_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    total_messages_analyzed: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_complete: bool = Field(default=False)

    def to_vector(self) -> List[float]:
        """Kişilik profilini eşleştirme için vektöre dönüştür"""
        return [
            self.openness,
            self.conscientiousness,
            self.extraversion,
            self.agreeableness,
            1.0 - self.neuroticism,  # Düşük nevrotiklik daha iyi eşleşme için
        ]

    def get_dominant_traits(self, threshold: float = 0.7) -> List[PersonalityTrait]:
        """Baskın kişilik özelliklerini döndür"""
        traits = []
        if self.openness >= threshold:
            traits.append(PersonalityTrait.OPENNESS)
        if self.conscientiousness >= threshold:
            traits.append(PersonalityTrait.CONSCIENTIOUSNESS)
        if self.extraversion >= threshold:
            traits.append(PersonalityTrait.EXTRAVERSION)
        if self.agreeableness >= threshold:
            traits.append(PersonalityTrait.AGREEABLENESS)
        if self.neuroticism >= threshold:
            traits.append(PersonalityTrait.NEUROTICISM)
        return traits


class ConversationMessage(BaseModel):
    """Konuşma mesajı"""
    id: str
    user_id: str
    content: str
    is_from_ai: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sentiment_score: Optional[float] = None
    detected_traits: Optional[Dict[str, float]] = None


class ConversationSession(BaseModel):
    """Bir konuşma oturumu"""
    session_id: str
    user_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    current_topic: Optional[str] = None
    topics_covered: List[str] = Field(default_factory=list)
    analysis_phase: int = Field(default=1, ge=1, le=5)  # 1-5 arası analiz aşaması
    is_analysis_complete: bool = Field(default=False)


class MatchScore(BaseModel):
    """İki kullanıcı arasındaki eşleşme skoru"""
    user_id_1: str
    user_id_2: str
    overall_score: float = Field(ge=0.0, le=1.0)
    trait_compatibility: Dict[str, float] = Field(default_factory=dict)
    interest_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    communication_compatibility: float = Field(default=0.0, ge=0.0, le=1.0)
    predicted_friendship_type: str = ""  # "deep", "casual", "activity_based", "intellectual"
    match_reasons: List[str] = Field(default_factory=list)
    potential_challenges: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
