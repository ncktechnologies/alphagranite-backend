from src.app.interface.generated_schemas import Drafting, DraftingSession, DraftingSessionNote

# Thin re-export for other modules importing from src.app.database.drafting
Drafting = Drafting
DraftingSession = DraftingSession
DraftingSessionNote = DraftingSessionNote

__all__ = ["Drafting", "DraftingSession", "DraftingSessionNote"]
