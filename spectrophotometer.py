import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from matplotlib.widgets import Button

# === CARGAR FACTOR DE CORRECCIÓN (si existe) ===
CALIBRATION_FILE = "calibration_factor.npy"
if os.path.exists(CALIBRATION_FILE):
    CORRECTION_FACTOR = np.load(CALIBRATION_FILE)
    print(f"✅ Factor de corrección cargado desde {CALIBRATION_FILE}")
else:
    CORRECTION_FACTOR = np.ones(18)
    print("⚠️  No se encontró archivo de calibración. Usando factor = 1 (sin corrección).")

# === FUNCIÓN DE VALIDACIÓN ===
def lectura_es_valida(valores):
    """
    Valida una lectura del sensor.
    Rechaza si el canal D (485 nm, índice 3) es cero o negativo.
    """
    if valores is None:
        return False
    if len(valores) != 18:
        return False
    return valores[3] > 0  # Canal D (485 nm) debe ser > 0

# === SELECCIÓN DE PUERTO CON TKINTER ===
def select_port_gui():
    root = tk.Tk()
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Select Serial Port")
    top.geometry("400x250")

    label = ttk.Label(top, text="Choose the sensor port:", font=("Helvetica", 12))
    label.pack(pady=10)

    def list_ports():
        ports = []
        for p in serial.tools.list_ports.comports():
            if p.device:
                ports.append(p.device)
        if not ports:
            ports = ['/dev/ttyUSB0', '/dev/ttyACM0']
            if os.name == 'nt':
                ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']
        return ports

    available_ports = list_ports()
    selected_port = tk.StringVar(value=available_ports[0] if available_ports else "/dev/ttyUSB0")

    combo = ttk.Combobox(top, textvariable=selected_port, values=available_ports, state="readonly", width=30, font=("Helvetica", 11))
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

# === EJECUTAR SELECCIÓN DE PUERTO ===
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

# === CARPETAS DE GUARDADO ===
base_folder = os.path.expanduser("~/Descargas")
csv_folder = os.path.join(base_folder, "Spectra_Absorbance_CSV")
png_folder = os.path.join(base_folder, "Spectra_Absorbance_PNG")

os.makedirs(csv_folder, exist_ok=True)
os.makedirs(png_folder, exist_ok=True)

# === LONGITUDES DE ONDA EXACTAS (AS7265x) ===
wavelengths = [
    410, 435, 460, 485, 510, 535,
    560, 585, 610, 645, 680, 705,
    730, 760, 810, 860, 900, 940
]

# === CONEXIÓN SERIAL ===
try:
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    print(f"🔌 Connected to {port} at {baud_rate} bps")
except Exception as e:
    print(f"❌ Error opening serial port: {e}")
    exit(1)

# === ESTADO DEL SISTEMA ===
reference = None
sample_intensity = None
absorbance_values = None
absorbance_std = None
transmittance_percent = None
count = 0

# === FUNCIONES AUXILIARES ===
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
                if line.count(',') == 17:
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

# === CONFIGURACIÓN DE LA GRÁFICA DOBLE ===
plt.ion()
fig, (ax_abs, ax_T) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [1, 1]})

line_abs, = ax_abs.plot(wavelengths, [0]*18, 'o-', color='purple', linewidth=2, markersize=6, zorder=5)
errorbars = ax_abs.errorbar(wavelengths, [0]*18, yerr=[0]*18, fmt='none', ecolor='red', capsize=3, capthick=1, elinewidth=1, zorder=4)
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

fig.suptitle('🔬 Spectrophotometer - Calibrated', fontsize=14, fontweight='bold')

# === BOTONES ===
ax_btn_ref = plt.axes([0.1, 0.02, 0.2, 0.05])
btn_ref = Button(ax_btn_ref, 'Take Reference', color='skyblue')

ax_btn_sample = plt.axes([0.35, 0.02, 0.2, 0.05])
btn_sample = Button(ax_btn_sample, 'Measure Sample', color='lightgreen')

ax_btn_save = plt.axes([0.6, 0.02, 0.2, 0.05])
btn_save = Button(ax_btn_save, 'Save', color='gold')

