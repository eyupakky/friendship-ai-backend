#!/usr/bin/env python3
"""
Terminal Chat - AI ile Konuşma

Bu script ile AI'a doğrudan terminal üzerinden mesaj gönderebilirsin.
Kullanım: python chat.py
"""

import asyncio
import sys
from src.services.conversation_ai import ConversationAI


async def main():
    print("=" * 60)
    print("  Friendship AI - Kişilik Analizi Chatbot")
    print("  Ollama ile çalışıyor (ücretsiz, yerel)")
    print("=" * 60)
    print()
    print("Çıkmak için 'q' veya 'quit' yazın.")
    print("Profil görmek için 'profil' yazın.")
    print()

    # AI'ı başlat
    ai = ConversationAI()

    # Kullanıcı ID'si
    user_id = "test_user"

    # Oturum başlat
    session = await ai.start_session(user_id)
    print(f"Oturum başlatıldı: {session.session_id[:8]}...")
    print()

    # Hoşgeldin mesajı
    print("AI: Merhaba! Ben senin arkadaşlık asistanınım.")
    print("    Seni tanımak ve en uygun arkadaşları bulmana yardımcı olmak için buradayım.")
    print("    Biraz sohbet edelim mi? Bana kendinden bahseder misin?")
    print()

    while True:
        try:
            # Kullanıcı girişi
            user_input = input("Sen: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['q', 'quit', 'exit', 'çıkış']:
                print("\nGörüşürüz! İyi günler.")
                break

            if user_input.lower() == 'profil':
                # Profil göster
                summary = await ai.get_session_summary(user_id)
                print("\n" + "=" * 40)
                print("KİŞİLİK PROFİLİ")
                print("=" * 40)
                if summary.get("profile"):
                    p = summary["profile"]
                    print(f"Deneyime Açıklık:  {_bar(p['openness'])} {p['openness']}")
                    print(f"Sorumluluk:        {_bar(p['conscientiousness'])} {p['conscientiousness']}")
                    print(f"Dışadönüklük:      {_bar(p['extraversion'])} {p['extraversion']}")
                    print(f"Uyumluluk:         {_bar(p['agreeableness'])} {p['agreeableness']}")
                    print(f"Nevrotiklik:       {_bar(p['neuroticism'])} {p['neuroticism']}")
                    print(f"\nGüven: %{int(p['confidence'] * 100)}")
                    print(f"Mesaj sayısı: {summary['user_messages']}")
                    print(f"Analiz aşaması: {summary['analysis_phase']}/5")
                    if p['interests']:
                        print(f"İlgi alanları: {', '.join(p['interests'])}")
                print("=" * 40 + "\n")
                continue

            # AI'a mesaj gönder
            print("\nAI düşünüyor...", end="", flush=True)
            ai_response, session, profile = await ai.process_message(user_id, user_input)
            print("\r" + " " * 20 + "\r", end="")  # "AI düşünüyor" mesajını temizle

            print(f"AI: {ai_response}")

            # Analiz durumu
            user_count = len([m for m in session.messages if not m.is_from_ai])
            print(f"    [Aşama: {session.analysis_phase}/5 | Mesaj: {user_count}/30 | Güven: %{int(profile.analysis_confidence * 100)}]")
            print()

            # Analiz tamamlandıysa bildir
            if session.is_analysis_complete:
                print("\n" + "=" * 40)
                print("ANALİZ TAMAMLANDI!")
                print("Profilini görmek için 'profil' yaz.")
                print("=" * 40 + "\n")

        except KeyboardInterrupt:
            print("\n\nÇıkılıyor...")
            break
        except Exception as e:
            print(f"\nHata: {e}")
            print("Tekrar deneyin.\n")


def _bar(value: float, width: int = 20) -> str:
    """Görsel bar oluştur"""
    if value is None:
        return "?" * width
    filled = int(value * width)
    return "█" * filled + "░" * (width - filled)


if __name__ == "__main__":
    asyncio.run(main())
