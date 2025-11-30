IMAGE_FOLDER_PATH = "/users/json/downloads/limited training data"
OUTPUT_FOLDER_PATH = IMAGE_FOLDER_PATH + "/_segmented"
SAM_PATH = "/Users/json/Developer/src/jasonappah/cv-project/embeddding-based-detection/sam-checkpoints/sam_vit_b_01ec64.pth"
SAM_MODEL_TYPE = "vit_b"
USE_AUTOMATIC_MASK_GENERATOR = True

import os
import cv2
import time
import pickle
import numpy as np
import torch
from segment_anything import SamPredictor, sam_model_registry, SamAutomaticMaskGenerator
sam = sam_model_registry[SAM_MODEL_TYPE](checkpoint=SAM_PATH)

if torch.cuda.is_available():
    print("Using CUDA")
    sam.to(device="cuda")
# elif torch.backends.mps.is_available():
#     print("Using MPS")
#     sam.to(device="mps")



if USE_AUTOMATIC_MASK_GENERATOR:
    mask_generator = SamAutomaticMaskGenerator(sam)
    predictor = None
else:
    predictor = SamPredictor(sam)
    mask_generator = None



for image_path in os.listdir(IMAGE_FOLDER_PATH):
    start_time = time.time()
    print(f"Processing {image_path}")
    if not image_path.endswith((".png", ".jpg", ".jpeg")):
        print(f"Skipping {image_path} because it is not a PNG, JPG, or JPEG file")
        continue

    image = cv2.imread(os.path.join(IMAGE_FOLDER_PATH, image_path))

    if USE_AUTOMATIC_MASK_GENERATOR:
        masks = mask_generator.generate(image)
    else:
        predictor.set_image(image)
        masks, _, _ = predictor.predict("get all tools or tool cases in the image")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    

    # Ensure output folder exists
    os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)

    for idx, mask in enumerate(masks):
        # Write each mask as a pickle file
        mask_path = os.path.join(OUTPUT_FOLDER_PATH, f"{os.path.splitext(image_path)[0]}_mask_{idx}.pkl")
        with open(mask_path, "wb") as f:
            pickle.dump(mask, f)

        # Create masked image: keep only segmented region, set rest to 0
        segmentation = mask["segmentation"]
        segmented_image = np.zeros_like(image)
        segmented_image[segmentation] = image[segmentation]

        # Save the masked image to disk
        base_name = os.path.splitext(image_path)[0]
        output_image_path = os.path.join(OUTPUT_FOLDER_PATH, f"{base_name}_seg_{idx}.png")
        cv2.imwrite(output_image_path, segmented_image)

"""
Observations:
- SAM is guzzling memory like its no one's business... even the base model is heavy on my mac.
- can't use mps due to:
```
TypeError: Cannot convert a MPS Tensor to float64 dtype as the MPS framework doesn't support float64. Please use float32 instead.
```

"""