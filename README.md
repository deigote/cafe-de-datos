# Café de Datos

Un cuaderno sencillo para recordar cafés y elegir mejor el próximo pedido: notas de la tienda, opiniones personales, fechas y precios en un CSV. Una web de solo lectura permite explorar y compartir la colección.

[Ver la colección de Deigote](https://deigote.github.io/cafe-de-datos/)

## Cómo usarlo

Copia este repositorio, abre tu agente de código y dile:

> Lee AGENTS.md y ayúdame a configurar mi colección de cafés.

El agente te preguntará por tus gustos, tiendas y preferencias de compra. Después puedes pedirle cosas como:

- «Prepara un pedido basándote en los cafés que me han gustado».
- «A este café le pongo un 3,5; está rico, pero solo repetiría si es barato».
- «Publica mis últimas notas».

Tu historial vive en `colecciones/tu-nombre/cafes.csv`; tus preferencias, en `preferencias.md`. Se incluyen una colección real y un ejemplo ficticio. No hay editor web ni cuentas: trabajas con tu agente y tus archivos.

## Si quieres ejecutarlo tú

Con Python 3.10 o posterior, sin instalar dependencias:

```sh
python3 scripts/construir.py --coleccion ejemplo
python3 -m http.server 8000 --directory dist
```

Abre http://localhost:8000. Para publicar, el agente configura `publicacion.local.json` a partir del ejemplo y GitHub Pages con `main /docs`. Después basta con:

```sh
python3 scripts/publicar.py --push
```

La publicación requiere Git y GitHub CLI autenticado. El script utiliza un clon separado y publica código y colecciones; no sube preferencias, comprobantes ni el archivo histórico. Los CSV publicados son públicos. No es necesario publicar después de cada cambio.
