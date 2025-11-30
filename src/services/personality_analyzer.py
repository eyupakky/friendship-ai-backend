"""
Kişilik Analizi Servisi

Bu servis, kullanıcı mesajlarını analiz ederek Big Five kişilik özelliklerini tespit eder.
OpenAI GPT API kullanarak doğal dil işleme yapar.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import openai
from openai import AsyncOpenAI

from ..models.personality import (
    PersonalityProfile,
    PersonalityTrait,
    ConversationMessage,
    PersonalityScore,
)


class PersonalityAnalyzer:
    """Kişilik analizi yapan AI servisi"""

    # Kişilik özelliklerini tespit etmek için anahtar kelimeler ve kalıplar
    TRAIT_INDICATORS = {
        PersonalityTrait.OPENNESS: {
            "positive": [
                "merak", "yaratıcı", "hayal", "sanat", "felsefe", "yeni", "farklı",
                "deneyim", "keşfet", "öğren", "ilginç", "sıradışı", "özgün",
                "curious", "creative", "imagine", "art", "philosophy", "new", "different"
            ],
            "negative": [
                "geleneksel", "alışık", "rutin", "normal", "standart", "klasik",
                "traditional", "routine", "normal", "standard"
            ]
        },
        PersonalityTrait.CONSCIENTIOUSNESS: {
            "positive": [
                "plan", "düzen", "hedef", "organize", "disiplin", "sorumluluk",
                "dikkatli", "detay", "başar", "çalış", "titiz", "program",
                "goal", "organized", "discipline", "responsible", "careful", "detail"
            ],
            "negative": [
                "erteledim", "unuttum", "dağınık", "rastgele", "spontan", "anında",
                "postpone", "forgot", "messy", "random", "spontaneous"
            ]
        },
        PersonalityTrait.EXTRAVERSION: {
            "positive": [
                "parti", "arkadaş", "sosyal", "eğlence", "enerji", "heyecan",
                "konuş", "tanış", "etkinlik", "grup", "insanlar", "canlı",
                "party", "friend", "social", "fun", "energy", "excitement"
            ],
            "negative": [
                "yalnız", "sessiz", "sakin", "evde", "kitap", "tek başına",
                "alone", "quiet", "calm", "home", "book", "solitude"
            ]
        },
        PersonalityTrait.AGREEABLENESS: {
            "positive": [
                "yardım", "anlayış", "empati", "işbirliği", "güven", "affet",
                "nazik", "kibar", "paylaş", "destekle", "saygı", "hoşgörü",
                "help", "understand", "empathy", "cooperation", "trust", "forgive"
            ],
            "negative": [
                "rekabet", "tartış", "karşı çık", "eleştir", "şüphe", "bencil",
                "compete", "argue", "oppose", "criticize", "doubt", "selfish"
            ]
        },
        PersonalityTrait.NEUROTICISM: {
            "positive": [
                "endişe", "stres", "kaygı", "kork", "gergin", "sinir", "üzgün",
                "depresif", "mutsuz", "tedirgin", "panik", "bunalım",
                "worry", "stress", "anxiety", "fear", "nervous", "angry", "sad"
            ],
            "negative": [
                "rahat", "sakin", "huzur", "mutlu", "güven", "stabil", "dengeli",
                "relaxed", "calm", "peaceful", "happy", "confident", "stable"
            ]
        }
    }

    # Analiz için kullanılacak sorular (aşamalara göre)
    ANALYSIS_QUESTIONS = {
        1: [  # Tanışma aşaması
            "Merhaba! Seninle tanışmak çok güzel. Bana biraz kendinden bahseder misin? Neler yapmaktan hoşlanırsın?",
            "Boş zamanlarında genellikle ne yaparsın?",
            "En sevdiğin aktivite ne?",
        ],
        2: [  # Sosyal yaşam
            "Arkadaşlarınla nasıl vakit geçirirsin?",
            "Yeni insanlarla tanışmak hakkında ne düşünüyorsun?",
            "Hafta sonları genellikle evde mi olursun yoksa dışarıda mı?",
        ],
        3: [  # Değerler ve görüşler
            "Hayatta en çok neye değer verirsin?",
            "Seni en çok ne motive eder?",
            "İdeal bir gün nasıl olurdu senin için?",
        ],
        4: [  # Duygusal derinlik
            "Zor zamanlarla nasıl başa çıkarsın?",
            "Seni en çok ne mutlu eder?",
            "Hayatta en çok korktuğun şey ne?",
        ],
        5: [  # Gelecek ve hedefler
            "Gelecekte kendini nerede görüyorsun?",
            "Hayalindeki arkadaşlık nasıl olurdu?",
            "Bir arkadaşta en çok aradığın özellik ne?",
        ]
    }

    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.analysis_cache: Dict[str, Dict] = {}

    async def analyze_message(
        self,
        message: str,
        user_id: str,
        conversation_history: List[ConversationMessage]
    ) -> Dict[str, float]:
        """
        Tek bir mesajı analiz et ve kişilik özelliklerini tespit et.

        Returns:
            Dict[str, float]: Her kişilik özelliği için 0-1 arası skor
        """
        # Önce keyword bazlı hızlı analiz
        keyword_scores = self._analyze_keywords(message)

        # Sonra LLM ile derin analiz
        llm_scores = await self._analyze_with_llm(message, conversation_history)

        # İki analizi birleştir (LLM'e daha fazla ağırlık ver)
        combined_scores = {}
        for trait in PersonalityTrait:
            keyword_score = keyword_scores.get(trait.value, 0.5)
            llm_score = llm_scores.get(trait.value, 0.5)
            # %30 keyword, %70 LLM
            combined_scores[trait.value] = (keyword_score * 0.3) + (llm_score * 0.7)

        return combined_scores

    def _analyze_keywords(self, message: str) -> Dict[str, float]:
        """Anahtar kelime bazlı hızlı analiz"""
        message_lower = message.lower()
        scores = {}

        for trait, indicators in self.TRAIT_INDICATORS.items():
            positive_count = sum(
                1 for word in indicators["positive"]
                if word in message_lower
            )
            negative_count = sum(
                1 for word in indicators["negative"]
                if word in message_lower
            )

            total = positive_count + negative_count
            if total > 0:
                # Normalize et: pozitif kelimeler skoru artırır
                score = (positive_count / total) * 0.5 + 0.25
                scores[trait.value] = min(max(score, 0.0), 1.0)
            else:
                scores[trait.value] = 0.5  # Nötr

        return scores

    async def _analyze_with_llm(
        self,
        message: str,
        conversation_history: List[ConversationMessage]
    ) -> Dict[str, float]:
        """LLM kullanarak derin kişilik analizi"""

        # Konuşma geçmişini formatla
        history_text = "\n".join([
            f"{'AI' if msg.is_from_ai else 'Kullanıcı'}: {msg.content}"
            for msg in conversation_history[-10:]  # Son 10 mesaj
        ])

        prompt = f"""Aşağıdaki konuşmayı analiz et ve kullanıcının Big Five (OCEAN) kişilik özelliklerini değerlendir.

