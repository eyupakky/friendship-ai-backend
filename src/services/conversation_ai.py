"""
Konuşma AI Servisi

Kullanıcılarla doğal konuşma yapan ve kişilik analizi için veri toplayan AI.
"""

import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from openai import AsyncOpenAI

from ..models.personality import (
    PersonalityProfile,
    ConversationMessage,
    ConversationSession,
)
from .personality_analyzer import PersonalityAnalyzer


class ConversationAI:
    """Kullanıcılarla konuşma yapan AI"""

    SYSTEM_PROMPT = """Sen samimi, meraklı ve empatik bir arkadaşsın. Amacın kullanıcıyı tanımak ve onunla doğal bir sohbet yapmak.

Kurallar:
1. Samimi ve sıcak ol ama yapay veya aşırı hevesli olma
2. Kullanıcının cevaplarına gerçekten ilgi göster ve takip soruları sor
3. Kendi hakkında da biraz bilgi paylaş ki konuşma tek taraflı olmasın
4. Hassas konularda dikkatli ol
5. Kullanıcıyı yargılama
6. Kısa ve öz cevaplar ver, uzun paragraflar yazma
7. Türkçe konuş

Amacın kullanıcının:
- İlgi alanlarını
- Sosyal tercihlerini
- Değerlerini
- İletişim stilini
- Duygusal tepkilerini
anlamak. Ama bunu doğrudan sorma, doğal konuşma içinde öğren.

Şu anki analiz aşaması: {phase}/5
Kalan minimum mesaj sayısı: {remaining_messages}
"""

    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.analyzer = PersonalityAnalyzer(openai_api_key)
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.user_profiles: Dict[str, PersonalityProfile] = {}

    async def start_session(self, user_id: str) -> ConversationSession:
        """Yeni bir konuşma oturumu başlat"""
        session = ConversationSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            started_at=datetime.utcnow(),
            analysis_phase=1
        )

        # Kullanıcının profili yoksa oluştur
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = PersonalityProfile(user_id=user_id)

        self.active_sessions[user_id] = session
        return session

    async def process_message(
        self,
        user_id: str,
        user_message: str
    ) -> Tuple[str, ConversationSession, PersonalityProfile]:
        """
        Kullanıcı mesajını işle ve cevap üret.

        Returns:
            Tuple[str, ConversationSession, PersonalityProfile]:
                - AI'ın cevabı
                - Güncel oturum bilgisi
                - Güncel kişilik profili
        """
        # Oturum yoksa başlat
        if user_id not in self.active_sessions:
            await self.start_session(user_id)

        session = self.active_sessions[user_id]
        profile = self.user_profiles[user_id]

        # Kullanıcı mesajını kaydet
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=user_message,
            is_from_ai=False,
            timestamp=datetime.utcnow()
        )
        session.messages.append(user_msg)

        # Kişilik analizi yap
        trait_scores = await self.analyzer.analyze_message(
            user_message,
            user_id,
            session.messages
        )
        user_msg.detected_traits = trait_scores

        # Profili güncelle
        message_count = len([m for m in session.messages if not m.is_from_ai])
        profile = await self.analyzer.update_personality_profile(
            profile,
            trait_scores,
            message_count
        )
        self.user_profiles[user_id] = profile

        # Analiz aşamasını güncelle
        session.analysis_phase = self._calculate_phase(message_count)

        # AI cevabı üret
        ai_response = await self._generate_response(session, profile)

        # AI mesajını kaydet
        ai_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=ai_response,
            is_from_ai=True,
            timestamp=datetime.utcnow()
        )
        session.messages.append(ai_msg)

        # Analiz tamamlandı mı kontrol et
        if message_count >= 30 and profile.analysis_confidence >= 0.6:
            session.is_analysis_complete = True
            # İlgi alanlarını tespit et
            profile.interests = await self.analyzer.detect_interests(session.messages)
            # İletişim stilini tespit et
            profile.communication_style = await self.analyzer.detect_communication_style(session.messages)
            profile.is_complete = True

        return ai_response, session, profile

    def _calculate_phase(self, message_count: int) -> int:
        """Mesaj sayısına göre analiz aşamasını hesapla"""
        if message_count < 6:
            return 1  # Tanışma
        elif message_count < 12:
            return 2  # Sosyal yaşam
        elif message_count < 18:
            return 3  # Değerler
        elif message_count < 24:
            return 4  # Duygusal derinlik
        else:
            return 5  # Gelecek ve hedefler

    async def _generate_response(
        self,
        session: ConversationSession,
        profile: PersonalityProfile
    ) -> str:
        """AI cevabı üret"""

        # Konuşma geçmişini hazırla
        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT.format(
                    phase=session.analysis_phase,
                    remaining_messages=max(0, 30 - len([m for m in session.messages if not m.is_from_ai]))
                )
            }
        ]

        # Son 20 mesajı ekle
        for msg in session.messages[-20:]:
            role = "assistant" if msg.is_from_ai else "user"
            messages.append({"role": role, "content": msg.content})

        # Analiz tamamlanmak üzereyse özel mesaj ekle
        user_message_count = len([m for m in session.messages if not m.is_from_ai])
        if user_message_count >= 28 and not session.is_analysis_complete:
            messages.append({
                "role": "system",
                "content": "Konuşma bitiyor. Son birkaç mesajda kullanıcıya teşekkür et ve arkadaşlık eşleştirmesi için hazır olduğunu söyle."
            })

        # Eğer bu ilk mesajsa, özel başlangıç isteği ekle
        if len(session.messages) <= 1:
            messages.append({
                "role": "system",
                "content": "Bu konuşmanın başlangıcı. Kendini tanıt ve kullanıcıyla tanışmaya başla. Samimi ama profesyonel ol."
            })

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.8,
                max_tokens=300,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI cevap üretme hatası: {e}")
            # Fallback cevap
            return self.analyzer.get_next_question(
                session.analysis_phase,
                session.topics_covered
            )

    async def get_session_summary(self, user_id: str) -> Dict:
        """Oturum özetini getir"""
        if user_id not in self.active_sessions:
            return {"error": "Aktif oturum bulunamadı"}

        session = self.active_sessions[user_id]
        profile = self.user_profiles.get(user_id)

        user_messages = [m for m in session.messages if not m.is_from_ai]

        return {
            "session_id": session.session_id,
            "total_messages": len(session.messages),
            "user_messages": len(user_messages),
            "analysis_phase": session.analysis_phase,
            "is_complete": session.is_analysis_complete,
            "profile": {
                "openness": round(profile.openness, 2) if profile else None,
                "conscientiousness": round(profile.conscientiousness, 2) if profile else None,
                "extraversion": round(profile.extraversion, 2) if profile else None,
                "agreeableness": round(profile.agreeableness, 2) if profile else None,
                "neuroticism": round(profile.neuroticism, 2) if profile else None,
                "confidence": round(profile.analysis_confidence, 2) if profile else None,
                "interests": profile.interests if profile else [],
                "communication_style": profile.communication_style if profile else None,
            } if profile else None
        }

    async def end_session(self, user_id: str) -> Optional[PersonalityProfile]:
        """Oturumu sonlandır ve profili döndür"""
        if user_id not in self.active_sessions:
            return None

        session = self.active_sessions[user_id]
        session.ended_at = datetime.utcnow()

        profile = self.user_profiles.get(user_id)

        # İlgi alanlarını son kez güncelle
        if profile and not profile.interests:
            profile.interests = await self.analyzer.detect_interests(session.messages)
            profile.communication_style = await self.analyzer.detect_communication_style(session.messages)

        # Aktif oturumu kaldır
        del self.active_sessions[user_id]

        return profile

    def get_profile(self, user_id: str) -> Optional[PersonalityProfile]:
        """Kullanıcının kişilik profilini getir"""
        return self.user_profiles.get(user_id)

    def set_profile(self, user_id: str, profile: PersonalityProfile):
        """Kullanıcının kişilik profilini ayarla (veritabanından yüklerken)"""
        self.user_profiles[user_id] = profile
