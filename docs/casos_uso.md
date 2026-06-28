# Casos de uso verificados

## CU01 Monitorear servicio

Playwright navega, comprueba código HTTP y texto esperado, mide duración y retorna
un código de proceso. Ante falla intenta capturar PNG y registrar un evento.

## CU02 Registrar evento

Un componente envía JSON con `X-API-Key`. La API rechaza credenciales, campos extra,
vacíos, estados desconocidos y longitudes fuera de contrato; confirma con HTTP 201.

## CU03 Consultar y visualizar

El operador consulta páginas de hasta 100 eventos. El dashboard solicita 20,
presenta el total, escapa datos y muestra errores o timeouts.

## CU04 Recuperar servicio

Tras confirmar una caída, el gestor invoca el remediador. Este acepta únicamente
`sitio-vigilado`, lo recrea con Compose y el gestor vuelve a comprobarlo.

## CU05 Activar contingencia

Si CU04 no recupera el principal, se inicia el perfil `continuidad`, se valida el
respaldo y se registra/notifica la decisión. Si también falla, se escala manualmente.

## CU06 Orquestar desde Rocketbot

Rocketbot Studio invoca el adaptador `.bat`; este conserva códigos, salidas y tiempos
de cada módulo en una evidencia JSON. La ejecución visual requiere configurar y
mostrar el robot real durante la defensa.
