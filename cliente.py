"""
PFO 3 - Rediseño como Sistema Distribuido (Cliente-Servidor)
------------------------------------------------------------
Cliente que se conecta al servidor por socket, le envía una lista de tareas y luego lee el resultado de cada una, mostrando qué worker
la procesó y las métricas que devolvió.
"""

import socket


# ─────────────────────────────────────────────
# MÓDULO DE CONFIGURACIÓN
# ─────────────────────────────────────────────

HOST = "localhost"
PUERTO = 5000

# Lista de tareas propias de este cliente (distinta a la del enunciado base).
TAREAS = [
    "monitorear el estado del cluster",
    "balancear la carga entrante",
    "registrar las metricas del worker",
    "validar el formato de mensajes",
    "resultados en la base de datos",
    "replicar archivos",
    "encolar las tareas pendientes",
    "notificar al cliente el resultado",
    "auditar tiempos de respuesta",
    "liberar recursos al finalizar",
    "verificar la conexion",
    "generar reporte de procesamiento",
]


# ─────────────────────────────────────────────
# MÓDULO PRINCIPAL
# ─────────────────────────────────────────────

def iniciar_cliente(host: str = HOST, puerto: int = PUERTO) -> None:
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente_socket.connect((host, puerto))
        print(f"[CLIENTE] Conectado al servidor en {host}:{puerto}")
        print(f"[CLIENTE] Se enviarán {len(TAREAS)} tareas.\n")
    except ConnectionRefusedError:
        print(
            f"[CLIENTE] No se pudo conectar a {host}:{puerto}. "
            "¿El servidor está corriendo?"
        )
        return

    try:
        # Envío de todas las tareas.
        for t in TAREAS:
            cliente_socket.sendall((t + "\n").encode("utf-8"))
            print(f"[CLIENTE] envía tarea: {t}")

        # Avisamos que terminamos de enviar (half-close de escritura).
        cliente_socket.shutdown(socket.SHUT_WR)

        # Lectura de los resultados (el orden puede variar según el worker).
        print()
        archivo = cliente_socket.makefile("r", encoding="utf-8")
        for _ in TAREAS:
            resultado = archivo.readline().strip()
            if not resultado:
                break
            print(f"[CLIENTE] resultado: {resultado}")

    except (socket.error, BrokenPipeError) as e:
        print(f"[CLIENTE] Error de conexión: {e}")
    finally:
        cliente_socket.close()
        print("\n Comunicación cerrada")


# ─────────────────────────────────────────────
# EJECUTAR EL CLIENTE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    iniciar_cliente()
