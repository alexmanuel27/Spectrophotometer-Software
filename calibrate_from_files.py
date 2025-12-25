# calibrate_from_files.py
import os
import numpy as np
import csv
import pickle

CALIBRATION_DIR = "calibration_data"
WAVELENGTHS = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940]

def load_my_abs(filename):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        return [float(row['Absorbance_Calibrated']) for row in reader]

def load_ref_abs(filename):
    λ_ref = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines[7:]:
        parts = line.strip().split(',')
        if len(parts) >= 2:
            try:
                w = round(float(parts[0]))
                a = float(parts[1])
                λ_ref[w] = a
            except:
                continue
    return [λ_ref.get(w, np.nan) for w in WAVELENGTHS]

def main():
    lut = {w: {'my': [], 'ref': []} for w in WAVELENGTHS}

    for i in range(1, 8):
        try:
            my_vals = load_my_abs(os.path.join(CALIBRATION_DIR, f"mi_muestra_{i}.csv"))
            ref_vals = load_ref_abs(os.path.join(CALIBRATION_DIR, f"ref_muestra_{i}.csv"))
            for j, w in enumerate(WAVELENGTHS):
                if not np.isnan(ref_vals[j]) and my_vals[j] > 0:
                    lut[w]['my'].append(my_vals[j])
                    lut[w]['ref'].append(ref_vals[j])
        except Exception as e:
            print(f"⚠️ Error en muestra {i}: {e}")

    # Ordenar por valor medido
    for w in WAVELENGTHS:
        if lut[w]['my']:
            idx = np.argsort(lut[w]['my'])
            lut[w]['my'] = np.array(lut[w]['my'])[idx]
            lut[w]['ref'] = np.array(lut[w]['ref'])[idx]

    # Guardar
    with open("calibration_lut.pkl", "wb") as f:
        pickle.dump(lut, f)
    print("✅ LUT guardada en calibration_lut.pkl")

if __name__ == "__main__":
    main()