ax_btn_error = plt.axes([0.85, 0.02, 0.13, 0.05])
btn_error = Button(ax_btn_error, 'Measure Error', color='orange')

# === FUNCIONES DE BOTONES ===
def take_reference(event):
    global reference, absorbance_values, absorbance_std, transmittance_percent
    absorbance_values = None
    absorbance_std = None
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

    print("📊 Taking valid readings (target: 10)...")
    valid_readings = []
    attempt = 0
    while len(valid_readings) < 10 and attempt < 50:
        vals = read_spectrum()
        if lectura_es_valida(vals):
            valid_readings.append(vals)
            print(f"  ✅ Reading {len(valid_readings)}/10")
        attempt += 1
        plt.pause(0.1)

    if not turn_off_light():
        print("⚠️ Failed to turn off light.")

    if len(valid_readings) < 10:
        print(f"⚠️ Only got {len(valid_readings)} valid readings.")
        if len(valid_readings) == 0:
            print("❌ No valid reference.")
            return

    reference = np.mean(valid_readings, axis=0)
    print("✅ Reference saved.")
    ax_abs.set_title('Reference ready. Measure sample.', color='green')
    fig.canvas.draw_idle()

def measure_sample(event):
    global sample_intensity, absorbance_values, absorbance_std, transmittance_percent
    if reference is None:
        print("⚠️ Take a reference first.")
        return

    print("\n🔍 MEASURING SAMPLE")
    if not turn_on_light():
        print("❌ Failed to turn on light.")
        return

    plt.pause(5.0)

    print("📊 Taking valid readings (target: 10)...")
    valid_readings = []
    attempt = 0
    while len(valid_readings) < 10 and attempt < 50:
        vals = read_spectrum()
        if lectura_es_valida(vals):
            valid_readings.append(vals)
            print(f"  ✅ Reading {len(valid_readings)}/10")
        attempt += 1
        plt.pause(0.1)

    if not turn_off_light():
        print("⚠️ Failed to turn off light.")

    if len(valid_readings) < 10:
        print(f"⚠️ Only got {len(valid_readings)} valid readings.")
        if len(valid_readings) == 0:
            print("❌ No valid sample.")
            return

    sample_intensity = np.mean(valid_readings, axis=0)
    I0 = reference
    I = sample_intensity

    I_safe = np.maximum(I, 1e-6)
    I0_safe = np.maximum(I0, I_safe)

    A_raw = np.log10(I0_safe / I_safe)
    A_raw = np.clip(A_raw, 0, None)
    A_corrected = A_raw * CORRECTION_FACTOR

    T_percent = (I_safe / I0_safe) * 100
    T_percent = np.clip(T_percent, 0, 100)

    absorbance_values = A_corrected
    absorbance_std = None
    transmittance_percent = T_percent

    line_abs.set_ydata(A_corrected)
    ax_abs.set_ylim(0, max(A_corrected)*1.2 or 2.0)
    ax_abs.relim(visible_only=True)
    ax_abs.autoscale_view(scalex=False, scaley=True)
    ax_abs.set_title('Absorbance (calibrated)', color='darkred')

    line_T.set_ydata(T_percent)
    ax_T.set_ylim(0, 100)
    ax_T.relim(visible_only=True)
    ax_T.autoscale_view(scalex=False, scaley=True)
    ax_T.set_title('Transmittance', color='darkgreen')

    global errorbars
    errorbars.remove()
    errorbars = ax_abs.errorbar(wavelengths, A_corrected, yerr=[0]*18, fmt='none', ecolor='red', capsize=3, capthick=1, elinewidth=1, zorder=4)

    fig.canvas.draw_idle()
    print("✅ Data updated (with calibration).")

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

    A_raw = np.log10(np.maximum(I0, 1e-6) / np.maximum(I, 1e-6))
    A_raw = np.clip(A_raw, 0, None)
    A_corrected = A_raw * CORRECTION_FACTOR

    T_percent = (I / I0) * 100
    T_percent = np.clip(T_percent, 0, 100)

    # --- GUARDAR CSV ---
    csv_path = os.path.join(csv_folder, f"{filename}.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Wavelength_nm',
            'I0_Reference_uW_per_cm2',
            'I_Sample_uW_per_cm2',
            'Absorbance_Calibrated',
            'Transmittance_%'
        ])
        for w, i0, i_samp, a, t in zip(wavelengths, I0, I, A_corrected, T_percent):
            writer.writerow([w, round(i0, 4), round(i_samp, 4), round(a, 4), round(t, 2)])
    print(f"✅ CSV saved: {csv_path}")

    # --- GUARDAR PNG LIMPIO ---
    png_path = os.path.join(png_folder, f"{filename}.png")
    fig_save, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(wavelengths, A_corrected, 'o-', color='purple', linewidth=2, markersize=6)
    ax1.set_ylabel('Absorbance (calibrated)')
    ax1.set_title(f'Absorbance - {name}')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(400, 960)
    ax1.set_ylim(0, max(A_corrected)*1.2 or 2.0)

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
    messagebox.showinfo("Success", f"Sample '{name}' saved with calibration.")

