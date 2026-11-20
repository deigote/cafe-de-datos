# Café de Datos

Un cuaderno de cafés en CSV, pensado para llevarlo con cualquier agente de código y compartirlo como una web estática. Sin editor web, base de datos, cuentas ni dependencias de Python externas.

Este repositorio incluye **la colección real de deigote** en `colecciones/deigote/` y un ejemplo ficticio independiente en `colecciones/ejemplo/`. Las notas son personales; las descripciones comerciales no son valoraciones.

## Probarlo

Necesitas Python 3.10 o posterior. Node solo se usa para las pruebas de JavaScript, no para ejecutar el visor.

```sh
python3 scripts/construir.py --coleccion ejemplo
python3 -m http.server 8000 --directory dist
```

Abre http://localhost:8000. Para ver la colección incluida, usa `--coleccion deigote`. El visor carga los datos mediante HTTP; no basta con hacer doble clic en index.html.

Permite buscar en nombres y comentarios, filtrar por puntuación, precios e intervalos de fecha de compra o valoración, y ordenar por puntuación, fecha, precio o nombre. Muestra cada café una vez, con compras y valoraciones desplegables. La nota de portada es la última valoración registrada de ese café, con su fecha y versión visibles; no es la nota de la última compra. El precio es el de la última compra/muestra registrada, por bolsa, sin normalizar tamaños ni convertir monedas. Los desconocidos se ordenan al final y no pasan filtros numéricos o de fecha.

## Empezar tu colección

1. Copia `colecciones/ejemplo/` como `colecciones/tu-nombre/`.
2. Cambia titulo, autor y descripcion en `coleccion.json`.
3. Vacía las filas de ejemplo de los tres CSV conservando las cabeceras.
4. Copia `preferencias.example.md` a `preferencias.md` y escribe libremente tus tiendas, gustos, formato y presupuesto.
5. Pide a tu agente que lea `AGENTS.md` y añada una compra o una valoración en tu colección.

Puedes eliminar las otras colecciones en tu copia. Todas las colecciones incluidas se publican en GitHub; la configuración elige cuál se muestra en la web. Las preferencias locales y los documentos originales quedan fuera.

## Datos y relaciones

Los tres CSV son la fuente de verdad, no exportaciones de Markdown. Edítalos con un agente, un editor o una biblioteca CSV. Comas, comillas y saltos de línea dentro de comentarios se admiten mediante el formato CSV estándar. Se valida su estructura antes de publicar. Usa números con punto decimal; fechas `AAAA-MM-DD`; vacío significa desconocido.

| Archivo | Una fila representa | Campos principales |
| --- | --- | --- |
| cafes.csv | Un café comercial | id, nombre, tienda, web, url, origen, proceso, descripcion, notas |
| compras.csv | Una línea de compra o muestra | id, cafe_id, pedido_id, fecha, fecha_registro, tipo, precio, moneda, cantidad, gramos, molienda, tueste, version, notas |
| valoraciones.csv | Una valoración de una versión probada | id, cafe_id, compra_id, fecha, fecha_consumo, puntuacion, version, notas |

`precio` es unitario; `cantidad` es número de bolsas. `tipo` es compra o muestra. Una muestra regalada puede tener precio vacío; no se inventa un valor comercial. Un cero explícito es distinto de un desconocido. `compra_id` puede quedar vacío cuando no se pueda relacionar con certeza la valoración con una compra; `cafe_id` y `version` conservan su contexto. La fecha de registro no reemplaza una fecha de compra desconocida. Un café repetido conserva su ID; cada nueva compra recibe otro ID y no hereda notas.

Si registras más de una moneda, los filtros de precio comparan importes nominales; utiliza una moneda común para comparar precios. El catálogo es histórico: no acredita stock ni precios actuales.

## Trabajo local y publicación

La carpeta local puede estar en Dropbox. Para evitar sincronizar `.git` a través de Dropbox, `scripts/publicar.py` usa un **clon separado**, dedicado a publicación. Copia solo código, documentación y colecciones; genera la web en `docs/` del clon. No mueve ni borra los originales.

Configuración inicial:

1. Crea un repositorio vacío en GitHub y autentica Git/GitHub CLI (`gh auth login`).
2. Copia `publicacion.example.json` a `publicacion.local.json`: pon tu `usuario/repositorio`, colección y ruta absoluta del clon fuera de esta carpeta.
3. Ejecuta `python3 scripts/publicar.py --push`. En un repositorio vacío, su rama predeterminada debe ser main.
4. En GitHub, Settings → Pages → Deploy from a branch → main → /docs.

Uso habitual:

```sh
# Después de editar los CSV, validar y previsualizar sin publicar:
python3 scripts/construir.py --coleccion deigote

# Cuando quieras actualizar GitHub y la web:
python3 scripts/publicar.py --push --mensaje "Añadir valoración del Burundi"
```

Sin `--push`, el script prepara una copia sin commit en el clon para revisar. Confirma o descarta allí esos cambios antes de volver a ejecutarlo. Si el clon tiene cambios locales, el script se detiene; nunca hace reset ni force push. Usa pull de avance rápido antes de copiar. Mantén el clon solo para publicación y realiza las ediciones en la carpeta de trabajo. Si alguien cambia el remoto, revisa y traslada esos cambios a la carpeta de trabajo antes de publicar para evitar sobrescribirlos con una copia antigua.

Solo los archivos de la lista de publicación se sincronizan. Si desaparece uno previamente gestionado, se elimina también del clon; archivos ajenos no se tocan. Los fallos de red no borran los CSV. Un push correcto inicia el despliegue de Pages, que puede tardar unos minutos.

No hace falta publicar después de cada nota. No hay sincronización en segundo plano. Preferencias, fuentes, propuestas locales y el archivo anterior no se suben. **Los CSV publicados sí son públicos**, igual que los comentarios del visor.

## Migración de la colección de deigote

Se migraron siete cafés, nueve líneas de compra/muestra y cinco valoraciones. Sidamo Shantawene y la línea comercial Ato Tona son una misma compra confirmada, no dos cafés comprados. La muestra Perú no se vincula a un pedido sin confirmación. Las valoraciones de Colombia y Nicaragua conservan versión de etiqueta y compra concreta sin confirmar. Las cuatro bolsas de noviembre están compradas, todavía sin valoración de esa compra. La fecha del pedido inicial y el envío final del pedido de noviembre siguen desconocidos.

La carpeta de trabajo conserva los Markdown originales en `archivo/markdown-inicial/`, y las fotos/comprobantes en `fuentes/`; las propuestas siguen en `pedidos/`. El archivo es evidencia de la migración y no otra base editable. Los nuevos datos se escriben únicamente en CSV.

## Pruebas

```sh
python3 -m unittest discover -s tests
node --test tests/visor.test.js
```

La web y el script son deliberadamente pequeños: HTML, CSS, JavaScript y biblioteca estándar de Python. Git y `gh` solo son necesarios para publicar.
