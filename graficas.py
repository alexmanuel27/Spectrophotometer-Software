import serial
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime
import os
from scipy.signal import savgol_filter  # For smoothing

# === SERIAL PORT CONFIGURATION ===
port = '/dev/ttyACM0'   # Change to '/dev/ttyUSB0' if needed
baud_rate = 115200
timeout = 2

# === SAVE FOLDERS ===
base_folder = os.path.expanduser("~/Downloads")
csv_folder = os.path.join(base_folder, "Spectra_CSV")
png_folder = os.path.join(base_folder, "Spectra_PNG")

os.makedirs(csv_folder, exist_ok=True)
os.makedirs(png_folder, exist_ok=True)

# === EXACT WAVELENGTHS (AS7265x) ===
wavelengths = [
    410, 435, 460, 485, 510, 535,
    560, 585, 610, 645, 680, 705,
    730, 760, 810, 860, 900, 940
]

labels = [
    "UV 410nm", "435nm", "460nm", "485nm", "510nm", "535nm",
    "560nm", "585nm", "610nm", "645nm", "680nm", "705nm",
    "730nm", "760nm", "810nm", "860nm", "900nm", "940nm"
]

# === FUNCTION: Approximate RGB color from wavelength ===
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

colors = [rgb_from_wavelength(w) for w in wavelengths]

# === SERIAL CONNECTION ===
try:
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    print(f"🔌 Connected to {port} at {baud_rate} bps")
except Exception as e:
    print(f"❌ Error opening serial port: {e}")
    exit(1)

# === PLOT CONFIGURATION ===
plt.ion()
fig, ax = plt.subplots(figsize=(14, 7))

scatter = ax.scatter(wavelengths, [0]*18, c=colors, s=150, edgecolors='black', linewidth=1.5)
line, = ax.plot(wavelengths, [0]*18, '-', color='gray', alpha=0.5, linewidth=2, zorder=1)

ax.set_xlabel('Wavelength (nm)', fontsize=12)
ax.set_ylabel('Spectral Intensity (µW/cm²)', fontsize=12)
ax.set_title('🔬 Spectral Reading - AS7265x (Exact λ Positions)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_xlim(400, 960)
ax.set_ylim(0, 20)
ax.margins(x=0.02)

xticks = [410, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 940]
ax.set_xticks(xticks)
ax.tick_params(axis='x', rotation=0)

print("📡 Waiting for sensor data... (Press Ctrl+C to exit)")

# === MAIN LOOP ===
count = 0
try:
    while True:
        if ser.in_waiting > 0:
            line_data = ser.readline().decode('utf-8', errors='ignore').strip()

            if ',' not in line_data or 'A,B,C' in line_data or len(line_data) < 10:
                continue

            try:
                values = list(map(float, [x for x in line_data.split(',') if x.strip()]))

                if len(values) == 18:
                    count += 1
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"spectrum_{timestamp}_{count}"

                    # --- APPLY SAVITZKY-GOLAY FILTER ---
                    try:
                        smoothed = savgol_filter(values, window_length=5, polyorder=2)
                        final_values = np.maximum(smoothed, 0)
                    except Exception as e:
                        print(f"⚠️ Savitzky-Golay error: {e}. Using raw data.")
                        final_values = values

                    # --- SAVE CSV ---
                    csv_path = os.path.join(csv_folder, f"{filename}.csv")
                    with open(csv_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Wavelength_nm', 'Intensity_uW_per_cm2', 'Label'])
                        for w, v, n in zip(wavelengths, final_values, labels):
                            writer.writerow([w, round(v, 4), n])
                    print(f"✅ CSV saved: {csv_path}")

                    # --- UPDATE PLOT ---
                    line.set_ydata(final_values)
                    scatter.set_offsets(np.column_stack((wavelengths, final_values)))
                    max_val = max(final_values) * 1.1
                    ax.set_ylim(0, max(max_val, 20))
                    plt.draw()
                    plt.pause(0.05)

                    # --- SAVE PNG ---
                    png_path = os.path.join(png_folder, f"{filename}.png")
                    fig.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
                    print(f"🎨 PNG saved: {png_path}")

            except Exception as e:
                print(f"⚠️ Data processing error: {e}")
                continue

except KeyboardInterrupt:
    print("\n\n🛑 Stopped by user.")
finally:
    ser.close()
    plt.ioff()
    plt.show()
    print(f"🎯 Final spectrum displayed. Total readings saved: {count}")