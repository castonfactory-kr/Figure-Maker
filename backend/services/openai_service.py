import base64
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
openai_client = OpenAI(
    api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
    base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
)


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower()
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, "status_code") and exception.status_code == 429)
    )


CHARACTER_STYLES = {
    "sd_character": {
        "name": "SD Character (Chibi)",
        "prompt_prefix": "Transform this person into an adorable SD (super-deformed) chibi anime character with big expressive eyes, small body with large head ratio, cute cartoon proportions, maintaining their key facial features and hairstyle",
    },
    "anime": {
        "name": "Anime Style",
        "prompt_prefix": "Transform this person into a beautiful anime character with smooth cel-shaded style, expressive anime eyes, detailed hair, maintaining their facial features and essence",
    },
    "semi_realistic": {
        "name": "Semi-Realistic",
        "prompt_prefix": "Transform this person into a semi-realistic stylized character like a high-quality 3D animation character (Pixar/Disney style), with slightly exaggerated but realistic proportions, maintaining their key features",
    },
    "pixel_art": {
        "name": "Pixel Art",
        "prompt_prefix": "Transform this person into a charming pixel art character sprite, 16-bit retro game style, with recognizable features simplified into pixel form",
    },
    "cartoon": {
        "name": "Cartoon Style",
        "prompt_prefix": "Transform this person into a fun cartoon character with exaggerated expressions, bold outlines, vibrant colors, maintaining their distinctive features",
    }
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def transform_to_character(image_bytes: bytes, style: str = "sd_character") -> bytes:
    style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["sd_character"])
    
    prompt = f"{style_config['prompt_prefix']}. Create a high-quality character illustration suitable for figure production. The character should be expressive, detailed, and have a clean design with clear outlines. Include a white or simple gradient background."
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(image_bytes)
        tmp_path = tmp_file.name
    
    try:
        with open(tmp_path, "rb") as image_file:
            response = openai_client.images.edit(
                model="gpt-image-1",
                image=[image_file],
                prompt=prompt,
                size="1024x1024"
            )
        
        image_base64 = response.data[0].b64_json or ""
        return base64.b64decode(image_base64)
    finally:
        os.unlink(tmp_path)


def get_available_styles() -> dict:
    return {k: v["name"] for k, v in CHARACTER_STYLES.items()}
