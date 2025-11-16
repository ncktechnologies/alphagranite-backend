from src.app.interface.generated_schemas import SalesCT

# Thin re-export for other modules importing from src.app.database.sales_ct
SalesCT = SalesCT

__all__ = ["SalesCT"]
