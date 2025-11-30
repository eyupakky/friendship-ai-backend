"""
Eşleştirme Motoru

Kişilik profillerine göre kullanıcıları eşleştirir.
Kosinüs benzerliği ve özel uyumluluk algoritmalarını kullanır.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from ..models.personality import (
    PersonalityProfile,
    PersonalityTrait,
    MatchScore,
)


class MatchingEngine:
    """Kullanıcıları kişilik profillerine göre eşleştiren motor"""

    # Kişilik uyumluluğu kuralları
    # Bazı özellikler benzerlik ister, bazıları tamamlayıcılık
    COMPATIBILITY_RULES = {
        # (trait1, trait2, rule_type, weight)
        # rule_type: "similar" = benzer olmalı, "complementary" = tamamlayıcı olmalı, "balanced" = dengeli
        "openness": {"type": "similar", "weight": 1.2},  # Benzer açıklık iyi
        "conscientiousness": {"type": "similar", "weight": 1.0},  # Benzer düzen iyi
        "extraversion": {"type": "balanced", "weight": 1.5},  # Çok farklı olmamalı
        "agreeableness": {"type": "similar", "weight": 1.3},  # Benzer uyumluluk çok iyi
        "neuroticism": {"type": "low_both", "weight": 1.4},  # İkisi de düşük olmalı
    }

    # Arkadaşlık türleri
    FRIENDSHIP_TYPES = {
        "deep": {
            "description": "Derin, anlamlı arkadaşlık",
            "requirements": {
                "openness_min": 0.6,
                "agreeableness_min": 0.6,
                "extraversion_range": (0.3, 0.8)
            }
        },
        "activity_based": {
            "description": "Aktivite odaklı arkadaşlık",
            "requirements": {
                "extraversion_min": 0.5,
                "conscientiousness_min": 0.4
            }
        },
        "intellectual": {
            "description": "Entelektüel, fikir paylaşımlı arkadaşlık",
            "requirements": {
                "openness_min": 0.7,
                "conscientiousness_min": 0.5
            }
        },
        "casual": {
            "description": "Rahat, gündelik arkadaşlık",
            "requirements": {
                "agreeableness_min": 0.5,
                "neuroticism_max": 0.5
            }
        }
    }

    def __init__(self):
        self.user_profiles: Dict[str, PersonalityProfile] = {}

    def add_profile(self, profile: PersonalityProfile):
        """Kullanıcı profilini eşleştirme havuzuna ekle"""
        self.user_profiles[profile.user_id] = profile

    def remove_profile(self, user_id: str):
        """Kullanıcı profilini havuzdan çıkar"""
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]

    def calculate_match_score(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> MatchScore:
        """
        İki profil arasındaki eşleşme skorunu hesapla.

        Algoritma:
        1. Big Five özellikleri için uyumluluk hesapla
        2. İlgi alanı örtüşmesini hesapla
        3. İletişim stili uyumluluğunu hesapla
        4. Ağırlıklı toplam skor oluştur
        """
        # 1. Kişilik özelliği uyumluluğu
        trait_scores = self._calculate_trait_compatibility(profile1, profile2)

        # 2. İlgi alanı örtüşmesi
        interest_score = self._calculate_interest_overlap(profile1, profile2)

        # 3. İletişim stili uyumluluğu
        comm_score = self._calculate_communication_compatibility(profile1, profile2)

        # 4. Genel skor (ağırlıklı ortalama)
        overall_score = (
            sum(trait_scores.values()) / len(trait_scores) * 0.5 +  # %50 kişilik
            interest_score * 0.3 +  # %30 ilgi alanları
            comm_score * 0.2  # %20 iletişim stili
        )

        # Arkadaşlık türünü belirle
        friendship_type = self._predict_friendship_type(profile1, profile2, trait_scores)

        # Eşleşme nedenlerini oluştur
        match_reasons = self._generate_match_reasons(
            profile1, profile2, trait_scores, interest_score
        )

        # Potansiyel zorlukları belirle
        challenges = self._identify_potential_challenges(profile1, profile2, trait_scores)

        return MatchScore(
            user_id_1=profile1.user_id,
            user_id_2=profile2.user_id,
            overall_score=round(overall_score, 3),
            trait_compatibility=trait_scores,
            interest_overlap=round(interest_score, 3),
            communication_compatibility=round(comm_score, 3),
            predicted_friendship_type=friendship_type,
            match_reasons=match_reasons,
            potential_challenges=challenges,
            created_at=datetime.utcnow()
        )

    def _calculate_trait_compatibility(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> Dict[str, float]:
        """Her kişilik özelliği için uyumluluk skorunu hesapla"""
        scores = {}

        trait_pairs = [
            ("openness", profile1.openness, profile2.openness),
            ("conscientiousness", profile1.conscientiousness, profile2.conscientiousness),
            ("extraversion", profile1.extraversion, profile2.extraversion),
            ("agreeableness", profile1.agreeableness, profile2.agreeableness),
            ("neuroticism", profile1.neuroticism, profile2.neuroticism),
        ]

        for trait_name, val1, val2 in trait_pairs:
            rule = self.COMPATIBILITY_RULES[trait_name]
            rule_type = rule["type"]

            if rule_type == "similar":
                # Benzer değerler iyi
                diff = abs(val1 - val2)
                score = 1.0 - diff

            elif rule_type == "complementary":
                # Tamamlayıcı değerler iyi (biri yüksek biri düşük)
                score = abs(val1 - val2)

            elif rule_type == "balanced":
                # Çok uç farklar kötü, orta farklar ok
                diff = abs(val1 - val2)
                if diff < 0.3:
                    score = 1.0 - diff
                elif diff < 0.5:
                    score = 0.7
                else:
                    score = 0.5 - (diff - 0.5)

            elif rule_type == "low_both":
                # İkisi de düşük olması iyi (nevrotiklik için)
                avg = (val1 + val2) / 2
                score = 1.0 - avg  # Düşük ortalama = yüksek skor

            else:
                score = 0.5

            scores[trait_name] = round(max(0.0, min(1.0, score)), 3)

        return scores

    def _calculate_interest_overlap(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> float:
        """İlgi alanı örtüşmesini hesapla"""
        if not profile1.interests or not profile2.interests:
            return 0.5  # Bilgi yoksa nötr

        set1 = set(interest.lower() for interest in profile1.interests)
        set2 = set(interest.lower() for interest in profile2.interests)

        if not set1 or not set2:
            return 0.5

        # Jaccard benzerliği
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.5

        jaccard = intersection / union

        # Minimum 2 ortak ilgi alanı varsa bonus
        if intersection >= 2:
            jaccard = min(1.0, jaccard + 0.1)

        return jaccard

    def _calculate_communication_compatibility(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> float:
        """İletişim stili uyumluluğunu hesapla"""

        style1 = profile1.communication_style
        style2 = profile2.communication_style

        if not style1 or not style2:
            return 0.5  # Bilgi yoksa nötr

        # Uyumluluk matrisi
        compatibility_matrix = {
            ("direct", "direct"): 0.8,
            ("direct", "diplomatic"): 0.6,
            ("direct", "expressive"): 0.5,
            ("direct", "reserved"): 0.4,

            ("diplomatic", "diplomatic"): 0.9,
            ("diplomatic", "expressive"): 0.7,
            ("diplomatic", "reserved"): 0.6,

            ("expressive", "expressive"): 0.85,
            ("expressive", "reserved"): 0.4,

            ("reserved", "reserved"): 0.7,
        }

        # Her iki yönü de kontrol et
        key1 = (style1, style2)
        key2 = (style2, style1)

        return compatibility_matrix.get(key1, compatibility_matrix.get(key2, 0.5))

    def _predict_friendship_type(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> str:
        """Olası arkadaşlık türünü tahmin et"""

        avg_openness = (profile1.openness + profile2.openness) / 2
        avg_extraversion = (profile1.extraversion + profile2.extraversion) / 2
        avg_agreeableness = (profile1.agreeableness + profile2.agreeableness) / 2
        avg_conscientiousness = (profile1.conscientiousness + profile2.conscientiousness) / 2
        avg_neuroticism = (profile1.neuroticism + profile2.neuroticism) / 2

        # Skorlara göre en uygun türü belirle
        type_scores = {}

        # Deep friendship
        deep_score = (
            avg_openness * 0.3 +
            avg_agreeableness * 0.4 +
            trait_scores.get("openness", 0.5) * 0.3
        )
        type_scores["deep"] = deep_score

        # Activity-based
        activity_score = (
            avg_extraversion * 0.4 +
            avg_conscientiousness * 0.3 +
            (1 - avg_neuroticism) * 0.3
        )
        type_scores["activity_based"] = activity_score

        # Intellectual
        intellectual_score = (
            avg_openness * 0.5 +
            avg_conscientiousness * 0.3 +
            trait_scores.get("openness", 0.5) * 0.2
        )
        type_scores["intellectual"] = intellectual_score

        # Casual
        casual_score = (
            avg_agreeableness * 0.4 +
            (1 - avg_neuroticism) * 0.4 +
            0.5 * 0.2  # Base score
        )
        type_scores["casual"] = casual_score

        # En yüksek skoru alan türü döndür
        return max(type_scores, key=type_scores.get)

    def _generate_match_reasons(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile,
        trait_scores: Dict[str, float],
        interest_score: float
    ) -> List[str]:
        """Eşleşme nedenlerini oluştur"""
        reasons = []

        # Yüksek uyumluluk skorları için nedenler
        if trait_scores.get("openness", 0) > 0.7:
            reasons.append("İkiniz de yeni deneyimlere açıksınız")

        if trait_scores.get("agreeableness", 0) > 0.7:
            reasons.append("Benzer düzeyde anlayışlı ve empatiksiniz")

        if trait_scores.get("extraversion", 0) > 0.7:
            reasons.append("Sosyal enerji seviyeniz uyumlu")

        if trait_scores.get("conscientiousness", 0) > 0.7:
            reasons.append("Düzen ve planlama konusunda benzer yaklaşımlarınız var")

        if trait_scores.get("neuroticism", 0) > 0.7:
            reasons.append("Duygusal olarak dengeli bir arkadaşlık kurabilirsiniz")

        # İlgi alanları
        if interest_score > 0.5:
            common = set(profile1.interests) & set(profile2.interests)
            if common:
                reasons.append(f"Ortak ilgi alanlarınız var: {', '.join(list(common)[:3])}")

        # İletişim stili
        if profile1.communication_style == profile2.communication_style:
            reasons.append(f"İletişim stiliniz uyumlu: {profile1.communication_style}")

        return reasons[:5]  # En fazla 5 neden

    def _identify_potential_challenges(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> List[str]:
        """Potansiyel zorlukları belirle"""
        challenges = []

        # Düşük uyumluluk skorları için uyarılar
        if trait_scores.get("extraversion", 1) < 0.4:
            diff = abs(profile1.extraversion - profile2.extraversion)
            if diff > 0.4:
                if profile1.extraversion > profile2.extraversion:
                    challenges.append("Biri daha sosyal, diğeri daha içe dönük olabilir")
                else:
                    challenges.append("Sosyallik seviyelerinde fark var")

        if trait_scores.get("conscientiousness", 1) < 0.4:
            challenges.append("Düzen ve planlama konusunda farklı yaklaşımlar olabilir")

        if trait_scores.get("neuroticism", 1) < 0.4:
            avg_neuroticism = (profile1.neuroticism + profile2.neuroticism) / 2
            if avg_neuroticism > 0.6:
                challenges.append("Stresli dönemlerde birbirinizi etkileyebilirsiniz")

        # İletişim stili uyumsuzluğu
        if profile1.communication_style and profile2.communication_style:
            if (profile1.communication_style == "direct" and
                profile2.communication_style == "reserved"):
                challenges.append("İletişim tarzlarınız farklı - sabır gerekebilir")

        return challenges[:3]  # En fazla 3 uyarı

    def find_best_matches(
        self,
        user_id: str,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[MatchScore]:
        """
        Bir kullanıcı için en iyi eşleşmeleri bul.

        Args:
            user_id: Eşleşme aranan kullanıcı
            limit: Döndürülecek maksimum eşleşme sayısı
            min_score: Minimum eşleşme skoru

        Returns:
            List[MatchScore]: Skora göre sıralı eşleşme listesi
        """
        if user_id not in self.user_profiles:
            return []

        user_profile = self.user_profiles[user_id]

        if not user_profile.is_complete:
            return []  # Profil tamamlanmamışsa eşleşme yapma

        matches = []

        for other_id, other_profile in self.user_profiles.items():
            if other_id == user_id:
                continue

            if not other_profile.is_complete:
                continue

            match_score = self.calculate_match_score(user_profile, other_profile)

            if match_score.overall_score >= min_score:
                matches.append(match_score)

        # Skora göre sırala
        matches.sort(key=lambda x: x.overall_score, reverse=True)

        return matches[:limit]

    def get_compatibility_explanation(self, match: MatchScore) -> str:
        """Eşleşme için açıklama metni oluştur"""
        score_percent = int(match.overall_score * 100)

        explanation = f"Uyumluluk Skoru: %{score_percent}\n\n"

        explanation += f"Arkadaşlık Türü: {self.FRIENDSHIP_TYPES.get(match.predicted_friendship_type, {}).get('description', match.predicted_friendship_type)}\n\n"

        if match.match_reasons:
            explanation += "Neden uyumsunuz:\n"
            for reason in match.match_reasons:
                explanation += f"  • {reason}\n"
            explanation += "\n"

        if match.potential_challenges:
            explanation += "Dikkat edilmesi gerekenler:\n"
            for challenge in match.potential_challenges:
                explanation += f"  • {challenge}\n"

        return explanation
