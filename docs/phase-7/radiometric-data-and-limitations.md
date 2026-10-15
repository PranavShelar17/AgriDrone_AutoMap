# Radiometric Data, Dynamic Range & Scientific Limitations — Phase 7

## 1. Digital Numbers (DN) vs Surface Reflectance
A common misconception in drone mapping is assuming that pixel numbers directly represent calibrated surface reflectance.

- **Digital Numbers (DN)**: Raw integer values recorded by the camera sensor (e.g., 0–255 for 8-bit, 0–65535 for 16-bit). DNs depend on solar irradiance, sun angle, camera shutter speed, ISO, and atmospheric haze.
- **Surface Reflectance**: The ratio of reflected radiant energy to incoming solar irradiance, standardized between 0.0 (0% reflection) and 1.0 (100% reflection). Achieving true surface reflectance requires a downwelling light sensor (DLS) on the drone and calibrated reflectance panel images taken on the ground before/after the flight.

---

## 2. Dynamic Range Detection in Phase 7
The raster inspection service evaluates the statistical distribution across bands:

1. **`REFLECTANCE_FLOAT`**: Values lie in range $[0.0, 1.05]$. Recognized as standardized surface reflectance.
2. **`DIGITAL_NUMBERS_16BIT`**: Values exceed 255. Identified as uncalibrated 16-bit integers.
3. **`DIGITAL_NUMBERS_8BIT`**: Values range from 0 to 255. Standard consumer camera digital numbers.

---

## 3. Scientific Transparency & Calibration Notes
If a dataset contains uncalibrated Digital Numbers, the engine:
1. Computes the mathematical vegetation formula directly from the available values.
2. Embeds an explicit scientific notice in the product metadata:
   > *"Values appear to be uncalibrated Digital Numbers (DN). Scientific notice: Index formulas are computed from relative digital numbers without surface reflectance normalization. Absolute cross-temporal comparisons between different dates should be interpreted with caution."*
3. Displays this disclosure prominently on Page 3 and in the API responses.

The system **never** blindly normalizes arbitrary pixel values and claims they are calibrated surface reflectance.
