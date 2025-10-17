import serial
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from matplotlib.widgets import Button

# === SELECT SERIAL PORT WITH GUI ===
def select_port_gui():
    root = tk.Tk()
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Select Serial Port")
    top.geometry("400x250")

    label = ttk.Label(top, text="Choose the sensor port:", font=("Helvetica", 12))
    label.pack(pady=10)

    def list_ports():
        possible = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
        available = []
        for p in possible:
            try:
                s = serial.Serial(p)
                s.close()
                available.append(p)
            except (OSError, serial.SerialException):
                pass
        if not available:
            available = ["/dev/ttyUSB0"]
        return available

    ports = list_ports()
    selected_port = tk.StringVar(value=ports[0] if ports else "/dev/ttyUSB0")

    combo = ttk.Combobox(top, textvariable=selected_port, values=ports, state="readonly", width=30, font=("Helvetica", 11))
    combo.pack(pady=10)

    port = None

    def accept():
        nonlocal port
        port = selected_port.get()
        top.destroy()

    btn_frame = ttk.Frame(top)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Cancel", command=top.destroy).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="OK", command=accept).pack(side=tk.LEFT, padx=5)

    top.grab_set()
    top.focus_set()
    top.wait_window()
    root.destroy()
    return port

# === RUN PORT SELECTION ===
try:
    port = select_port_gui()
    if not port:
        print("❌ No port selected.")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

baud_rate = 115200
timeout = 2

# === SAVE FOLDERS ===
base_folder = os.path.expanduser("~/Descargas")
csv_folder = os.path.join(base_folder, "Spectra_Absorbance_CSV")
png_folder = os.path.join(base_folder, "Spectra_Absorbance_PNG")

os.makedirs(csv_folder, exist_ok=True)
os.makedirs(png_folder, exist_ok=True)

# === EXACT WAVELENGTHS (AS7265x) ===
wavelengths = [
    410, 435, 460, 485, 510, 535,
    560, 585, 610, 645, 680, 705,
    730, 760, 810, 860, 900, 940
]

# === SERIAL CONNECTION ===
try:
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    print(f"🔌 Connected to {port} at {baud_rate} bps")
except Exception as e:
    print(f"❌ Error opening serial port: {e}")
    exit(1)

# === SYSTEM STATE ===
reference = None       # I₀
sample_intensity = None # I
absorbance_values = None
transmittance_percent = None
count = 0

# === HELPER FUNCTIONS ===
def clear_buffer():
    while ser.in_waiting > 0:
        ser.readline()
    plt.pause(0.1)

def wait_for_confirmation(expected_text, timeout=5):
    start_time = datetime.now()
    while (datetime.now() - start_time).seconds < timeout:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if expected_text in line:
                    return True
                if line.count(',') == 17:  # Ignore spectral data
                    continue
            except:
                continue
        plt.pause(0.1)
    return False

def turn_on_light():
    clear_buffer()
    ser.write(b'LIGHT_ON\n')
    success = wait_for_confirmation("LUZ_ENCENDIDA", timeout=5)
    if not success:
        print("❌ Timeout waiting for 'LUZ_ENCENDIDA'")
    return success

def turn_off_light():
    ser.write(b'LIGHT_OFF\n')
    success = wait_for_confirmation("LUZ_APAGADA", timeout=5)
    if not success:
        print("⚠️ Timeout waiting for 'LUZ_APAGADA'")
    return success

def read_spectrum():
    for _ in range(5):
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            parts = [x.strip() for x in line.split(',') if x.strip()]
            if len(parts) == 18 and 'A,B,C' not in line and ',' in line:
                try:
                    values = list(map(float, parts))
                    if len(values) == 18:
                        return np.array(values)
                except:
                    continue
        plt.pause(0.1)
    return None

def take_n_readings_average(n=10):
    readings = []
    for i in range(n):
        vals = read_spectrum()
        if vals is not None:
            readings.append(vals)
        else:
            print(f"⚠️ Reading #{i+1} failed.")
        plt.pause(0.1)
    return np.mean(readings, axis=0) if readings else None

# === PLOT SETUP ===
plt.ion()
fig, (ax_abs, ax_T) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [1, 1]})

line_abs, = ax_abs.plot(wavelengths, [0]*18, 'o-', color='purple', linewidth=2, markersize=6)
ax_abs.set_ylabel('Absorbance (a.u.)')
ax_abs.set_title('Absorbance')
ax_abs.grid(True, alpha=0.3)
ax_abs.set_xlim(400, 960)
ax_abs.set_ylim(-0.1, 2.0)

line_T, = ax_T.plot(wavelengths, [0]*18, 's-', color='green', linewidth=2, markersize=5)
ax_T.set_xlabel('Wavelength (nm)')
ax_T.set_ylabel('Transmittance (%)')
ax_T.set_title('Transmittance')
ax_T.grid(True, alpha=0.3)
ax_T.set_xlim(400, 960)
ax_T.set_ylim(0, 100)

fig.suptitle('🔬 Spectrophotometer - Dual View', fontsize=14, fontweight='bold')

# === BUTTONS (repositioned below plots) ===
ax_btn_ref = plt.axes([0.1, 0.02, 0.2, 0.05])     # [left, bottom, width, height]
btn_ref = Button(ax_btn_ref, 'Take Reference', color='skyblue')

ax_btn_sample = plt.axes([0.35, 0.02, 0.2, 0.05])
btn_sample = Button(ax_btn_sample, 'Measure Sample', color='lightgreen')

ax_btn_save = plt.axes([0.6, 0.02, 0.2, 0.05])
btn_save = Button(ax_btn_save, 'Save', color='gold')

