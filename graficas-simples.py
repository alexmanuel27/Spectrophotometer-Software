import serial
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime
import os

# === CONFIGURACIÓN DEL PUERTO SERIAL ===
puerto = '/dev/ttyUSB0'   # Cambia si es /dev/ttyUSB0
baud_rate = 115200
timeout = 2

# === CARPETAS DE GUARDADO ===
carpeta_base = os.path.expanduser("~/Descargas")
carpeta_csv = os.path.join(carpeta_base, "Espectros_Simple_CSV")
carpeta_png = os.path.join(carpeta_base, "Espectros_Simple_PNG")

os.makedirs(carpeta_csv, exist_ok=True)
os.makedirs(carpeta_png, exist_ok=True)

# === LONGITUDES DE ONDA EXACTAS (de tu código Arduino) ===
longitudes_onda = [
    410, 435, 460, 485, 510, 535,  # UV - Azul-Verde
    560, 585, 610, 645, 680, 705,  # Amarillo - Rojo
    730, 760, 810, 860, 900, 940   # Rojo profundo - IR
]

nombres = [
    "UV 410nm", "435nm", "460nm", "485nm", "510nm", "535nm",
    "560nm", "585nm", "610nm", "645nm", "680nm", "705nm",
    "730nm", "760nm", "810nm", "860nm", "900nm", "940nm"
]

# === FUNCIÓN: Color RGB aproximado por λ ===
def rgb_from_wavelength(nm):
    if nm >= 380 and nm < 440:
        R = -(nm - 440) / (440 - 380)
        G = 0.0
        B = 1.0
    elif nm < 490:
        R = 0.0
        G = (nm - 440) / (490 - 440)
        B = 1.0
    elif nm < 510:
        R = 0.0
        G = 1.0
        B = -(nm - 510) / (510 - 490)
    elif nm < 580:
        R = (nm - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif nm < 645:
        R = 1.0
        G = -(nm - 645) / (645 - 580)
        B = 0.0
    else:
        R = 0.5 + (940 - nm) / (940 - 645) * 0.5
        G = 0.5 + (940 - nm) / (940 - 645) * 0.5
        B = 0.5 + (940 - nm) / (940 - 645) * 0.5

    attenuation = 1.0
    if nm < 420:
        attenuation = 0.3 + 0.7 * (nm - 380) / 40
    elif nm > 700:
        attenuation = 0.3 + 0.7 * (800 - nm) / 100 if nm < 800 else 0.3

    return (
        max(0, min(1, R * attenuation)),
        max(0, min(1, G * attenuation)),
        max(0, min(1, B * attenuation))
    )

colores = [rgb_from_wavelength(w) for w in longitudes_onda]

# === CONEXIÓN SERIAL ===
try:
    ser = serial.Serial(puerto, baud_rate, timeout=timeout)
    print(f"🔌 Conectado a {puerto} a {baud_rate} bps")
except Exception as e:
    print(f"❌ Error al abrir puerto serial: {e}")
    exit(1)

# === CONFIGURACIÓN DE LA GRÁFICA ===
plt.ion()
fig, ax = plt.subplots(figsize=(14, 7))

# Gráfica con posiciones exactas en X
scatter = ax.scatter(longitudes_onda, [0]*18, c=colores, s=150, edgecolors='black', linewidth=1.5)
line, = ax.plot(longitudes_onda, [0]*18, '-', color='gray', alpha=0.5, linewidth=2, zorder=1)

ax.set_xlabel('Longitud de onda (nm)', fontsize=12)
ax.set_ylabel('Intensidad espectral (µW/cm²)', fontsize=12)
ax.set_title('🔬 Espectro Preciso - AS7265x (Puntos en λ exactas)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_xlim(400, 960)
ax.set_ylim(0, 20)  # Se ajustará dinámicamente
ax.margins(x=0.02)

# Marcar solo algunas longitudes de onda en el eje X para evitar saturación
xticks = [410, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 940]
ax.set_xticks(xticks)
ax.tick_params(axis='x', rotation=0)

print("📡 Esperando datos del sensor... (Ctrl+C para salir)")

# === BUCLE PRINCIPAL ===
contador = 0
try:
    while True:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()

            if ',' not in linea or 'A,B,C' in linea or len(linea) < 10:
                continue

            try:
                valores = list(map(float, [x for x in linea.split(',') if x.strip()]))

                if len(valores) == 18:
                    contador += 1
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"espectro_{timestamp}_{contador}"

                    # --- GUARDAR CSV ---
                    ruta_csv = os.path.join(carpeta_csv, f"{nombre_archivo}.csv")
                    with open(ruta_csv, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Wavelength_nm', 'Intensity_uW_per_cm2', 'Label'])
                        for w, v, n in zip(longitudes_onda, valores, nombres):
                            writer.writerow([w, v, n])
                    print(f"✅ CSV guardado: {ruta_csv}")

                    # --- ACTUALIZAR GRÁFICA ---
                    line.set_ydata(valores)
                    scatter.set_offsets(np.column_stack((longitudes_onda, valores)))
                    max_val = max(valores) * 1.1
                    ax.set_ylim(0, max(max_val, 20))
                    plt.draw()
                    plt.pause(0.05)

                    # --- GUARDAR PNG ---
                    ruta_png = os.path.join(carpeta_png, f"{nombre_archivo}.png")
                    fig.savefig(ruta_png, dpi=150, bbox_inches='tight', facecolor='white')
                    print(f"🎨 PNG guardado: {ruta_png}")

            except Exception as e:
                print(f"⚠️ Error procesando datos: {e}")
                continue

except KeyboardInterrupt:
    print("\n\n🛑 Detenido por usuario.")
finally:
    ser.close()
    plt.ioff()
    plt.show()
    print(f"🎯 Último espectro mostrado. Total lecturas guardadas: {contador}")