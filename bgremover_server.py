#!/usr/bin/env python3
"""
bgremover_server.py
===================
Entry point for BGRemover's HTTP server mode.

Modos de arranque
-----------------
  dev   Flask dev server  — recarga automática, errores detallados.
                            Solo para desarrollo en localhost.
  local Flask sin debug   — sin recarga, sin stack traces expuestos.
                            Para pruebas locales o intranet.
  prod  Waitress WSGI     — multi-hilo, apto para producción en Windows.
                            Recomendado cuando otros servicios consumen la API.

Uso
---
    python bgremover_server.py [--mode MODE] [--host HOST] [--port PORT]
                               [--model MODEL] [--threads N]

Endpoints
---------
    POST /api/v1/remove-bg   Procesa una imagen (multipart/form-data).
    GET  /api/v1/health      Liveness probe.
    GET  /api/v1/models      Lista de modelos disponibles.

Ejemplo rápido (curl)
---------------------
    curl -X POST http://localhost:5000/api/v1/remove-bg ^
         -F "image=@foto.jpg" ^
         -F "threshold=20"    ^
         --output resultado.png
"""

import argparse
import sys

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MODES = ("dev", "local", "prod")
DEFAULT_MODE    = "local"
DEFAULT_HOST    = "127.0.0.1"
DEFAULT_PORT    = 5000
DEFAULT_MODEL   = "isnet-general-use"
DEFAULT_THREADS = 4   # solo relevante en modo prod (Waitress)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bgremover-server",
        description="BGRemover — servidor HTTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default=DEFAULT_MODE,
        help=(
            "Modo de arranque: "
            "dev (Flask debug), "
            "local (Flask sin debug), "
            "prod (Waitress WSGI)  "
            f"[default: {DEFAULT_MODE}]"
        ),
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        metavar="HOST",
        help=f"Interfaz de escucha (default: {DEFAULT_HOST}; usa 0.0.0.0 para red local)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Puerto TCP (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="MODEL",
        help=f"Modelo de IA a cargar (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        metavar="N",
        help=f"Hilos Waitress en modo prod (default: {DEFAULT_THREADS})",
    )
    return parser


# ---------------------------------------------------------------------------
# Runners — uno por modo (SRP: cada función sabe cómo arrancar su servidor)
# ---------------------------------------------------------------------------

def _run_dev(app, host: str, port: int) -> None:
    """Flask dev server: recarga automática, errores detallados en pantalla."""
    print("  [ADVERTENCIA] Modo dev — NO usar en produccion")
    app.run(host=host, port=port, debug=True)


def _run_local(app, host: str, port: int) -> None:
    """Flask sin debug: estable para pruebas locales, un hilo."""
    app.run(host=host, port=port, debug=False)


def _run_prod(app, host: str, port: int, threads: int) -> None:
    """Waitress WSGI: multi-hilo, apto para produccion en Windows."""
    try:
        from waitress import serve
    except ImportError:
        print("[ERROR] Waitress no esta instalado.")
        print("        Ejecuta:  pip install waitress")
        sys.exit(1)

    print(f"  Hilos Waitress : {threads}")
    serve(app, host=host, port=port, threads=threads)


_RUNNERS = {
    "dev":   _run_dev,
    "local": _run_local,
    "prod":  _run_prod,
}


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def _print_banner(mode: str, host: str, port: int, model: str) -> None:
    base_url = f"http://{host}:{port}"
    print("=" * 58)
    print("  BGRemover Server")
    print("=" * 58)
    print(f"  Modo  : {mode.upper()}")
    print(f"  Host  : {host}")
    print(f"  Puerto: {port}")
    print(f"  Modelo: {model}")
    print("-" * 58)
    print(f"  POST  {base_url}/api/v1/remove-bg")
    print(f"  GET   {base_url}/api/v1/health")
    print(f"  GET   {base_url}/api/v1/models")
    print("=" * 58)
    print("  Cargando modelo de IA — el primer inicio puede tardar...")
    print()


def main() -> None:
    args = _build_parser().parse_args()
    _print_banner(args.mode, args.host, args.port, args.model)

    try:
        from server import create_app
    except ImportError as exc:
        print(f"[ERROR] No se pudo importar el paquete server: {exc}")
        print("        Asegurate de instalar Flask:  pip install flask")
        sys.exit(1)

    app = create_app(model_name=args.model)
    runner = _RUNNERS[args.mode]

    if args.mode == "prod":
        runner(app, args.host, args.port, args.threads)
    else:
        runner(app, args.host, args.port)


if __name__ == "__main__":
    main()
