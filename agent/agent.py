import os
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import agent.config as config
from agent.tools import PlaywrightBrowserManager, GROK_TOOLS
from agent.llm_client import LLMClient

# Setup logging configuration
# Configure logger to save verbose output to file, but keep terminal output clean
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Clear any default handlers to avoid duplicates
root_logger.handlers = []

# File Handler - saves everything (INFO and above) with a 1MB rotation threshold and 3 backups
file_handler = RotatingFileHandler(
    os.path.join(config.LOGS_DIR, "agent.log"),
    encoding="utf-8",
    maxBytes=1024 * 1024, # 1 MB limit
    backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
root_logger.addHandler(file_handler)

# Console Handler - only prints warnings and errors to the screen
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
root_logger.addHandler(console_handler)

logger = logging.getLogger("agent.core")

class WebsiteAutomationAgent:
    """Persistent Gen-AI agent that maintains browser sessions across consecutive tasks."""
    
    def __init__(self):
        logger.info("Initializing Website Automation Agent")
        config.print_config()
        
        self.browser_manager = PlaywrightBrowserManager(
            screenshots_dir=config.SCREENSHOTS_DIR,
            logs_dir=config.LOGS_DIR
        )
        self.llm_client = LLMClient()
        
        self.conversation_history = []
        self.step_count = 0
        self.task_completed = False
        self.session_active = False
        self.current_url = None # Track current website URL
        
        # Build tools list for Grok including the completion tool
        self.tools = list(GROK_TOOLS)
        self.tools.append({
            "type": "function",
            "function": {
                "name": "task_complete",
                "description": "Signals that the website automation task is complete and details the success summary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A summary of what was completed."
                        }
                    },
                    "required": ["summary"]
                }
            }
        })

    def start_session(self, headless: bool = False) -> bool:
        """Launches the browser context and page, preserving it between consecutive tasks."""
        logger.info(f"Starting persistent browser session (headless={headless})")
        res = self.browser_manager.open_browser(headless=headless)
        if res["success"]:
            self.session_active = True
            return True
        return False

    @property
    def is_session_healthy(self) -> bool:
        """Checks if the browser session is active, open, and healthy."""
        if not self.session_active:
            return False
        if not self.browser_manager.page:
            return False
        try:
            if self.browser_manager.page.is_closed():
                return False
            if not self.browser_manager.browser or not self.browser_manager.browser.is_connected():
                return False
            return True
        except Exception:
            return False

    def navigate_to(self, url: str) -> bool:
        """Navigates to target website link and clears previous task history to start fresh."""
        self.current_url = url
        
        if not self.is_session_healthy:
            logger.info("Browser session is not active or has been closed. Re-starting session for navigation...")
            self.close_session()
            if not self.start_session(headless=config.HEADLESS):
                logger.error("Failed to restart browser session for navigation.")
                return False
                
        logger.info(f"Navigating persistent browser to URL: {url}")
        res = self.browser_manager.navigate_to_url(url)
        if res["success"]:
            # Clean history for new site navigation
            self.conversation_history = []
            self.step_count = 0
            return True
        return False

    def run_task(self, task_description: str, max_steps: int = 5) -> bool:
        """Performs a task description on the already-opened webpage state, loops autonomously to complete it."""
        if not self.is_session_healthy:
            logger.info("Browser session is not healthy or has been closed. Re-starting session...")
            self.close_session()
            if not self.start_session(headless=config.HEADLESS):
                logger.error("Failed to restart browser session for task execution.")
                return False
            if self.current_url:
                logger.info(f"Re-navigating to {self.current_url}...")
                if not self.navigate_to(self.current_url):
                    logger.error(f"Failed to re-navigate to {self.current_url}")
                    return False
            
        # Reset task status and clear old history to avoid LLM confusion from previous tasks
        self.task_completed = False
        self.conversation_history = []
        self.screenshot_taken = False
        task_step = 0
        
        # System prompt setting up the task instructions dynamically
        system_prompt = f"""You are the cognitive brain of a University Website Automation Agent.
Your objective is to complete the user's requested task on the current page context.

TARGET TASK:
{task_description}

OPERATING PRINCIPLES:
- Reason step-by-step before invoking any tool. Explain your thought process in the assistant text.
- Do NOT call `open_browser` or `navigate_to_url` unless specifically requested by the user's task description (the browser is already open and loaded).
- Do NOT call `take_screenshot` unless explicitly requested by the task, as the agent coordinator automatically captures progress screenshots.
- Look at the "Available interactive elements on the page" list provided in the user message. This list gives you exact IDs, selectors, labels, and coordinates.
- Crucially, when calling `send_keys` or `double_click`, the `selector` parameter MUST be the exact literal string from either the `Selector` or `Label` field of one of the perceived elements. Do NOT invent new descriptive names (e.g. use "#form-rhf-demo-title" or "Bug Title" instead of inventing "message box" or "name field").
- To input text into a field, call `send_keys` with the element's selector or semantic label.
- If the target elements are not visible, use `scroll` to scroll down.
- Once the task has been successfully completed, call `task_complete` with a summary of the operations performed.

COMPLETION CRITERIA:
You must call `task_complete` with a brief summary when you have completed the user's task.
"""

        logger.info(f"--- Starting Task Loop for: '{task_description}' ---")
        
        # Insert task command context into history so LLM is oriented
        self.conversation_history.append({
            "role": "user",
            "content": f"New Task instruction to execute: {task_description}"
        })

        try:
            while task_step < max_steps and not self.task_completed:
                task_step += 1
                self.step_count += 1
                logger.info(f"\n=== AGENT LOOP STEP {task_step}/{max_steps} (Global Step: {self.step_count}) ===")
                
                # a. Perceive: Only take screenshot if we are using a vision-capable model to save disk/tokens
                screenshot_path = None
                if self.llm_client.is_vision_model:
                    screenshot_res = self.browser_manager.take_screenshot(f"step_{self.step_count}_perceive.png")
                    screenshot_path = screenshot_res.get("path") if screenshot_res["success"] else None
                
                # Extract interactive elements context
                elements = self.browser_manager.get_interactive_elements()
                logger.info(f"Perceived {len(elements)} interactive elements in current viewport.")
                
                # b. Decide: Query LLM (Grok/Llama)
                try:
                    text_content, tool_calls = self.llm_client.query(
                        system_prompt=system_prompt,
                        conversation_history=self.conversation_history,
                        latest_screenshot_path=screenshot_path,
                        interactive_elements=elements,
                        tools=self.tools
                    )
                except Exception as e:
                    logger.error(f"Error calling LLM API: {e}")
                    self.browser_manager.take_screenshot("error_llm_api.png")
                    break
                
                if text_content:
                    logger.info(f"LLM Reasoning: {text_content}")
                
                if not tool_calls:
                    logger.warning("LLM response did not request any tool call. Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                
                # c. Act: Execute proposed tool calls
                assistant_tool_calls_payload = []
                for tc in tool_calls:
                    assistant_tool_calls_payload.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
                    
                self.conversation_history.append({
                    "role": "assistant",
                    "content": text_content,
                    "tool_calls": assistant_tool_calls_payload
                })
                
                for tc in tool_calls:
                    name = tc.function.name
                    raw_args = tc.function.arguments
                    
                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except Exception as json_err:
                        logger.error(f"Failed to parse tool call arguments '{raw_args}': {json_err}")
                        args = {}
                        
                    logger.info(f"ACTING: Executing tool '{name}' with args {args}")
                    
                    # Execute tool action
                    tool_result = self.execute_tool(name, args)
                    logger.info(f"OBSERVATION: Tool '{name}' returned: {tool_result}")
                    
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result)
                    })
                    
                    if self.task_completed:
                        break
                        
            if self.task_completed:
                # Capture exactly one success screenshot per task if not already captured
                if not getattr(self, "screenshot_taken", False):
                    self.browser_manager.take_screenshot(f"task_{self.step_count}_success.png")
                logger.info(f"RESULT: Task '{task_description}' successfully completed.")
                return True
            else:
                if not getattr(self, "screenshot_taken", False):
                    self.browser_manager.take_screenshot(f"task_{self.step_count}_failure.png")
                logger.error(f"RESULT: Task '{task_description}' finished without completion signal or failed.")
                return False
                
        except Exception as e:
            logger.error(f"Fatal error in task loop: {e}", exc_info=True)
            self.browser_manager.take_screenshot("error_fatal.png")
            return False

    def execute_tool(self, name: str, arguments: dict) -> dict:
        """Executes a single tool based on its name and arguments, returning a structured success/failure dict."""
        try:
            if name == "task_complete":
                summary = arguments.get("summary", "Task finished.")
                self.task_completed = True
                return {"success": True, "message": f"Task complete acknowledged: {summary}"}
                
            elif name == "open_browser":
                headless = arguments.get("headless", config.HEADLESS)
                return self.browser_manager.open_browser(headless=headless)
                
            elif name == "navigate_to_url":
                url = arguments.get("url")
                if not url:
                    return {"success": False, "message": "Missing 'url' argument."}
                return self.browser_manager.navigate_to_url(url)
                
            elif name == "take_screenshot":
                filename = arguments.get("filename", "screenshot")
                self.screenshot_taken = True
                return self.browser_manager.take_screenshot(filename)
                
            elif name == "click_on_screen":
                x = arguments.get("x")
                y = arguments.get("y")
                if x is None or y is None:
                    return {"success": False, "message": "Missing 'x' or 'y' coordinate arguments."}
                return self.browser_manager.click_on_screen(x, y)
                
            elif name == "send_keys":
                selector = arguments.get("selector")
                text = arguments.get("text")
                if selector is None or text is None:
                    return {"success": False, "message": "Missing 'selector' or 'text' arguments."}
                return self.browser_manager.send_keys(selector, text)
                
            elif name == "scroll":
                direction = arguments.get("direction", "down")
                amount = arguments.get("amount", 500)
                return self.browser_manager.scroll(direction, amount)
                
            elif name == "double_click":
                selector = arguments.get("selector")
                if selector is None:
                    return {"success": False, "message": "Missing 'selector' argument."}
                return self.browser_manager.double_click(selector)
                
            else:
                return {"success": False, "message": f"Unknown tool call name '{name}'"}
                
        except Exception as e:
            logger.error(f"Exception during execution of tool '{name}': {e}")
            return {"success": False, "message": f"Error executing tool '{name}': {str(e)}"}

    def close_session(self):
        """Closes browser session."""
        logger.info("Closing persistent browser session.")
        self.browser_manager.close_browser()
        self.session_active = False
