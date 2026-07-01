import os
import numpy as np

base_dir = "/link/to/your/folder/aerial_image_dataset"

x_path = os.path.join(base_dir, "X_input")
y_path = os.path.join(base_dir, "Y_normalized_aerial")

os.makedirs(x_path, exist_ok=True)
os.makedirs(y_path, exist_ok=True)

RESOLUTION = 512
WAVELENGTH = 193.0
SIGMA = 0.85
DX = 3.9
SAMPLES_PER_LAYOUT = 100
TOTAL_LAYOUTS = 5

global_sample_idx = 0
print("🚀 Starting Native NCHW Dataset Generation...")

for layout_type in range(TOTAL_LAYOUTS):
    print(f"🎬 Generating variations for Layout Type {layout_type}...")
    for var_idx in range(SAMPLES_PER_LAYOUT):
        np.random.seed(global_sample_idx)
        mask_2d = np.zeros((RESOLUTION, RESOLUTION), dtype=np.float32)

        # Structure layout geometries
        if layout_type == 0:    # Vertical Grating
            cd, pitch = 24, 32
            offset = (RESOLUTION - (7 * cd + 6 * pitch)) // 2
            for col in range(7):
                x_start = offset + col * (cd + pitch)
                mask_2d[:, x_start : x_start + cd] = 1.0
        elif layout_type == 1:  # Horizontal Grating
            cd, pitch = 24, 32
            offset = (RESOLUTION - (7 * cd + 6 * pitch)) // 2
            for row in range(7):
                y_start = offset + row * (cd + pitch)
                mask_2d[y_start : y_start + cd, :] = 1.0
        elif layout_type == 2:  # Contact Array
            cd, pitch = 24, 32
            offset = (RESOLUTION - (8 * cd + 7 * pitch)) // 2
            for row in range(8):
                for col in range(8):
                    y_start = offset + row * (cd + pitch)
                    x_start = offset + col * (cd + pitch)
                    mask_2d[y_start : y_start + cd, x_start : x_start + cd] = 1.0
        elif layout_type == 3:  # Single Vertical Line
            cd = 32
            start_x = (RESOLUTION - cd) // 2
            mask_2d[:, start_x : start_x + cd] = 1.0
        elif layout_type == 4:  # Single Contact Hole
            cd = 40
            start_pos = (RESOLUTION - cd) // 2
            mask_2d[start_pos : start_pos + cd, start_pos : start_pos + cd] = 1.0

        # Process Optical Variation
        dose = np.random.uniform(22.0, 38.0)
        defocus = np.random.uniform(-45.0, 45.0)
        na = np.random.uniform(0.50, 1.35)

        # Hopkins-Abbe Frequency Mathematics Core
        freq_axis = np.fft.fftfreq(RESOLUTION, d=DX)
        fx, fy = np.meshgrid(freq_axis, freq_axis)
        freq_radius = np.sqrt(fx**2 + fy**2)

        pupil = (freq_radius <= (na / WAVELENGTH)).astype(np.float32)
        wavefront = 0.5 * defocus * (WAVELENGTH**2) * (freq_radius**2)
        phase_aberration = np.exp(1j * (2.0 * np.pi / WAVELENGTH) * wavefront)
        complex_pupil = pupil * phase_aberration

        source_limit = SIGMA * (na / WAVELENGTH)
        source_axis = np.linspace(-source_limit, source_limit, 5)
        aerial_image = np.zeros((RESOLUTION, RESOLUTION), dtype=np.float32)
        nodes = 0

        mask_fft = np.fft.fft2(mask_2d)
        for sx in source_axis:
            for sy in source_axis:
                if np.sqrt(sx**2 + sy**2) <= source_limit:
                    shift_x = int(round(sx / (freq_axis[1] - freq_axis[0])))
                    shift_y = int(round(sy / (freq_axis[1] - freq_axis[0])))
                    shifted_fft = np.roll(np.roll(mask_fft, shift_x, axis=1), shift_y, axis=0)
                    aerial_image += np.abs(np.fft.ifft2(shifted_fft * complex_pupil))**2
                    nodes += 1

        aerial_image /= nodes


        GLOBAL_SCALE = 1.0
        normalized_img = aerial_image / GLOBAL_SCALE
        normalized_img = np.clip(normalized_img, 0, 1)



        # TARGET FORMAT: [Channels, Height, Width] -> [1, 512, 512]
        y_target = np.expand_dims(normalized_img, axis=0)

        # INPUT FORMAT: [Channels, Height, Width] -> [4, 512, 512]
        x_input = np.zeros((4, RESOLUTION, RESOLUTION), dtype=np.float32)
        x_input[0, :, :] = mask_2d
        x_input[1, :, :] = dose / 38.0
        x_input[2, :, :] = defocus / 45.0
        x_input[3, :, :] = na / 1.35

               # =====================================================================
        # 3. SAVE MATRICES DIRECTLY TO CACHE CHANNELS
        # =====================================================================
        np.save(os.path.join(x_path, f"sample_{global_sample_idx}.npy"), x_input)
        np.save(os.path.join(y_path, f"sample_{global_sample_idx}.npy"), normalized_img)

        # Step tracker ahead for subsequent iterations
        global_sample_idx += 1

print(f"\n🎉 DATASET GENERATION COMPLETE!")
print(f"📦 Total samples successfully cached to disk: {global_sample_idx}") 
print(f" -> Inputs saved in: 'aerial_image_dataset/X_input/' [Shape: 512, 512, 4]")
print(f" -> Targets saved in: 'aerial_image_dataset/Y_normalized_aerial/' [Shape: 512, 512, 1]")
print(f"\n🎉 DATASET GENERATION COMPLETE!")
print(f"📦 Total samples successfully backed up permanently to Drive: {global_sample_idx}")
