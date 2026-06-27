# Casos de Uso

## CU01 Monitorear servicio web

**Actor:** Monitor Playwright.

**Precondicion:** La URL monitoreada esta configurada.

**Flujo principal:**
1. El monitor abre la URL configurada.
2. Playwright espera la respuesta de navegacion.
3. El monitor obtiene el codigo HTTP cuando esta disponible.
4. El monitor mide el tiempo de respuesta.
5. El monitor muestra estado OK en consola.

**Flujo alternativo:** Si ocurre timeout, error DNS, error HTTP o fallo de navegacion, el monitor genera un mensaje descriptivo y registra un incidente en la API.

**Postcondicion:** El resultado del monitoreo queda informado en consola y, si falla, registrado como incidente.

## CU02 Registrar incidente

**Actor:** Playwright, remediador o usuario tecnico.

**Precondicion:** La API FastAPI esta activa y conectada a la base de datos.

**Flujo principal:**
1. El actor envia `POST /incidentes`.
2. La API valida los campos `servicio`, `estado` y `mensaje`.
3. La API guarda el incidente en la base de datos.
4. La API retorna el incidente creado con `id` y `fecha_hora`.

**Flujo alternativo:** Si la base de datos no esta disponible, la API retorna error y el incidente no se persiste.

**Postcondicion:** El incidente queda almacenado en la tabla `incidentes`.

## CU03 Consultar incidentes

**Actor:** Usuario tecnico, dashboard o herramienta externa.

**Precondicion:** Existen cero o mas incidentes registrados.

**Flujo principal:**
1. El actor solicita `GET /incidentes`.
2. La API consulta la tabla `incidentes`.
3. La API retorna la lista ordenada por `id`.

**Flujo alternativo:** Si la base de datos no responde, la API informa error.

**Postcondicion:** El actor recibe la lista actual de incidentes.

## CU04 Visualizar dashboard

**Actor:** Usuario tecnico.

**Precondicion:** La API esta activa y permite consultas desde el navegador.

**Flujo principal:**
1. El usuario abre el dashboard HTML.
2. El dashboard consulta `GET /incidentes`.
3. El dashboard calcula el total de incidentes.
4. El dashboard renderiza la tabla con los campos principales.

**Flujo alternativo:** Si la API no responde o el navegador bloquea la peticion, el dashboard muestra un mensaje de error.

**Postcondicion:** El usuario visualiza el estado actual de incidentes.

## CU05 Ejecutar remediacion

**Actor:** Usuario tecnico.

**Precondicion:** Las variables SSH del remediador estan configuradas.

**Flujo principal:**
1. El usuario ejecuta `remediador.py`.
2. Paramiko intenta conectar al host SSH.
3. El remediador ejecuta el comando configurado.
4. El remediador muestra resultado y fecha/hora.
5. El remediador registra el resultado en la API.

**Flujo alternativo:** Si falla la conexion SSH o el comando, el remediador registra el error en la API.

**Postcondicion:** El resultado de remediacion queda visible en consola y registrado como incidente o evento.

## CU06 Ejecutar remediacion desde Rocketbot

**Actor:** Rocketbot.

**Precondicion:** Rocketbot tiene configurado el flujo para invocar el remediador.

**Flujo principal:**
1. Rocketbot detecta o recibe una condicion de remediacion.
2. Rocketbot ejecuta el modulo de remediacion.
3. El remediador usa Paramiko para ejecutar acciones por SSH.
4. El resultado se registra en la API.

**Flujo alternativo:** Si Rocketbot no puede ejecutar el modulo, se informa el error en la evidencia del flujo.

**Postcondicion:** La remediacion queda ejecutada o documentada como fallida.
