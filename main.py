"""
Friendship AI Backend - Ana Uygulama

Kişilik analizi yapan AI destekli arkadaşlık eşleştirme uygulaması.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import router
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü yönetimi"""
    # Başlangıç
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} başlatılıyor...")
    yield
    # Kapanış
    print("👋 Uygulama kapatılıyor...")


# FastAPI uygulaması
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Friendship AI Backend

    Kişilik analizi yapan AI destekli arkadaşlık eşleştirme API'si.

    ### Özellikler

    * **Konuşma AI**: Kullanıcılarla doğal sohbet yaparak kişilik analizi yapar
    * **Big Five Analizi**: OCEAN modeliyle kişilik profili oluşturur
    * **Akıllı Eşleştirme**: Kişilik uyumluluğuna göre arkadaş önerir

    ### Akış

    1. `/conversation/start` - Konuşma başlat
    2. `/conversation/message` - AI ile sohbet et (30+ mesaj)
    3. `/conversation/end` - Konuşmayı bitir
    4. `/matches/{user_id}` - Eşleşmeleri gör
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prodüksiyonda spesifik origin'ler kullanın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ı ekle
app.include_router(router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    """API bilgisi"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
