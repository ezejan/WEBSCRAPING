"""Gestor de almacenamiento de datos de proveedores."""
from __future__ import annotations

import csv
import logging
import re
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from scraping.directory import Provider

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DataManager:
    """Guarda los datos extraídos en CSV y/o SQLite."""

    def __init__(self, csv_file: str | None = None, sqlite_file: str | None = None) -> None:
        self.csv_file = csv_file
        self.sqlite_file = sqlite_file

    def save(self, providers: Iterable[Provider]) -> None:
        providers = [p for p in providers if self._valid(p)]
        if self.csv_file:
            self._save_csv(providers)
        if self.sqlite_file:
            self._save_sqlite(providers)

    def _valid(self, provider: Provider) -> bool:
        """Valida información mínima del proveedor."""

        if provider.email and not EMAIL_RE.match(provider.email):
            logging.warning("Correo inválido descartado: %s", provider.email)
            return False
        return bool(provider.nombre)

    def _save_csv(self, providers: Iterable[Provider]) -> None:
        file = Path(self.csv_file)
        file.parent.mkdir(parents=True, exist_ok=True)
        write_header = not file.exists()

        with file.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["nombre", "servicio", "zona", "email"])
            if write_header:
                writer.writeheader()
            for p in providers:
                writer.writerow(asdict(p))
        logging.info("Datos guardados en %s", file)

    def _save_sqlite(self, providers: Iterable[Provider]) -> None:
        con = sqlite3.connect(self.sqlite_file)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS proveedores (
                nombre TEXT,
                servicio TEXT,
                zona TEXT,
                email TEXT
            )
            """
        )
        cur.executemany(
            "INSERT INTO proveedores VALUES (:nombre, :servicio, :zona, :email)",
            [asdict(p) for p in providers],
        )
        con.commit()
        con.close()
        logging.info("Datos guardados en %s", self.sqlite_file)
