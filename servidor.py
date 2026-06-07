"""
PFO 3 - Sistema Distribuido (Cliente-Servidor)
------------------------------------------------------------
Servidor TCP que recibe tareas por socket, las encola y las reparte entre
un pool de hilos worker. Cada worker toma una tarea de la cola, la procesa
(simulando un tiempo de cómputo variable) y devuelve el resultado al cliente
que la originó, indicando qué worker la atendió.

Arquitectura interna:
    cliente --socket--> servidor --cola(Queue)--> [Worker-1 .. Worker-N]
                                                       |
                                                       +--> respuesta al cliente
"""

import socket
import threading
import queue
import time
import random
from datetime import datetime


# ─────────────────────────────────────────────
# MÓDULO DE CONFIGURACIÓN
# ─────────────────────────────────────────────

HOST = "localhost"          # escucha en todas las interfaces (apto detrás de balanceador)
PUERTO = 5000             # puerto del servidor de recepción
CANTIDAD_WORKERS = 4      # tamaño del pool de hilos
DELAY_MIN = 0.4           # tiempo mínimo simulado de procesamiento (seg)
DELAY_MAX = 1.3           # tiempo máximo simulado de procesamiento (seg)

# Cola compartida entre el hilo que recibe y los workers que procesan.
cola_de_tareas = queue.Queue()


# ─────────────────────────────────────────────
# MÓDULO DE PROCESAMIENTO
# ─────────────────────────────────────────────

def procesar_tarea(contenido: str) -> dict:
    demora = round(random.uniform(DELAY_MIN, DELAY_MAX), 2)
    time.sleep(demora)

    palabras = len(contenido.split())
    caracteres = len(contenido)

    return {
        "transformado": contenido.upper(),
        "palabras": palabras,
        "caracteres": caracteres,
        "demora": demora,
    }


# ─────────────────────────────────────────────
# MÓDULO DE WORKERS (POOL DE HILOS)
# ─────────────────────────────────────────────

def worker(nombre: str) -> None:
    while True:
        item = cola_de_tareas.get()
        if item is None:                 # señal de apagado
            cola_de_tareas.task_done()
            break

        cliente_socket, direccion, num_tarea, contenido, lock = item
        print(f"[{nombre}] tomó tarea #{num_tarea} de {direccion} -> '{contenido}'")

        resultado = procesar_tarea(contenido)
        hora = datetime.now().strftime("%H:%M:%S")

        respuesta = (
            f"#{num_tarea} [{nombre} {hora}] "
            f"'{contenido}' => {resultado['transformado']} "
            f"({resultado['palabras']} palabras, {resultado['caracteres']} car., "
            f"{resultado['demora']}s)\n"
        )

        try:
            with lock:
                cliente_socket.sendall(respuesta.encode("utf-8"))
        except socket.error:
            pass
        finally:
            cola_de_tareas.task_done()


def iniciar_pool(cantidad: int = CANTIDAD_WORKERS) -> None:
    for i in range(cantidad):
        hilo = threading.Thread(target=worker, args=(f"Worker-{i + 1}",), daemon=True)
        hilo.start()
    print(f"[SERVIDOR] Pool de {cantidad} workers iniciado")


# ─────────────────────────────────────────────
# MÓDULO DE SOCKET DEL SERVIDOR
# ─────────────────────────────────────────────

def inicializar_socket(host: str = HOST, puerto: int = PUERTO) -> socket.socket:
    """Crea, configura y deja escuchando el socket del servidor."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, puerto))
        server.listen()
        print(f"[SERVIDOR] Escuchando en {host}:{puerto}")
        return server
    except socket.error as e:
        raise RuntimeError(f"[SERVIDOR] No se pudo inicializar el socket: {e}")


# ─────────────────────────────────────────────
# MÓDULO DE MANEJO DE CLIENTES
# ─────────────────────────────────────────────

def manejar_cliente(cliente_socket: socket.socket, direccion: tuple) -> None:

    print(f"[SERVIDOR] Cliente conectado desde {direccion}")
    lock = threading.Lock()
    contador = 0
    try:
        archivo = cliente_socket.makefile("r", encoding="utf-8")
        for linea in archivo:
            tarea = linea.strip()
            if not tarea:
                continue
            contador += 1
            print(f"[SERVIDOR] Recibida tarea #{contador} de {direccion}: '{tarea}'")
            cola_de_tareas.put((cliente_socket, direccion, contador, tarea, lock))
        print(f"[SERVIDOR] Cliente {direccion} terminó de enviar tareas")
    except socket.error as e:
        print(f"[SERVIDOR] Error en la conexión con {direccion}: {e}")
    finally:
        cola_de_tareas.join()
        cliente_socket.close()
        print(f"[SERVIDOR] Conexión con {direccion} cerrada")


# ─────────────────────────────────────────────
# INICIAR LA COMUNICACIÓN
# ─────────────────────────────────────────────

def iniciar_comunicacion() -> None:
    iniciar_pool()

    try:
        servidor_socket = inicializar_socket()
        servidor_socket.settimeout(1.0)
    except RuntimeError as e:
        print(e)
        return

    print("[SERVIDOR] Esperando conexiones... (Ctrl+C para detener)")

    try:
        while True:
            try:
                cliente_socket, direccion = servidor_socket.accept()
                hilo = threading.Thread(
                    target=manejar_cliente,
                    args=(cliente_socket, direccion),
                    daemon=True,
                )
                hilo.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Apagando...")
    finally:
        for _ in range(CANTIDAD_WORKERS):
            cola_de_tareas.put(None)
        servidor_socket.close()
        print("[SERVIDOR] Socket cerrado")


# ─────────────────────────────────────────────
# EJECUTAR EL SERVIDOR
# ─────────────────────────────────────────────

if __name__ == "__main__":
    iniciar_comunicacion()
