import os
import numpy as np
import csv
from scipy.interpolate import interp1d

# === CONFIGURACIÓN ===
DATA_DIR = "calibration_data"

# Tus 18 longitudes de onda exactas (AS7265x)
MY_WAVELENGTHS = [
    410, 435, 460, 485, 510, 535,
    560, 585, 610, 645, 680, 705,
    730, 760, 810, 860, 900, 940
]

def load_my_absorbance(filename):
    """Carga absorbancia de tu CSV (con encabezado estándar)"""
    absorbance = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            absorbance.append(float(row['Absorbance']))
    return np.array(absorbance)

def load_ref_spectrum(filename):
    """
    Carga el archivo comercial con el formato específico:
    - 6 líneas de metadatos
    - Línea 7: encabezado con espacios
    - Datos desde la línea 8
    """
    wavelengths = []
    absorbance = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Saltar las primeras 6 líneas y la línea vacía
    data_lines = lines[7:]  # Desde la línea 8 en adelante
    
    for line in data_lines:
        if line.strip() == "":
            continue
        parts = line.strip().split(',')
        if len(parts) >= 2:
            try:
                w = float(parts[0])
                a = float(parts[1])
                wavelengths.append(w)
                absorbance.append(a)
            except ValueError:
                continue
    
    return np.array(wavelengths), np.array(absorbance)

def main():
    print("🔍 Iniciando calibración espectral...")
    all_factors = []

    for i in range(1, 5):
        print(f"\n--- Muestra {i} ---")
        my_file = os.path.join(DATA_DIR, f"mi_muestra_{i}.csv")
        ref_file = os.path.join(DATA_DIR, f"ref_muestra_{i}.csv")
        
        if not os.path.exists(my_file):
            print(f"❌ No se encontró: {my_file}")
            continue
        if not os.path.exists(ref_file):
            print(f"❌ No se encontró: {ref_file}")
            continue
        
        # Cargar tu absorbancia
        try:
            A_my = load_my_absorbance(my_file)
            if len(A_my) != 18:
                print(f"⚠️  Formato incorrecto en {my_file}")
                continue
        except Exception as e:
            print(f"⚠️  Error en {my_file}: {e}")
            continue
        
        # Cargar espectro comercial
        try:
            λ_ref, A_ref = load_ref_spectrum(ref_file)
            if len(λ_ref) == 0:
                print(f"⚠️  No se leyeron datos en {ref_file}")
                continue
        except Exception as e:
            print(f"⚠️  Error al leer {ref_file}: {e}")
            continue
        
        # Interpolar en tus longitudes de onda
        try:
            f_interp = interp1d(λ_ref, A_ref, kind='linear', fill_value="extrapolate")
            A_ref_interp = f_interp(MY_WAVELENGTHS)
        except Exception as e:
            print(f"⚠️  Error interpolando: {e}")
            continue
        
        # Calcular factor de corrección (solo donde A_my > 0.1)
        factors = np.ones(18)
        valid = (A_my > 0.1) & (A_ref_interp > -0.5)  # Permitir valores ligeramente negativos
        factors[valid] = A_ref_interp[valid] / np.maximum(A_my[valid], 1e-6)
        
        all_factors.append(factors)
        print(f"✅ Muestra {i} procesada.")

    if not all_factors:
        print("\n❌ No se procesó ninguna muestra.")
        return
    
    # Calcular factor final (mediana)
    correction_factor = np.median(np.array(all_factors), axis=0)
    
    # Guardar
    np.save("calibration_factor.npy", correction_factor)
    
    print("\n" + "="*50)
    print("✅ CALIBRACIÓN COMPLETADA")
    print("="*50)
    for w, f in zip(MY_WAVELENGTHS, correction_factor):
        print(f"  {w} nm: x{f:.3f}")
    print(f"\n💾 Guardado en: calibration_factor.npy")

if __name__ == "__main__":
    main()