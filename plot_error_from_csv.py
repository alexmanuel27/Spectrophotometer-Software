import os
import numpy as np
import matplotlib.pyplot as plt
import csv
import sys

def plot_error_from_csv(csv_path):
    """
    Genera un PNG con la curva de absorbancia promedio y barras de error
    a partir de un CSV generado por 'Measure Error'.
    """
    if not os.path.exists(csv_path):
        print(f"❌ Archivo no encontrado: {csv_path}")
        return

    wavelengths = []
    absorbance_mean = []
    absorbance_std = []

    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Primera línea: encabezados

        # Encontrar índices de las columnas necesarias
        try:
            wl_idx = header.index('Wavelength_nm')
            mean_idx = header.index('Absorbance_Mean')
            std_idx = header.index('Absorbance_Std')
        except ValueError as e:
            print(f"❌ Columna no encontrada en el CSV: {e}")
            return

        # Leer datos
        for row in reader:
            try:
                wl = float(row[wl_idx])
                mean_a = float(row[mean_idx])
                std_a = float(row[std_idx])
                wavelengths.append(wl)
                absorbance_mean.append(mean_a)
                absorbance_std.append(std_a)
            except (ValueError, IndexError):
                continue

    if not wavelengths:
        print("❌ No se leyeron datos válidos del CSV.")
        return

    # Convertir a arrays
    wavelengths = np.array(wavelengths)
    absorbance_mean = np.array(absorbance_mean)
    absorbance_std = np.array(absorbance_std)

    # Crear gráfica
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        wavelengths, absorbance_mean, yerr=absorbance_std,
        fmt='o-', color='purple', ecolor='red', capsize=4, capthick=1.5,
        elinewidth=1.5, markersize=6, linewidth=2
    )
    plt.xlabel('Wavelength (nm)', fontsize=12)
    plt.ylabel('Absorbance (a.u.)', fontsize=12)
    plt.title('Absorbance with Error Bars', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xlim(400, 960)
    plt.ylim(0, max(absorbance_mean + absorbance_std) * 1.2 or 2.0)

    # Guardar PNG
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    png_path = os.path.join(os.path.dirname(csv_path), f"{base_name}_plot.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()

    print(f"✅ Gráfica guardada: {png_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 plot_error_from_csv.py <ruta_al_archivo.csv>")
        print("Ejemplo: python3 plot_error_from_csv.py ~/Descargas/Spectra_Absorbance_CSV/error_measurement_20251020_153045.csv")
    else:
        csv_file = sys.argv[1]
        plot_error_from_csv(csv_file)