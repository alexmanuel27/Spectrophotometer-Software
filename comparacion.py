import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import os

# === CONFIGURACIÓN ===
# === CONFIGURACIÓN ===
ruta_csv = "/home/alex/Descargas/Espectros_CSV/espectro_20250922_135759_33.csv"

# Verificar que el archivo exista
if not os.path.exists(ruta_csv):
    print(f"❌ Archivo no encontrado: {ruta_csv}")
    print("Verifica que:")
    print("  1. El archivo existe")
    print("  2. La ruta está escrita correctamente")
    print("  3. El nombre del archivo es exacto (incluyendo mayúsculas)")
    exit(1)

print(f"✅ Archivo cargado: {ruta_csv}")

# Longitudes de onda del AS7265x
longitudes_onda = [
    410, 435, 460, 485, 510, 535,
    560, 585, 610, 645, 680, 705,
    730, 760, 810, 860, 900, 940
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

# === CARGAR TU MEDICIÓN ===
try:
    df = pd.read_csv(ruta_csv)
    intensidades_reales = df['Intensity_uW_per_cm2'].values
except Exception as e:
    print(f"❌ Error leyendo el CSV: {e}")
    exit(1)

# Verificar que tenga 18 valores
if len(intensidades_reales) != 18:
    print(f"⚠️  El archivo tiene {len(intensidades_reales)} puntos, se esperaban 18.")
    exit(1)

# === GENERAR ESPECTRO TÍPICO HALÓGENO (modelo físico aproximado) ===
temperatura = 3000  # K, temperatura de color típica de halógeno 12V
h = 6.626e-34   # J·s
c = 2.998e8     # m/s
k = 1.381e-23   # J/K

def planck(wavelength_nm, T):
    """Devuelve irradiancia espectral en W/m²/nm"""
    wavelength = wavelength_nm * 1e-9
    exponent = h * c / (wavelength * k * T)
    radiance = (2 * h * c**2 / wavelength**5) / (np.exp(exponent) - 1)
    return radiance * 1e-7  # Aproximación a µW/cm²/nm

espectro_halogeno = np.array([planck(w, temperatura) for w in longitudes_onda])

# Normalizar ambos espectros para comparar forma (no magnitud absoluta)
intensidades_norm = intensidades_reales / np.max(intensidades_reales)
halogeno_norm = espectro_halogeno / np.max(espectro_halogeno)

# === GRÁFICA ===
plt.figure(figsize=(12, 7))

# Tu medición (puntos con color real)
plt.scatter(longitudes_onda, intensidades_norm, c=colores, s=100, edgecolors='black',
            linewidth=1.2, label='Tu medición (normalizada)', zorder=5)

# Curva halógeno (línea suave)
plt.plot(longitudes_onda, halogeno_norm, 'o-', color='orange', alpha=0.8, linewidth=2,
         label=f'Espectro halógeno 3000K (teórico)', markersize=4)

plt.xlabel('Longitud de onda (nm)', fontsize=12)
plt.ylabel('Intensidad (normalizada)', fontsize=12)
plt.title('Comparación: Tu Medición vs. Espectro Halógeno Típico', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.xlim(400, 960)
plt.ylim(0, 1.1)
plt.legend(fontsize=10)
plt.tight_layout()

# Mostrar gráfica
plt.show()

# === RESUMEN EN CONSOLA ===
print("\n📊 Comparación completada:")
print(f"Archivo cargado: {os.path.basename(ruta_csv)}")
print(f"Rango medido: {min(intensidades_reales):.2f} – {max(intensidades_reales):.2f} µW/cm²")
print("La curva naranja es el espectro esperado para una lámpara halógena.")
print("Los puntos coloreados son tus datos reales (normalizados).")