from pathlib import Path

from sqlalchemy import text

from ETL import bce, inec, mineduc, supercias


def test_etl_modules_resolve_project_data_paths():
    assert Path(bce.BASE_DIR).exists()
    assert (bce.BASE_DIR / "data" / "BCE" / "crecimiento-anual-pib.csv").exists()
    assert (inec.BASE_DIR / "data" / "INEC" / "2. Tasas.csv").exists()
    assert (mineduc.BASE_DIR / "data" / "Supercias y MINEDUC" / "2Registro-Administrativo-Historico_2009-2024-Fin.xlsx").exists()
    assert (supercias.BASE_DIR / "data" / "Supercias y MINEDUC" / "bi_ranking.csv").exists()


def test_geografia_nacional_exists():
    bce.asegurar_geografia_nacional()
    with bce.engine.connect() as conn:
        count = conn.execute(text("SELECT 1 FROM dim_geografia WHERE id_geo = 0")).scalar()
    assert count == 1
