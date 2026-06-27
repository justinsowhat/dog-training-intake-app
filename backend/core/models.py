from backend.core.database import Base
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

class ConsultationORM(Base):
    __tablename__ = "consultations"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intake_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    messages: Mapped[list["ChatMessageORM"]] = relationship(
        "ChatMessageORM", back_populates="consultation", cascade="all, delete-orphan", lazy="selectin"
    )
    training_plan: Mapped["TrainingPlanORM"] = relationship(
        "TrainingPlanORM", back_populates="consultation", uselist=False, cascade="all, delete-orphan"
    )
    
class ChatMessageORM(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    consultation_id: Mapped[str] = mapped_column(ForeignKey("consultations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # system, user, assistant, or assistant_plan
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    consultation: Mapped[ConsultationORM] = relationship("ConsultationORM", back_populates="messages")

class TrainingPlanORM(Base):
    __tablename__ = "training_plans"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    consultation_id: Mapped[str] = mapped_column(ForeignKey("consultations.id"), nullable=False)
    plan_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    plan_status: Mapped[str] = mapped_column(String(20), default="proposed")  # proposed | finalized
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    consultation: Mapped[ConsultationORM] = relationship("ConsultationORM", back_populates="training_plan")
