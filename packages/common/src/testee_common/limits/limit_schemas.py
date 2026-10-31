from pydantic import BaseModel, computed_field


class BudgetOut(BaseModel):
    """How much of a shared daily budget (a limit for everyone) is used today, for the admin
    zone's AI costs tab: each owning service's GET /superadmin/budgets."""

    name: str
    used: float
    limit: float
    unit: str

    @computed_field
    @property
    def share(self) -> float:
        """Of the limit, the share used, 0 to 1 (more once over it)."""
        return self.used / self.limit if self.limit else 0.0
