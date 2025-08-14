# Automatización de Reclutamiento de Proveedores

Este proyecto demuestra cómo automatizar la búsqueda y contacto de
profesionales que ofrecen servicios en la Provincia de Buenos Aires.

## Funcionalidades

* Scraping concurrente de directorios de servicios utilizando `aiohttp` y
  `BeautifulSoup`.
* Almacenamiento de los datos en CSV o SQLite.
* Envío de correos de invitación personalizados mediante SMTP.
* Configuración flexible a través de archivos YAML.

## Uso

1. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Editar `configs/settings.example.yml` con las URLs de los directorios, las
   credenciales SMTP y otras opciones. También puede modificar la lista de
   servicios en `configs/services_ba.yml`.

3. Ejecutar el script:

   ```bash
   python -m src.main --config configs/settings.example.yml --services configs/services_ba.yml
   ```

   Utilice `--test` para enviar los correos a la dirección `test_recipient` en
   lugar de a los proveedores reales.

## Aspectos éticos y legales

* Respete los archivos `robots.txt` y los términos de uso de los sitios
  web que scrapee.
* Obtenga consentimiento antes de enviar correos comerciales y proporcione una
  vía clara para darse de baja.