# === BUTTON CALLBACKS ===
def take_reference(event):
    global reference, absorbance_values, transmittance_percent
    absorbance_values = None
    transmittance_percent = None
    line_abs.set_ydata([0]*18)
    line_T.set_ydata([0]*18)
    ax_abs.set_ylim(-0.1, 2.0)
    ax_T.set_ylim(0, 100)
    fig.canvas.draw_idle()

    print("\n🔍 TAKING REFERENCE (BLANK)")
    if not turn_on_light():
        print("❌ Failed to turn on light.")
        return

    plt.pause(5.0)

    print("📊 Taking 10 averaged readings...")
    ref_vals = take_n_readings_average(10)

    if not turn_off_light():
        print("⚠️ Failed to turn off light.")

    if ref_vals is None:
        print("❌ No valid readings obtained.")
        return

    if np.max(ref_vals) < 10:
        print("⚠️ WARNING: Very low signal. Is the LED on?")
        return

    reference = ref_vals
    print("✅ Reference saved.")
    ax_abs.set_title('Reference ready. Measure sample.', color='green')
    fig.canvas.draw_idle()

def measure_sample(event):
    global sample_intensity, absorbance_values, transmittance_percent
    if reference is None:
        print("⚠️ Take a reference first.")
        return

    print("\n🔍 MEASURING SAMPLE")
    if not turn_on_light():
        print("❌ Failed to turn on light.")
        return

    plt.pause(5.0)

    print("📊 Taking 10 averaged readings...")
    samp_vals = take_n_readings_average(10)

    if not turn_off_light():
        print("⚠️ Failed to turn off light.")

    if samp_vals is None:
        print("❌ No valid readings obtained.")
        return

    if np.max(samp_vals) < 10:
        print("⚠️ WARNING: Low sample signal.")
        return

    sample_intensity = samp_vals
    I0 = reference
    I = sample_intensity

    I_safe = np.maximum(I, 1e-6)
    I0_safe = np.maximum(I0, I_safe)

    A = np.log10(I0_safe / I_safe)
    A = np.clip(A, 0, None)

    T_percent = (I_safe / I0_safe) * 100
    T_percent = np.clip(T_percent, 0, 100)

    line_abs.set_ydata(A)
    ax_abs.set_ylim(0, max(A)*1.2 or 2.0)
    ax_abs.relim(visible_only=True)
    ax_abs.autoscale_view(scalex=False, scaley=True)
    ax_abs.set_title('Absorbance calculated', color='darkred')

    line_T.set_ydata(T_percent)
    ax_T.set_ylim(0, 100)
    ax_T.relim(visible_only=True)
    ax_T.autoscale_view(scalex=False, scaley=True)
    ax_T.set_title('Transmittance calculated', color='darkgreen')

    absorbance_values = A
    transmittance_percent = T_percent
    fig.canvas.draw_idle()
    print("✅ Data updated.")

def save_data(event):
    global absorbance_values, transmittance_percent, reference, sample_intensity, count
    if absorbance_values is None or sample_intensity is None or reference is None:
        messagebox.showerror("Error", "No data to save.")
        return

    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("Name", "Sample name:")
    root.destroy()

    if not name or name.strip() == "":
        messagebox.showinfo("Cancelled", "Save cancelled.")
        return
    name = name.strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}"
    count += 1

    I0 = reference
    I = sample_intensity

    A = np.log10(np.maximum(I0, 1e-6) / np.maximum(I, 1e-6))
    A = np.clip(A, 0, None)
    T_percent = (I / I0) * 100
    T_percent = np.clip(T_percent, 0, 100)

    # --- SAVE CSV ---
    csv_path = os.path.join(csv_folder, f"{filename}.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Wavelength_nm',
            'I0_Reference_uW_per_cm2',
            'I_Sample_uW_per_cm2',
            'Absorbance',
            'Transmittance_%'
        ])
        for w, i0, i_samp, a, t in zip(wavelengths, I0, I, A, T_percent):
            writer.writerow([w, round(i0, 4), round(i_samp, 4), round(a, 4), round(t, 2)])
    print(f"✅ CSV saved: {csv_path}")

    # --- SAVE CLEAN PNG ---
    png_path = os.path.join(png_folder, f"{filename}.png")
    fig_save, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(wavelengths, A, 'o-', color='purple', linewidth=2, markersize=6)
    ax1.set_ylabel('Absorbance')
    ax1.set_title(f'Absorbance - {name}')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(400, 960)
    ax1.set_ylim(0, max(A)*1.2 or 2.0)

    ax2.plot(wavelengths, T_percent, 's-', color='green', linewidth=2, markersize=5)
    ax2.set_xlabel('Wavelength (nm)')
    ax2.set_ylabel('Transmittance (%)')
    ax2.set_title('Transmittance')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(400, 960)
    ax2.set_ylim(0, 100)

    fig_save.tight_layout()
    fig_save.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close(fig_save)
    print(f"🎨 PNG saved: {png_path}")
    messagebox.showinfo("Success", f"Sample '{name}' saved successfully.")

# Assign callbacks
btn_ref.on_clicked(take_reference)
btn_sample.on_clicked(measure_sample)
btn_save.on_clicked(save_data)

# === CONSOLE INSTRUCTIONS ===
print("\n🟢 STEPS:")
print("1. Place the blank (solvent) and click 'Take Reference'")
print("2. Replace with sample and click 'Measure Sample'")
print("3. Click 'Save' and enter a name in the popup\n")

# === MAIN LOOP ===
try:
    while True:
        plt.pause(0.1)
except KeyboardInterrupt:
    pass
finally:
    turn_off_light()
    ser.close()
    plt.ioff()
    plt.show()
    print(f"🎯 Last measurement shown. Total samples saved: {count}")