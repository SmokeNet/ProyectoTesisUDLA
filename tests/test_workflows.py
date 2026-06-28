"""Pruebas unitarias de las decisiones que no requieren infraestructura externa."""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

RAIZ = Path(__file__).resolve().parents[1]


def cargar_modulo(nombre: str, ruta: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / ruta)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No fue posible cargar {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


remediador = cargar_modulo("remediador_prueba", "remediacion/remediador.py")
continuidad = cargar_modulo("continuidad_prueba", "continuidad/gestor_continuidad.py")
rocketbot = cargar_modulo("rocketbot_prueba", "rocketbot/robot_observabilidad.py")


class RemediadorTests(unittest.TestCase):
    def test_rechaza_servicio_fuera_de_lista(self):
        with (
            patch.object(remediador, "SERVICIO_OBJETIVO", "mysql"),
            patch.object(remediador, "registrar_incidente") as registrar,
        ):
            self.assertFalse(remediador.ejecutar_remediacion())
            registrar.assert_called_once()

    def test_recrea_solo_servicio_permitido(self):
        proceso = Mock(returncode=0, stdout="creado", stderr="")
        with (
            patch.object(remediador.subprocess, "run", return_value=proceso) as ejecutar,
            patch.object(remediador, "registrar_incidente", return_value=True),
        ):
            self.assertTrue(remediador.ejecutar_remediacion())
        comando = ejecutar.call_args.args[0]
        self.assertEqual(comando[-1], "sitio-vigilado")
        self.assertNotIn("shell", ejecutar.call_args.kwargs)


class ContinuidadTests(unittest.TestCase):
    def test_no_remedia_si_principal_esta_disponible(self):
        disponible = continuidad.ResultadoUrl(estado="ok", detalle="URL disponible")
        with (
            patch.object(continuidad, "validar_url_con_reintentos", return_value=disponible),
            patch.object(continuidad, "ejecutar_remediacion") as remediar,
            patch.object(continuidad, "registrar_incidente"),
            patch.object(continuidad, "guardar_evidencia", return_value=continuidad.RAIZ / "evidencia.json"),
        ):
            self.assertEqual(continuidad.ejecutar_continuidad(), 0)
            remediar.assert_not_called()

    def test_activa_respaldo_si_remediacion_no_recupera(self):
        error = continuidad.ResultadoUrl(estado="error", detalle="sin respuesta")
        respaldo = continuidad.ResultadoUrl(estado="ok", detalle="URL disponible")
        with (
            patch.object(
                continuidad,
                "validar_url_con_reintentos",
                side_effect=[error, error, respaldo],
            ),
            patch.object(continuidad, "ejecutar_remediacion", return_value={"estado": "error"}),
            patch.object(continuidad, "activar_sitio_respaldo", return_value={"estado": "ok"}),
            patch.object(continuidad, "registrar_incidente"),
            patch.object(continuidad, "enviar_notificacion_humana", return_value={"estado": "simulada"}),
            patch.object(continuidad, "guardar_evidencia", return_value=continuidad.RAIZ / "evidencia.json"),
            patch.object(continuidad.time, "sleep"),
        ):
            self.assertEqual(continuidad.ejecutar_continuidad(), 0)


class RocketbotTests(unittest.TestCase):
    def test_finalizar_paso_conserva_trazabilidad(self):
        paso = rocketbot.crear_paso("prueba")
        resultado = rocketbot.finalizar_paso(paso, "ok", "completo", {"codigo": 0})
        self.assertEqual(resultado["estado"], "ok")
        self.assertEqual(resultado["codigo"], 0)
        self.assertIsNotNone(resultado["fin"])

    def test_espera_readiness_en_lugar_de_pausa_fija(self):
        error = {"estado": "error"}
        listo = {"estado": "ok"}
        with (
            patch.object(rocketbot, "validar_api", side_effect=[error, listo]) as validar,
            patch.object(rocketbot.time, "sleep") as esperar,
        ):
            resultado = rocketbot.esperar_api(intentos=3, intervalo=0.1)
        self.assertEqual(resultado["estado"], "ok")
        self.assertEqual(resultado["intento"], 2)
        self.assertEqual(validar.call_count, 2)
        esperar.assert_called_once_with(0.1)


if __name__ == "__main__":
    unittest.main()
