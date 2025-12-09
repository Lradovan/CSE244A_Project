import anthropic
from openai import OpenAI
from google import genai
import os
import time
import base64


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def call_llm(model_name, api_key, prompt, image_path=None):
    """
    Clean generic interface for calling different LLM APIs.
    Correctly handles:
    - GPT (OpenAI)
    - Claude (Anthropic)
    - Gemini
    """

    start = time.time()

    # -------------------------------------------------------------
    # CASE 1 — Image baseline: Only OpenAI *actually supports* Responses+image
    # -------------------------------------------------------------
    if image_path:
        base64_image = encode_image(image_path)

        client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        response = client.responses.create(
            model=model_name,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    ],
                }
            ],
        )
        return response.output_text.strip(), time.time() - start

    # -------------------------------------------------------------
    # CASE 2 — OpenAI GPT text models
    # -------------------------------------------------------------
    if model_name.startswith("gpt"):
        client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        response = client.responses.create(
            model=model_name,
            #reasoning={"effort": "high"},
            input=[{"role": "user", "content": prompt}],
        )
        return response.output_text.strip(), time.time() - start

    # -------------------------------------------------------------
    # CASE 3 — Claude (Anthropic)
    # -------------------------------------------------------------
    if model_name.startswith("claude"):
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096
        )
        return response.content[0].text.strip(), time.time() - start

    # -------------------------------------------------------------
    # CASE 4 — Gemini
    # -------------------------------------------------------------
    if model_name.startswith("gemini"):
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip(), time.time() - start