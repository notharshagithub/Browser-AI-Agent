import os
import json
import base64
import logging
import io
import time
from openai import OpenAI
from PIL import Image
import agent.config as config

logger = logging.getLogger("agent.llm_client")

class LLMClient:
    """Wraps OpenAI-compatible API calls (xAI / Groq) for agent decision-making."""
    
    def __init__(self):
        self.api_key = config.XAI_API_KEY
        self.base_url = config.XAI_API_BASE
        self.model = config.XAI_MODEL
        
        if not self.api_key:
            raise ValueError("XAI_API_KEY is not set in environment or .env file.")
            
        logger.info(f"Initializing LLMClient pointing to base_url={self.base_url} with model={self.model}")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Determine if the model is vision-capable.
        # Standard Groq models (like llama-3.3-70b-versatile, qwen/qwen3-32b) are text-only.
        # Multimodal models (like grok-2-vision-1212) are vision-capable.
        # We can look for "vision" or "grok" or toggle this manually.
        self.is_vision_model = "vision" in self.model.lower() or "grok-2" in self.model.lower()

    def resize_and_encode_image(self, image_path: str, max_size: int = 800) -> str:
        """Resizes screenshot if it exceeds max_size to control token usage/cost, then encodes to base64."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                    
                width, height = img.size
                if width > max_size or height > max_size:
                    if width > height:
                        new_width = max_size
                        new_height = int(height * (max_size / width))
                    else:
                        new_height = max_size
                        new_width = int(width * (max_size / height))
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized screenshot from {width}x{height} to {new_width}x{new_height}")
                
                buffered = io.BytesIO()
                # Save as JPEG with compressed quality (80)
                img.save(buffered, format="JPEG", quality=80)
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to resize/encode image {image_path}: {e}")
            # Fallback to raw base64 encoding if resizing fails
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

    def query(self, system_prompt: str, conversation_history: list, latest_screenshot_path: str = None, interactive_elements: list = None, tools: list = None) -> tuple:
        """Sends the payload to the LLM (xAI / Groq) and returns (reasoning, tool_calls, text_content).
        
        Manages the history compactor to strip previous screenshots, keeping only the latest one.
        """
        # Prepare the list of messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Copy and compact history (remove images from all older messages)
        compacted_history = []
        for msg in conversation_history:
            msg_copy = dict(msg)
            # If there's content as a list (e.g. vision format), check if we should compact it
            if isinstance(msg_copy.get("content"), list):
                # Extract only text parts for older history
                text_parts = [item["text"] for item in msg_copy["content"] if item.get("type") == "text"]
                msg_copy["content"] = "\n".join(text_parts)
            compacted_history.append(msg_copy)
            
        messages.extend(compacted_history)
        
        # Construct the latest user message
        prompt_text = "Here is the current state of the page."
        if interactive_elements:
            prompt_text += "\n\nAvailable interactive elements on the page:\n"
            for el in interactive_elements:
                tag_desc = el['tag']
                if el.get('type') and el['type'] != 'text':
                    tag_desc += f" (type: {el['type']})"
                prompt_text += (
                    f"- ID: {el['id']} | Tag: {tag_desc} | Label: '{el['label']}' "
                    f"| Placeholder: '{el['placeholder']}' | Selector: '{el['selector']}' "
                    f"| Coordinates: ({el['x']}, {el['y']})\n"
                )
        else:
            prompt_text += "\nNo interactive elements extracted."
            
        # Compile content. If it's a vision model, we attach the base64 screenshot.
        if latest_screenshot_path and self.is_vision_model:
            try:
                base64_image = self.resize_and_encode_image(latest_screenshot_path)
                user_content = [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            except Exception as e:
                logger.error(f"Image encoding error, falling back to text: {e}")
                user_content = prompt_text
        else:
            # Text-only mode
            if latest_screenshot_path:
                prompt_text += f"\n(Screenshot taken and saved locally as context: {os.path.basename(latest_screenshot_path)})"
            user_content = prompt_text
            
        # Append latest perception state
        messages.append({"role": "user", "content": user_content})
        
        # Call API with retry logic
        attempts = 3
        last_exception = None
        
        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"Sending request to LLM (Attempt {attempt}/{attempts})")
                
                # Check model/tools compatibility
                # Standard tools format is supported
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1 # Low temperature for agent actions precision
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                    
                completion = self.client.chat.completions.create(**kwargs)
                
                response_message = completion.choices[0].message
                tool_calls = response_message.tool_calls
                text_content = response_message.content or ""
                
                logger.info("Successfully received LLM response.")
                if text_content:
                    logger.debug(f"LLM content: {text_content}")
                if tool_calls:
                    logger.info(f"LLM proposed tool calls: {[tc.function.name for tc in tool_calls]}")
                    
                return text_content, tool_calls
                
            except Exception as e:
                logger.warning(f"API call attempt {attempt} failed: {str(e)}")
                last_exception = e
                # Wait before retry with simple exponential backoff
                time.sleep(2 * attempt)
                
        logger.error("All LLM API call attempts failed.")
        raise last_exception
