from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class MCPQAHistory(SQLModel, table=True):
    """Persisted record of every MCP /ask question and its answer.

    Used to power lightweight retrieval (Option C): recent, relevant prior
    questions and their answers are surfaced into the advisor prompt so the
    assistant can build on past analysis and stay consistent over time.
    """

    __tablename__ = "mcp_qa_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    question: str = Field(sa_column=Column(Text, nullable=False))
    normalized_question: str = Field(sa_column=Column(Text, nullable=False))
    mode: str = Field(default="report", index=True)
    matched_tool: Optional[str] = Field(default=None, index=True)
    answer_summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    answer_json: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    feedback: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
