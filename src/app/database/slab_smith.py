from src.app.interface.generated_schemas import SlabSmith, SlabSmithSession, SlabSmithSessionNote

# Thin re-export for other modules importing from src.app.database.slab_smith
SlabSmith = SlabSmith
SlabSmithSession = SlabSmithSession
SlabSmithSessionNote = SlabSmithSessionNote

__all__ = ["SlabSmith", "SlabSmithSession", "SlabSmithSessionNote"]
