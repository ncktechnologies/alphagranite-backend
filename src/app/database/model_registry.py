"""
Import every table model so SQLAlchemy can resolve relationships and foreign
keys that refer to other models by name.

The API gets this for free because its routers import every model. Standalone
processes (Celery worker, monthly_reports) only import the models they use, so
e.g. inserting an HCP ingestion run fails on its `users.id` foreign key. Those
entrypoints import this module for its side effect.
"""
import importlib
import pkgutil

import src.app.database as _package

# operation_workflow.py duplicates generated_schemas.OperationWorkflow;
# importing both redefines the table.
_SKIPPED_MODULES = {"operation_workflow", __name__.rsplit(".", 1)[-1]}

for _module in pkgutil.iter_modules(_package.__path__):
    if _module.name not in _SKIPPED_MODULES:
        importlib.import_module(f"{_package.__name__}.{_module.name}")
