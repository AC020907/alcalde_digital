import os
import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


# TEST_DATABASE_URL=postgresql://... ejecuta la suite contra Postgres (tablas recreadas en cada prueba).
POSTGRES_PRUEBAS = os.environ.get("TEST_DATABASE_URL")


def _url_prueba(tmp_path):
    if not POSTGRES_PRUEBAS:
        return f"sqlite:///{tmp_path / 'test.db'}"
    from sqlalchemy import create_engine
    from app.db import metadata, normalize_url
    engine = create_engine(normalize_url(POSTGRES_PRUEBAS))
    metadata.drop_all(engine)
    engine.dispose()
    return POSTGRES_PRUEBAS


@pytest.fixture
def make_client(tmp_path):
    url = _url_prueba(tmp_path)
    creados = []

    def factory(**overrides):
        defaults = dict(
            database_url=url, env="development",
            allowed_origins=("*",), rate_scores_per_hour=1000, rate_start_per_hour=1000,
            rate_get_per_min=100000, rate_player_scores_per_hour=1000,
            rate_player_start_per_hour=1000)
        app = create_app(replace(Settings(), **{**defaults, **overrides}))
        creados.append(app)
        return TestClient(app)
    yield factory
    # Cada app abre su propio pool: sin cerrarlo, Postgres se queda sin conexiones a mitad de la suite.
    for app in creados:
        app.state.store.engine.dispose()


@pytest.fixture
def client(make_client):
    return make_client()


def new_id() -> str:
    return str(uuid.uuid4())


def payload(**overrides) -> dict:
    body = {
        "run_id": new_id(), "player_id": new_id(), "alias": "Ciudadano-4821",
        "platform": "pc", "mode": "historia", "final": "informada", "score": 742,
        "components": {"verificacion": 240, "decisiones": 190, "minijuegos": 150,
                       "investigacion": 90, "ciudad": 72},
        "evidencias": 2, "duration_s": 1650,
        "finales_desbloqueados": ["dividida", "informada"], "version": "2.0",
    }
    body.update(overrides)
    return body


def with_components(**comp) -> dict:
    base = {"verificacion": 240, "decisiones": 190, "minijuegos": 150,
            "investigacion": 90, "ciudad": 72}
    base.update(comp)
    return {"components": base, "score": sum(base.values())}
