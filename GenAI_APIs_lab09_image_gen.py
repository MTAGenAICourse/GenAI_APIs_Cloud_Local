"""
Lab 09 - Create: text to image with a local Stable Diffusion model (Text2ImagePipeline).

Run:
    python GenAI_APIs_lab09_image_gen.py ./stable-diffusion-v1-5-int8-ov "starry night over Jaffa port"
Writes image.bmp (512x512). Exercise: voice-to-image - transcribe a spoken prompt with
Lab 07 (Whisper), then render it here.
"""
import argparse
from PIL import Image
import openvino_genai

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_dir')
    parser.add_argument('prompt')
    args = parser.parse_args()
    
    device = 'CPU'  # GPU, NPU can be used as well
    pipe = openvino_genai.Text2ImagePipeline(args.model_dir, device)
    
    # Generate image from text prompt only (no reference image for Text2ImagePipeline)
    image_tensor = pipe.generate(
        prompt=args.prompt,
        width=512,
        height=512,
        num_inference_steps=20
    )

    image = Image.fromarray(image_tensor.data[0])
    image.save("image.bmp")

# Call to main function
if '__main__' == __name__:
    main()

#python GenAI_APIs_lab09_image_gen.py ./dreamlike_anime_1_0_ov/FP16 "Cartoonize the person in the refernce image with a dreamy anime style, vibrant colors, and a whimsical background"
#python GenAI_APIs_lab09_image_gen.py ./dreamlike_anime_1_0_ov/FP16 "cyberpunk cityscape like Tokyo New York with tall buildings at dusk golden hour cinematic lighting"
#python GenAI_APIs_lab09_image_gen.py ./dreamlike_anime_1_0_ov/FP16 "dessert landscape post thunder with focus on the especially starry sky including full moon at dusk golden hour cinematic lighting"
#python GenAI_APIs_lab09_image_gen.py ./dreamlike_anime_1_0_ov/FP16 "Starry night with full moon post  cinematic lighting"