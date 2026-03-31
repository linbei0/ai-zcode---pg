from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.app import App


class AppRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, app_id: int) -> App | None:
        app = self.db.get(App, app_id)
        if app and app.is_delete == 0:
            return app
        return None

    def save(self, app: App) -> App:
        self.db.add(app)
        self.db.flush()
        return app
