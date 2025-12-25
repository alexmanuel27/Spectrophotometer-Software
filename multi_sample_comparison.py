import os
import numpy as np
import csv
import matplotlib.pyplot as plt

def load_ref_csv(filename):
    """Carga el CSV del espectrofotómetro comercial (formato Scan_*.csv)."""
    wavelengths = []
    absorbance = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Saltar las primeras 6 líneas de metadatos
    for line in lines[6:]:
        parts = line.strip().split(',')
        if len(parts) < 3:
            continue
        try:
            # Limpiar espacios y encontrar las columnas correctas
            clean_parts = [p.strip() for p in parts if p.strip() != '']
            if len(clean_parts) >= 3:
                w = float(clean_parts[0])
                a = float(clean_parts[1])
                wavelengths.append(w)
                absorbance.append(a)
        except (ValueError, IndexError):
            continue
    return np.array(wavelengths), np.array(absorbance)

def load_18point_csv(filename):
    """Carga tu CSV de 18 puntos."""
    wavelengths = []
    A_cal = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            wavelengths.append(float(row['Wavelength_nm']))
            A_cal.append(float(row['Absorbance_Calibrated']))  # ← Cambiado
    return np.array(wavelengths), np.array(A_cal)

def load_continuous_csv(filename):
    """Carga tu CSV continuo."""
    wavelengths = []
    A_cal = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = float(row['Wavelength_nm'])
            a = float(row['Absorbance_Calibrated'])  # ← Cambiado
            if a >= 0:  # Evitar valores negativos no físicos
                wavelengths.append(w)
                A_cal.append(a)
    return np.array(wavelengths), np.array(A_cal)

def load_chinese_csv(filename, sample_name):
    """Carga el archivo chino y extrae la columna correcta."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Encontrar la línea del encabezado (normalmente la 6ª o 7ª)
    header_line = None
    data_start = None
    for i, line in enumerate(lines):
        if 'Nanometers' in line or 'nm' in line.lower():
            header_line = line
            data_start = i + 1
            break
        if line.replace(',', '').replace('.', '').strip().isdigit():
            # Si no hay encabezado, asume que empieza en la línea 0
            data_start = i
            break
    
    if header_line:
        header = [col.strip() for col in header_line.split(',')]
        try:
            col_index = header.index(sample_name)
        except ValueError:
            print(f"❌ Columna '{sample_name}' no encontrada en el encabezado.")
            print(f"Encabezado: {header}")
            return np.array([]), np.array([])
    else:
        # Si no hay encabezado, asume que la primera columna es Nanometers,
        # y las siguientes son las muestras en orden: grape, green, lemon, rose
        sample_order = ['grape', 'green', 'lemon', 'rose']
        try:
            col_index = sample_order.index(sample_name) + 1  # +1 por la columna de Nanometers
        except ValueError:
            print(f"❌ Muestra '{sample_name}' no está en el orden esperado: {sample_order}")
            return np.array([]), np.array([])
        data_start = 0

    # Leer datos
    wavelengths = []
    absorbance = []
    for line in lines[data_start:]:
        parts = line.strip().split(',')
        if len(parts) <= col_index:
            continue
        try:
            w = float(parts[0])
            a = float(parts[col_index])
            wavelengths.append(w)
            absorbance.append(a)
        except (ValueError, IndexError):
            continue
    return np.array(wavelengths), np.array(absorbance)

def main():
    n = int(input("Number of samples to plot? "))
    samples = []
    
    for i in range(n):
        print(f"\n--- Sample {i+1} ---")
        name = input("Sample name (e.g., 'rose', 'green'): ").strip()
        ref_file = input("Reference CSV (commercial): ").strip()
        point18_file = input("18-point CSV (your sensor): ").strip()
        cont_file = input("Continuous CSV (your sensor): ").strip()
        samples.append({
            'name': name,
            'ref': ref_file,
            '18': point18_file,
            'cont': cont_file
        })
    
    chinese_file = input("\nChinese spectrometer CSV: ").strip()

    # Paleta de colores fija
    colors = ['purple', 'pink', 'purple', 'green', 'red']
    if n > 5:
        for i in range(n - 5):
            colors.append(f'C{i+5}')  # C5, C6, etc.

    # Crear figura en formato 2 filas x (n*2) columnas
    fig, axes = plt.subplots(2, n*2, figsize=(5*n*2, 10))

    for i, sample in enumerate(samples):
        print(f"\nProcessing {sample['name']}...")
        
        # Cargar datos
        λ_ref, A_ref = load_ref_csv(sample['ref'])
        λ_18, A_18 = load_18point_csv(sample['18'])
        λ_cont, A_cont = load_continuous_csv(sample['cont'])
        λ_ch, A_ch = load_chinese_csv(chinese_file, sample['name'])

        # Verificar que los datos se cargaron
        if len(λ_ref) == 0:
            print(f"⚠️ No reference data for {sample['name']}")
            continue
        if len(λ_18) == 0:
            print(f"⚠️ No 18-point data for {sample['name']}")
            continue
        if len(λ_cont) == 0:
            print(f"⚠️ No continuous data for {sample['name']}")
            continue
        if len(λ_ch) == 0:
            print(f"⚠️ No Chinese data for {sample['name']}")
            continue

        color = colors[i]

        # Fila 1: Referencia y 18 puntos
        axes[0][i*2].plot(λ_ref, A_ref, '-', color='black', linewidth=1.5)
        axes[0][i*2].set_title(f"Reference ({sample['name']})")
        axes[0][i*2].set_ylabel("Absorbance")
        axes[0][i*2].grid(True, alpha=0.3)
        axes[0][i*2].set_xlim(400, 960)

        axes[0][i*2 + 1].plot(λ_18, A_18, 'o-', color=color, markersize=5)
        axes[0][i*2 + 1].set_title(f"18-point ({sample['name']})")
        axes[0][i*2 + 1].grid(True, alpha=0.3)
        axes[0][i*2 + 1].set_xlim(400, 960)

        # Fila 2: Continuo y chino
        axes[1][i*2].plot(λ_cont, A_cont, '-', color=color)
        axes[1][i*2].set_title(f"Continuous ({sample['name']})")
        axes[1][i*2].set_ylabel("Absorbance")
        axes[1][i*2].grid(True, alpha=0.3)
        axes[1][i*2].set_xlim(400, 960)

        axes[1][i*2 + 1].plot(λ_ch, A_ch, '-', color=color)
        axes[1][i*2 + 1].set_title(f"Chinese ({sample['name']})")
        axes[1][i*2 + 1].set_xlabel("Wavelength (nm)")
        axes[1][i*2 + 1].grid(True, alpha=0.3)
        axes[1][i*2 + 1].set_xlim(400, 960)

    plt.tight_layout()
    plt.savefig("multi_sample_comparison.png", dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"\n✅ PNG saved: multi_sample_comparison.png")

if __name__ == "__main__":
    main()