from src.app.interface.generated_schemas import JobTechnicianWorkflow

# Thin re-export for other modules importing from src.app.database.clockwork
Clockwork = JobTechnicianWorkflow

__all__ = ["Clockwork", "JobTechnicianWorkflow"]