Konuşma Geçmişi:
{history_text}

Son Mesaj: {message}

Her özellik için 0.0 ile 1.0 arasında bir skor ver:
- openness: Deneyime açıklık, yaratıcılık, merak (yüksek = çok açık/yaratıcı)
- conscientiousness: Sorumluluk, düzen, disiplin (yüksek = çok organize/disiplinli)
- extraversion: Dışadönüklük, sosyallik (yüksek = çok sosyal/enerjik)
- agreeableness: Uyumluluk, işbirliği, empati (yüksek = çok uyumlu/empatik)
- neuroticism: Nevrotiklik, duygusal dengesizlik (yüksek = çok endişeli/stresli)

Sadece JSON formatında cevap ver, başka bir şey yazma:
{{"openness": 0.X, "conscientiousness": 0.X, "extraversion": 0.X, "agreeableness": 0.X, "neuroticism": 0.X}}
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir kişilik analizi uzmanısın. Kullanıcıların mesajlarından kişilik özelliklerini analiz ediyorsun. Sadece JSON formatında cevap ver."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()
            # JSON'ı parse et
            scores = json.loads(result_text)

            # Skorları validate et
            validated_scores = {}
            for trait in PersonalityTrait:
                score = scores.get(trait.value, 0.5)
                validated_scores[trait.value] = min(max(float(score), 0.0), 1.0)

            return validated_scores

        except Exception as e:
            print(f"LLM analiz hatası: {e}")
            # Hata durumunda nötr skorlar döndür
            return {trait.value: 0.5 for trait in PersonalityTrait}

    async def update_personality_profile(
        self,
        profile: PersonalityProfile,
        new_scores: Dict[str, float],
        message_count: int
    ) -> PersonalityProfile:
        """
        Kişilik profilini yeni skorlarla güncelle.
        Exponential moving average kullanarak smooth güncelleme yapar.
        """
        # Ağırlık: daha fazla mesaj = daha az değişim (kararlılık)
        alpha = max(0.1, 1.0 / (message_count + 1))

        profile.openness = (1 - alpha) * profile.openness + alpha * new_scores.get("openness", 0.5)
        profile.conscientiousness = (1 - alpha) * profile.conscientiousness + alpha * new_scores.get("conscientiousness", 0.5)
        profile.extraversion = (1 - alpha) * profile.extraversion + alpha * new_scores.get("extraversion", 0.5)
        profile.agreeableness = (1 - alpha) * profile.agreeableness + alpha * new_scores.get("agreeableness", 0.5)
        profile.neuroticism = (1 - alpha) * profile.neuroticism + alpha * new_scores.get("neuroticism", 0.5)

        profile.total_messages_analyzed = message_count
        profile.last_updated = datetime.utcnow()

        # Güven seviyesini güncelle (daha fazla mesaj = daha yüksek güven)
        profile.analysis_confidence = min(0.95, message_count / 50)  # 50 mesajda %95 güven

        # 30+ mesaj analiz edildiyse profil tamamlanmış sayılır
        if message_count >= 30:
            profile.is_complete = True

        return profile

    async def detect_interests(
        self,
        conversation_history: List[ConversationMessage]
    ) -> List[str]:
        """Konuşmadan kullanıcının ilgi alanlarını tespit et"""

        user_messages = " ".join([
            msg.content for msg in conversation_history
            if not msg.is_from_ai
        ])

        prompt = f"""Aşağıdaki kullanıcı mesajlarından ilgi alanlarını tespit et:

{user_messages}

En fazla 10 ilgi alanı listele. Sadece JSON array formatında cevap ver:
["ilgi1", "ilgi2", ...]
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Kullanıcı mesajlarından ilgi alanlarını tespit et. Sadece JSON array döndür."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content.strip())
            return result if isinstance(result, list) else []

        except Exception as e:
            print(f"İlgi alanı tespit hatası: {e}")
            return []

    async def detect_communication_style(
        self,
        conversation_history: List[ConversationMessage]
    ) -> str:
        """Kullanıcının iletişim stilini tespit et"""

        user_messages = [msg for msg in conversation_history if not msg.is_from_ai]

        if not user_messages:
            return "unknown"

        # Mesaj uzunluğu analizi
        avg_length = sum(len(msg.content) for msg in user_messages) / len(user_messages)

        # Emoji kullanımı
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+",
            flags=re.UNICODE
        )
        emoji_count = sum(
            len(emoji_pattern.findall(msg.content))
            for msg in user_messages
        )

        # Soru işareti kullanımı
        question_count = sum(
            msg.content.count("?")
            for msg in user_messages
        )

        # Stil belirleme
        if avg_length > 100 and question_count > len(user_messages) * 0.3:
            return "expressive"  # Uzun, sorgulayıcı mesajlar
        elif avg_length < 30 and emoji_count < len(user_messages) * 0.2:
            return "direct"  # Kısa, net mesajlar
        elif emoji_count > len(user_messages) * 0.5:
            return "expressive"  # Çok emoji kullanan
        elif avg_length > 80:
            return "diplomatic"  # Uzun, açıklayıcı mesajlar
        else:
            return "reserved"  # Kısa, mesafeli mesajlar

    def get_next_question(
        self,
        phase: int,
        covered_topics: List[str]
    ) -> str:
        """Bir sonraki analiz sorusunu getir"""

        questions = self.ANALYSIS_QUESTIONS.get(phase, self.ANALYSIS_QUESTIONS[1])

        for question in questions:
            # Basit kontrol: soruyu daha önce sormadık mı?
            question_key = question[:30]  # İlk 30 karakter
            if question_key not in covered_topics:
                return question

        # Tüm sorular sorulduysa rastgele bir tane döndür
        import random
        return random.choice(questions)
