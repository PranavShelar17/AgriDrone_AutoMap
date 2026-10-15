# Diagnostic Interpretation Limitations & Agronomic Safeguards

## 1. Principles of Responsible Remote Sensing
A core tenet of AgriDrone AutoMap is **scientific transparency**. Remote sensing spectral indices (such as NDVI, NDRE, GNDVI, and SAVI) measure electromagnetic radiation reflected by surface targets. They do not directly measure chemical pathogens, specific fungal infections, or final crop harvest bushels.

---

## 2. Explicitly Prohibited Claims
AgriDrone AutoMap **strictly prohibits and excludes** automated claims of the following nature without laboratory tissue testing or field scouting:
- ❌ *"The crop has fungal blight or bacterial wilt."*
- ❌ *"This field will yield 140 bushels per acre."*
- ❌ *"The farmer must apply 50 kg of urea or specific synthetic fertilizer."*
- ❌ *"Low index values definitively prove nitrogen deficiency."*
- ❌ *"The crop is 100% healthy because the average NDVI is high."*

---

## 3. Confounding Environmental & Physical Factors
Vegetation index values are subject to numerous physical variables that agronomists and farmers must consider:

1. **Soil Background Interference**:
   - In sparse, early-stage crops (canopy cover $< 30\%$), bright or dark soils alter red and NIR reflection. SAVI with $L=0.5$ is recommended in emergence stages to dampen soil background noise.
2. **Atmospheric and Solar Illumination Variations**:
   - Uncalibrated RGB imagery (8-bit JPEG/TIFF without downwelling light sensors or radiometric calibration targets) varies with cloud cover, sun angle, and time of day.
3. **Canopy Architecture & Bidirectional Reflectance (BRDF)**:
   - Erectophile (upright leaf) crops vs. planophile (broad flat leaf) crops reflect sunlight differently even at identical chlorophyll concentrations.
4. **Water Stress vs. Nutrient Deficiency**:
   - Drought stress, soil compaction, salinity, nematode damage, and root rots can all produce identical drops in vegetative greenness and chlorophyll absorption.

---

## 4. Analytical Guardrails Implemented in Phase 8
1. **Telemetry Warnings**: If valid coverage is $< 80\%$, an explicit warning indicates high masked/NoData proportion.
2. **Radiometric Calibrations Notes**: If derived from 8-bit digital numbers, warnings notify the user that absolute values cannot be compared across different flight dates with differing lighting.
3. **Mandatory Ground-Truthing Disclaimer**: Displayed prominently on Page 4 and Page 5:
   > *"Vegetation indices measure canopy greenness, reflectance, and chlorophyll absorption, not direct crop disease. Variations in index values may be caused by soil background, canopy architecture, shadowing, irrigation, or growth stage. Ground-truthing is required before taking agronomic action."*
