Here’s a concise, production-ready guide for using Gemini 2.5 Flash Image in Python, focused on clarity, correctness, and quick iteration.

1. Install and setup

- Install requirements:

pip install google-genai pillow

- Set your API key securely in environment (don’t hardcode it in code):

macOS/Linux:export GEMINI_API_KEY="YOUR_KEY"

Windows (PowerShell):$env:GEMINI_API_KEY="YOUR_KEY"

2. Basic: text-to-image

Generates an image from a text prompt and saves it to disk.# filename: generate_text_to_image.py

import os

from google import genai

def main():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise RuntimeError("GEMINI_API_KEY is not set in environment")

    client = genai.Client(api_key=api_key)

    prompt = (

        "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"

    )

    response = client.models.generate_content(

        model="gemini-2.5-flash-image",

        contents=[prompt],

    )

    # The response may contain text parts (explanations) and image parts

    image_saved = False

    for part in response.parts:

        if getattr(part, "inline_data", None):

            image = part.as_image()  # returns a PIL.Image

            image.save("generated_image.png")

            image_saved = True

        elif getattr(part, "text", None):

            print("Model text:", part.text)

    if image_saved:

        print("Saved: generated_image.png")

    else:

        print("No image returned. Check prompt or config.")

if __name__ == "__main__":

    main()

3. Image editing: text + image input

Provide an input image and a text instruction to edit or compose.# filename: edit_image_with_text.py

import os

from google import genai

from PIL import Image

def main():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    prompt = (

        "Create a picture of my cat eating a nano-banana in a fancy restaurant under the Gemini constellation"

    )

    input_path = "path/to/cat_image.png"

    base_image = Image.open(input_path)

    response = client.models.generate_content(

        model="gemini-2.5-flash-image",

        contents=[prompt, base_image],

    )

    image_saved = False

    for part in response.parts:

        if getattr(part, "inline_data", None):

            edited = part.as_image()

            edited.save("edited_cat.png")

            image_saved = True

        elif getattr(part, "text", None):

            print("Model text:", part.text)

    print("Saved: edited_cat.png" if image_saved else "No image returned.")

if __name__ == "__main__":

    main()

4. Optional configs: image-only output and aspect ratio

Configure output to return only images and set aspect ratio.# filename: generate_with_config.py

import os

from google import genai

from google.genai import types

def main():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    prompt = "High-resolution studio-lit product shot of a matte black ceramic coffee mug on polished concrete. Square image."

    response = client.models.generate_content(

        model="gemini-2.5-flash-image",

        contents=[prompt],

        config=types.GenerateContentConfig(

            response_modalities=["Image"],

            image_config=types.ImageConfig(

                aspect_ratio="16:9",

            ),

        ),

    )

    image_saved = False

    for part in response.parts:

        if getattr(part, "inline_data", None):

            img = part.as_image()

            img.save("product_16x9.png")

            image_saved = True

    print("Saved: product_16x9.png" if image_saved else "No image returned.")

if __name__ == "__main__":

    main()

5. Common patterns and tips

- Multiple images in: pass them in order with your text instruction to compose or transfer style:

response = client.models.generate_content(

    model="gemini-2.5-flash-image",

    contents=[image1, image2, "Place the dress from image1 onto the person in image2. Outdoor lighting."],

)

- Response parts: iterate and check both ‎⁠part.text⁠ (explanations) and ‎⁠part.inline_data⁠ (image bytes). Use ‎⁠part.as_image()⁠ to get a PIL Image.

- Aspect ratios and sizes:

 ▫ Defaults to square (1:1) if no input image.

 ▫ Set via ‎⁠image_config.aspect_ratio⁠ (examples: “1:1”, “16:9”, “9:16”, etc.) per docs.

- High-fidelity text rendering: specify the exact text, font style (descriptive), and layout in your prompt for best results.

- Iterative refinement: make follow-up calls with new prompts referring to the previous output and your desired changes.

- Watermark: all generated images include a SynthID watermark.

6. Minimal Flask endpoint (generate image from prompt)

Quick API you can call from a React/Vite or Next.js frontend.# filename: app.py

from flask import Flask, request, jsonify, send_file

import os

import tempfile

from google import genai

from google.genai import types

app = Flask(__name__)

def get_client():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise RuntimeError("GEMINI_API_KEY is not set")

    return genai.Client(api_key=api_key)

@app.post("/generate-image")

def generate_image():

    data = request.get_json(force=True)

    prompt = data.get("prompt")

    aspect_ratio = data.get("aspectRatio")  # optional, e.g. "16:9"

    image_only = data.get("imageOnly", True)

    if not prompt:

        return jsonify({"error": "prompt is required"}), 400

    client = get_client()

    config = types.GenerateContentConfig()

    if image_only:

        config.response_modalities = ["Image"]

    if aspect_ratio:

        config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)

    response = client.models.generate_content(

        model="gemini-2.5-flash-image",

        contents=[prompt],

        config=config,

    )

    for part in response.parts:

        if getattr(part, "inline_data", None):

            img = part.as_image()

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

            img.save(tmp.name)

            return send_file(tmp.name, mimetype="image/png")

    # If no image returned, surface any text

    messages = [p.text for p in response.parts if getattr(p, "text", None)]

    return jsonify({"error": "no_image_returned", "messages": messages}), 422

if __name__ == "__main__":

    app.run(debug=True, port=5001)

7. Security and reliability notes

- Never hardcode API keys in source. Use environment variables or a secrets manager.

- Validate user inputs (prompt length, aspect ratio values).

- Rate limiting and timeouts: wrap calls and handle exceptions to prevent backend hangs.

- Content policy: ensure you respect Prohibited Use Policies and have rights to any images you upload.

- Logging: avoid logging raw images or sensitive prompts in production.

Assumptions:

- You’re using the official google-genai Python SDK per the docs.

- PIL (Pillow) is acceptable for image handling.

- Basic local testing environment; adapt paths and deployment settings as needed.