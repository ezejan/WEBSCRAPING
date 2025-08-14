"""Script principal para automatizar el reclutamiento de proveedores.

El script realiza scraping de directorios, almacena los resultados y envía
correos de invitación utilizando los datos configurados.

Uso de ejemplo::

    python -m src.main --config configs/settings.example.yml --services configs/services_ba.yml --test
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, Iterable, List

import yaml

from scraping.directory import DirectoryScraper, Provider
from storage.manager import DataManager
from emailer.client import EmailClient


def load_yaml(path: str | Path) -> dict:
    """Carga un archivo YAML y devuelve su contenido."""

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def build_url_map(base_urls: Iterable[str], services: Iterable[str]) -> Dict[str, List[str]]:
    """Crea un diccionario servicio -> [urls]."""

    url_map: Dict[str, List[str]] = {}
    for service in services:
        url_map[service] = [u.format(service=service) for u in base_urls]
    return url_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraping y envío de invitaciones")
    parser.add_argument(
        "--config",
        default="configs/settings.example.yml",
        help="Ruta al archivo de configuración principal",
    )
    parser.add_argument(
        "--services",
        default="configs/services_ba.yml",
        help="Archivo YAML con la lista de servicios a buscar",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo de prueba: los correos se envían a test_recipient",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_yaml(args.config)
    services = load_yaml(args.services).get("services", [])

    scraping_cfg = config.get("scraping", {})
    url_map = build_url_map(scraping_cfg.get("urls", []), services)

    scraper = DirectoryScraper(
        location=scraping_cfg.get("location", "Provincia de Buenos Aires"),
        max_entries=scraping_cfg.get("max_entries"),
        delay_range=tuple(scraping_cfg.get("delay_range", [1, 3])),
    )

    providers: List[Provider] = asyncio.run(scraper.scrape(url_map))
    if not providers:
        logging.warning("No se encontraron proveedores")
        return

    storage_cfg = config.get("storage", {})
    manager = DataManager(
        csv_file=storage_cfg.get("csv"), sqlite_file=storage_cfg.get("sqlite")
    )
    manager.save(providers)

    email_cfg = config.get("email", {})
    client = EmailClient(
        smtp_server=email_cfg.get("smtp_server", ""),
        smtp_port=email_cfg.get("smtp_port", 587),
        username=email_cfg.get("username"),
        password=email_cfg.get("password"),
        from_addr=email_cfg.get("from_addr", ""),
        subject=email_cfg.get("subject", "Invitación"),
        template_path=email_cfg.get("template_path", "configs/email_template.txt"),
    )

    for provider in providers[: config.get("max_emails", len(providers))]:
        client.send(provider, test_recipient=email_cfg.get("test_recipient") if args.test else None)


if __name__ == "__main__":  # pragma: no cover - ejecución directa
    main()