def measure_error(event):
    global reference
    if reference is None:
        print("⚠️ First take a reference.")
        messagebox.showwarning("Advertencia", "Primero toma una referencia.")
        return

    print("\n🔍 MEASURING ERROR (100 valid readings)...")
    
    if not turn_on_light():
        print("❌ Failed to turn on light.")
        messagebox.showerror("Error", "No se pudo encender el LED.")
        return

    plt.pause(5.0)

    print("📊 Taking valid readings (target: 100)...")
    all_A_raw = []
    attempt = 0
    while len(all_A_raw) < 100 and attempt < 500:
        I = read_spectrum()
        if lectura_es_valida(I):
            I_safe = np.maximum(I, 1e-6)
            I0_safe = np.maximum(reference, I_safe)
            A_raw = np.log10(I0_safe / I_safe)
            A_raw = np.clip(A_raw, 0, None)
            A_corr = A_raw * CORRECTION_FACTOR
            all_A_raw.append(A_corr)
            if len(all_A_raw) % 20 == 0:
                print(f"  ✅ {len(all_A_raw)}/100")
        attempt += 1
        plt.pause(0.01)

    if not turn_off_light():
        print("⚠️ Failed to turn off light.")

    if len(all_A_raw) < 100:
        print(f"⚠️ Only got {len(all_A_raw)} valid readings.")
        if len(all_A_raw) == 0:
            print("❌ No valid readings.")
            return

    all_A_raw = np.array(all_A_raw)
    mean_A = np.mean(all_A_raw, axis=0)
    std_A = np.std(all_A_raw, axis=0)

    # Guardar CSV especial
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_measurement_{timestamp}"
    csv_path = os.path.join(csv_folder, f"{filename}.csv")

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Wavelength_nm', 'I0_Reference_uW_per_cm2']
        header += [f'Absorbance_Reading_{i+1}' for i in range(100)]
        header += ['Absorbance_Mean', 'Absorbance_Std']
        writer.writerow(header)
        for j in range(18):
            row = [wavelengths[j], round(reference[j], 4)]
            row += [round(all_A_raw[i][j], 4) for i in range(100)]
            row += [round(mean_A[j], 4), round(std_A[j], 4)]
            writer.writerow(row)

    print(f"✅ CSV de error guardado: {csv_path}")
    messagebox.showinfo("Éxito", f"Medición de error guardada:\n{csv_path}")

# Asignar callbacks
btn_ref.on_clicked(take_reference)
btn_sample.on_clicked(measure_sample)
btn_save.on_clicked(save_data)
btn_error.on_clicked(measure_error)

# === INSTRUCCIONES EN CONSOLA ===
print("\n🟢 STEPS:")
print("1. Place the blank (solvent) and click 'Take Reference'")
print("2. Replace with sample and click 'Measure Sample'")
print("3. Click 'Save' to save normally")
print("4. Click 'Measure Error' to take 100 VALID readings with full statistics\n")

# === BUCLE PRINCIPAL ===
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