"""Herramientas para realizar scraping de directorios de proveedores.

Este módulo implementa una clase que obtiene datos de páginas web de forma
concurrente utilizando ``aiohttp`` y ``BeautifulSoup``.  El objetivo es
recuperar información básica de proveedores que operan en la Provincia de
Buenos Aires.

La clase ``DirectoryScraper`` no está acoplada a un directorio en particular;
se espera que el usuario adapte los selectores CSS a la estructura concreta de
las páginas que desea scrapear.
"""
from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class Provider:
    """Representa a un proveedor encontrado en un directorio."""

    nombre: str
    servicio: str
    zona: str
    email: str


class DirectoryScraper:
    """Scraper concurrente de directorios.

    Parameters
    ----------
    location:
        Cadena utilizada para filtrar resultados por ubicación. Solo se
        retornarán los proveedores cuyo texto contenga esta ubicación.
    max_entries:
        Número máximo de proveedores a obtener. ``None`` significa sin límite.
    delay_range:
        Rango de tiempo (en segundos) que se espera aleatoriamente entre
        requests para simular un comportamiento humano y respetuoso.
    """

    def __init__(
        self,
        location: str,
        max_entries: Optional[int] = None,
        delay_range: tuple[float, float] = (1, 3),
    ) -> None:
        self.location = location.lower()
        self.max_entries = max_entries
        self.delay_range = delay_range

    async def scrape(self, url_map: Dict[str, Iterable[str]]) -> List[Provider]:
        """Realiza scraping concurrente.

        Parameters
        ----------
        url_map:
            Diccionario donde las claves son el nombre del servicio y los
            valores una lista de URLs a scrapear para dicho servicio.

        Returns
        -------
        list of :class:`Provider`
            Lista con los proveedores obtenidos.
        """

        results: List[Provider] = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service, urls in url_map.items():
                for url in urls:
                    tasks.append(
                        asyncio.create_task(
                            self._fetch_and_parse(session, url, service, results)
                        )
                    )
            if tasks:
                await asyncio.gather(*tasks)
        return results

    async def _fetch_and_parse(
        self,
        session: aiohttp.ClientSession,
        url: str,
        service: str,
        results: List[Provider],
    ) -> None:
        """Obtiene una página y extrae los proveedores.

        Cualquier error se registra mediante ``logging`` sin detener el resto de
        las tareas.
        """

        if self.max_entries and len(results) >= self.max_entries:
            return
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                html = await resp.text()
        except Exception as exc:  # pragma: no cover - manejo básico
            logging.error("No se pudo obtener %s: %s", url, exc)
            return

        # Pausa aleatoria para evitar bloqueos por scraping agresivo
        await asyncio.sleep(random.uniform(*self.delay_range))

        for provider in self._parse(html, service):
            if self.max_entries and len(results) >= self.max_entries:
                break
            results.append(provider)

    def _parse(self, html: str, service: str) -> Iterable[Provider]:
        """Extrae proveedores desde el HTML.

        La lógica de extracción es intencionalmente genérica. El usuario puede
        modificar los selectores CSS según la estructura real del sitio a
        scrapear.
        """

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".provider")
        for card in cards:
            texto = card.get_text(" ", strip=True).lower()
            if self.location not in texto:
                continue

            nombre = card.select_one(".name")
            zona = card.select_one(".zone")
            email_tag = card.select_one("a[href^=mailto]")

            yield Provider(
                nombre=nombre.get_text(strip=True) if nombre else "",
                servicio=service,
                zona=zona.get_text(strip=True) if zona else "",
                email=email_tag["href"].replace("mailto:", "") if email_tag else "",
            )
