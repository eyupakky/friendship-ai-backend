"""
Veritabanı Modelleri

SQLAlchemy ORM modelleri - PostgreSQL için optimize edilmiş.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, Integer,
    ForeignKey, Text, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

Base = declarative_base()


class User(Base):
    """Kullanıcı tablosu"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    avatar_url = Column(String(500))

    # Durum
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Tarihler
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime)

    # İlişkiler
    personality_profile = relationship("PersonalityProfileDB", back_populates="user", uselist=False)
    conversations = relationship("ConversationSessionDB", back_populates="user")
    matches_as_user1 = relationship(
        "MatchDB",
        foreign_keys="MatchDB.user_id_1",
        back_populates="user1"
    )
    matches_as_user2 = relationship(
        "MatchDB",
        foreign_keys="MatchDB.user_id_2",
        back_populates="user2"
    )


class PersonalityProfileDB(Base):
    """Kişilik profili tablosu"""
    __tablename__ = "personality_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Big Five özellikleri
    openness = Column(Float, default=0.5)
    conscientiousness = Column(Float, default=0.5)
    extraversion = Column(Float, default=0.5)
    agreeableness = Column(Float, default=0.5)
    neuroticism = Column(Float, default=0.5)

    # Ek özellikler
    humor_style = Column(String(50))
    communication_style = Column(String(50))
    interests = Column(ARRAY(String), default=[])
    values = Column(ARRAY(String), default=[])

    # Meta
    analysis_confidence = Column(Float, default=0.0)
    total_messages_analyzed = Column(Integer, default=0)
    is_complete = Column(Boolean, default=False)

    # Tarihler
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="personality_profile")

    # İndeksler
    __table_args__ = (
        Index("idx_profile_complete", "is_complete"),
        Index("idx_profile_confidence", "analysis_confidence"),
    )


class ConversationSessionDB(Base):
    """Konuşma oturumu tablosu"""
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Oturum durumu
    analysis_phase = Column(Integer, default=1)
    is_analysis_complete = Column(Boolean, default=False)
    topics_covered = Column(ARRAY(String), default=[])

    # Tarihler
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    # İlişkiler
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessageDB", back_populates="session", order_by="ConversationMessageDB.timestamp")

    # İndeksler
    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_active", "ended_at"),
    )


class ConversationMessageDB(Base):
    """Konuşma mesajı tablosu"""
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)
    is_from_ai = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Analiz sonuçları
    sentiment_score = Column(Float)
    detected_traits = Column(JSON)  # {"openness": 0.7, "extraversion": 0.5, ...}

    # İlişkiler
    session = relationship("ConversationSessionDB", back_populates="messages")

    # İndeksler
    __table_args__ = (
        Index("idx_message_session", "session_id"),
        Index("idx_message_timestamp", "timestamp"),
    )


class MatchDB(Base):
    """Eşleşme tablosu"""
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id_1 = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_id_2 = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Skorlar
    overall_score = Column(Float, nullable=False)
    trait_compatibility = Column(JSON)  # {"openness": 0.8, "extraversion": 0.6, ...}
    interest_overlap = Column(Float, default=0.0)
    communication_compatibility = Column(Float, default=0.0)

    # Tahminler
    predicted_friendship_type = Column(String(50))
    match_reasons = Column(ARRAY(String), default=[])
    potential_challenges = Column(ARRAY(String), default=[])

    # Durum
    status = Column(String(20), default="pending")  # pending, accepted, rejected, blocked
    user1_action = Column(String(20))  # liked, passed
    user2_action = Column(String(20))

    # Tarihler
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    matched_at = Column(DateTime)  # İkisi de kabul edince

    # İlişkiler
    user1 = relationship("User", foreign_keys=[user_id_1], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user_id_2], back_populates="matches_as_user2")

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="unique_match_pair"),
        Index("idx_match_user1", "user_id_1"),
        Index("idx_match_user2", "user_id_2"),
        Index("idx_match_score", "overall_score"),
        Index("idx_match_status", "status"),
    )


class Friendship(Base):
    """Arkadaşlık tablosu - eşleşme kabul edildikten sonra"""
    __tablename__ = "friendships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id_1 = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_id_2 = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"))

    # Arkadaşlık durumu
    status = Column(String(20), default="active")  # active, paused, ended
    friendship_type = Column(String(50))

    # Etkileşim metrikleri
    message_count = Column(Integer, default=0)
    last_interaction_at = Column(DateTime)

    # Tarihler
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    # İndeksler
    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="unique_friendship_pair"),
        Index("idx_friendship_user1", "user_id_1"),
        Index("idx_friendship_user2", "user_id_2"),
        Index("idx_friendship_status", "status"),
    )
