import os
import numpy as np
import csv
import matplotlib.pyplot as plt
import pickle

# === Load calibration ===
CALIB_FILE = None
CALIB_DATA = None

if os.path.exists("calibration_lut.pkl"):
    with open("calibration_lut.pkl", "rb") as f:
        CALIB_DATA = pickle.load(f)
    CALIB_FILE = "calibration_lut.pkl"
elif os.path.exists("calibration_factor.npy"):
    CALIB_DATA = np.load("calibration_factor.npy")
    CALIB_FILE = "calibration_factor.npy"
else:
    print("❌ Calibration file not found.")
    exit(1)

# === Ask for files ===
my_csv = input("Enter your 18-point CSV file: ").strip()
ref_csv = input("Enter the commercial reference CSV file: ").strip()

if not os.path.exists(my_csv) or not os.path.exists(ref_csv):
    print("❌ One or both files do not exist.")
    exit(1)

# === Load your CSV (18 points) ===
wavelengths = []
A_raw = []
with open(my_csv, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        wavelengths.append(int(row['Wavelength_nm']))
        A_raw.append(float(row['Absorbance_Calibrated']))
wavelengths = np.array(wavelengths)
A_raw = np.array(A_raw)

# === Load commercial reference (continuous spectrum) ===
ref_w, ref_a = [], []
with open(ref_csv, 'r') as f:
    lines = f.readlines()
for line in lines[7:]:
    parts = line.strip().split(',')
    if len(parts) >= 2:
        try:
            w = float(parts[0])
            a = float(parts[1])
            ref_w.append(w)
            ref_a.append(a)
        except:
            continue
ref_w = np.array(ref_w)
ref_a = np.array(ref_a)

# === Apply calibration ===
if CALIB_FILE == "calibration_factor.npy":
    A_cal = A_raw * CALIB_DATA
elif CALIB_FILE == "calibration_lut.pkl":
    A_cal = np.array([
        np.interp(A_raw[i], CALIB_DATA[w]['my'], CALIB_DATA[w]['ref'])
        if w in CALIB_DATA and len(CALIB_DATA[w]['my']) > 0
        else A_raw[i]
        for i, w in enumerate(wavelengths)
    ])

# === Save calibrated CSV ===
base, _ = os.path.splitext(my_csv)
calibrated_csv = f"{base}_calibrated.csv"
with open(calibrated_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Wavelength_nm', 'Absorbance_Raw', 'Absorbance_Calibrated'])
    for w, a_r, a_c in zip(wavelengths, A_raw, A_cal):
        writer.writerow([w, round(a_r, 6), round(a_c, 6)])
print(f"✅ Calibrated CSV: {calibrated_csv}")

# === Generate comparison plot ===
plt.figure(figsize=(10, 6))

# Commercial reference (continuous line)
plt.plot(ref_w, ref_a, '-', color='black', linewidth=1.5, label='Commercial Reference')

# Your uncalibrated spectrum (circles + line)
plt.plot(wavelengths, A_raw, 'o-', color='blue', linewidth=2, markersize=6, label='Uncalibrated')

# Your calibrated spectrum (circles + line)
plt.plot(wavelengths, A_cal, 'o-', color='red', linewidth=2, markersize=6, label='Calibrated')

plt.xlabel('Wavelength (nm)', fontsize=12)
plt.ylabel('Absorbance', fontsize=12)
plt.title('Spectrum Comparison', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(loc='upper right')
plt.xlim(400, 960)
plt.tight_layout()

# Save PNG
calibrated_png = f"{base}_comparison.png"
plt.savefig(calibrated_png, dpi=300, facecolor='white', bbox_inches='tight')
plt.close()
print(f"🎨 PNG saved: {calibrated_png}")

print("\n✅ Done!")