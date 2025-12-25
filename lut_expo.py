# export_lut_to_csv.py
import pickle
import csv

with open("calibration_lut.pkl", "rb") as f:
    lut = pickle.load(f)

with open("calibration_lut_export.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Wavelength_nm", "My_Value", "Ref_Value"])
    for w in sorted(lut.keys()):
        my_vals = lut[w]['my']
        ref_vals = lut[w]['ref']
        for i in range(len(my_vals)):
            writer.writerow([w, my_vals[i], ref_vals[i]])

print("✅ LUT exportada a calibration_lut_export.csv")