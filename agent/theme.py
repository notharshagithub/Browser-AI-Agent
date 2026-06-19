"""
Cyberpunk/Agentic AI CLI Theme & Terminal Interface styling for Browser-AI-Agent.
Provides neon color definitions, custom state formatting, status cards, and diagnostic alerts.
"""

import sys
import os

# ANSI Neon/Cyberpunk Theme Colors
CYAN = "\033[38;5;51m"       # Neon Cyan
GREEN = "\033[38;5;82m"      # Neon Green
MAGENTA = "\033[38;5;201m"   # Pink/Magenta
ORANGE = "\033[38;5;208m"    # Warm Orange/Warning
RED = "\033[38;5;196m"       # Alarm Red
YELLOW = "\033[38;5;226m"    # Cyber Yellow
GRAY = "\033[38;5;244m"      # Dark Gray
BLUE = "\033[38;5;39m"       # Deep Sky Blue
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

# UI Borders and Shapes
DOUBLE_LINE = "═"
SINGLE_LINE = "─"
CORNER_TL = "╔"
CORNER_TR = "╗"
CORNER_BL = "╚"
CORNER_BR = "╝"
BOX_VERTICAL = "║"
BOX_HORIZONTAL = "═"

def clear_screen():
    """Clears the console screen."""
    os.system("clear" if os.name != "nt" else "cls")

def get_terminal_width(default=80):
    """Safely retrieves terminal columns width."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default

def print_horizontal_divider(char=SINGLE_LINE, color=GRAY):
    """Prints a styled divider matching the width of the terminal."""
    width = min(get_terminal_width(), 80)
    print(f"{color}{char * width}{RESET}")

def print_welcome_banner():
    """Renders a high-tech Agentic AI welcome banner."""
    width = min(get_terminal_width(), 80)
    
    # ASCII Art banner
    banner = [
        r"     ___       __  ___  __  ___  __  ___  __   __    ",
        r"    / _ \___  /  |/  / /  |/  / /  |/  / /  | /  |   ",
        r"   /  __  /  / /|_/ / / /|_/ / / /|_/ / /   |/   |   ",
        r"  /__/ /_/  /_/  /_/ /_/  /_/ /_/  /_/ /_/|__/|__|   ",
        r"  >> B R O W S E R  -  A I  -  A U T O M A T I O N   "
    ]
    
    print(f"\n{CYAN}{BOLD}{CORNER_TL}{DOUBLE_LINE * (width-2)}{CORNER_TR}{RESET}")
    for line in banner:
        padded = line.center(width - 2)
        print(f"{CYAN}{BOLD}{BOX_VERTICAL}{RESET}{CYAN}{padded}{RESET}{CYAN}{BOLD}{BOX_VERTICAL}{RESET}")
        
    print(f"{CYAN}{BOLD}{BOX_VERTICAL}{RESET}{GRAY}{'   [ Persistent Browser Cognitive Agent ]'.center(width-2)}{RESET}{CYAN}{BOLD}{BOX_VERTICAL}{RESET}")
    print(f"{CYAN}{BOLD}{CORNER_BL}{DOUBLE_LINE * (width-2)}{CORNER_BR}{RESET}\n")
    
    # Quick Instructions Card
    print(f"  {MAGENTA}{BOLD}⚡ CORE INTERFACES{RESET}")
    print(f"  {GRAY}├─{RESET} {GREEN}{BOLD}Link Input{RESET}   : Enter URL (e.g. {CYAN}google.com{RESET}) or press {YELLOW}Enter{RESET} for default target.")
    print(f"  {GRAY}├─{RESET} {GREEN}{BOLD}Task Prompts{RESET} : Instruct the agent in plain English.")
    print(f"  {GRAY}├─{RESET} {GREEN}{BOLD}Session Exit{RESET} : Type {RED}'exit'{RESET} to switch websites; {RED}'stop'{RESET} to close session.")
    print(f"  {GRAY}└─{RESET} {GREEN}{BOLD}Status Log{RESET}   : Real-time telemetry is streamed to {BLUE}logs/agent.log{RESET}\n")
    print_horizontal_divider(SINGLE_LINE, CYAN)

def print_status_card(title: str, url: str, status: str = "STANDBY"):
    """Prints a styled high-tech card representing agent connection state."""
    width = min(get_terminal_width(), 70)
    inner_width = width - 4
    
    status_colors = {
        "STANDBY": GRAY,
        "CONNECTED": GREEN,
        "ACTIVE": CYAN,
        "ERROR": RED,
        "WARNING": ORANGE
    }
    sc = status_colors.get(status.upper(), YELLOW)
    
    print(f"\n{sc}{CORNER_TL}{BOX_HORIZONTAL * inner_width}{CORNER_TR}{RESET}")
    
    title_str = f"SYSTEM: {title}".ljust(inner_width - 2)
    print(f"{sc}{BOX_VERTICAL}{RESET} {BOLD}{title_str} {sc}{BOX_VERTICAL}{RESET}")
    
    url_str = f"TARGET: {url}".ljust(inner_width - 2)
    print(f"{sc}{BOX_VERTICAL}{RESET} {GRAY}{url_str}{RESET} {sc}{BOX_VERTICAL}{RESET}")
    
    status_str = f"STATUS: [{status}]".ljust(inner_width - 2)
    print(f"{sc}{BOX_VERTICAL}{RESET} {sc}{BOLD}{status_str}{RESET} {sc}{BOX_VERTICAL}{RESET}")
    
    print(f"{sc}{CORNER_BL}{BOX_HORIZONTAL * inner_width}{CORNER_BR}{RESET}\n")

def print_step_header(step: int, max_steps: int, global_step: int):
    """Renders a progress tracker header for cognitive steps."""
    width = min(get_terminal_width(), 80)
    bar_len = 15
    filled = int((step / max_steps) * bar_len)
    bar = f"{GREEN}█{RESET}" * filled + f"{GRAY}░{RESET}" * (bar_len - filled)
    
    step_info = f" COGNITIVE STEP [{step}/{max_steps}] "
    glob_info = f" (Global: {global_step}) "
    remaining = width - len(step_info) - len(glob_info) - bar_len - 6
    
    print(f"\n{CYAN}{BOLD}┠─{RESET}{YELLOW}{BOLD}{step_info}{RESET}{GRAY}┫{RESET} {bar} {GRAY}┣{RESET}{CYAN}{BOLD}{glob_info}{RESET}{GRAY}{SINGLE_LINE * remaining}{RESET}")

def print_tool_execution(name: str, arguments: dict):
    """Displays a clean tool invocation report."""
    args_str = ", ".join(f"{BLUE}{k}{RESET}={YELLOW}{repr(v)}{RESET}" for k, v in arguments.items())
    print(f"  {MAGENTA}▶ EXECUTING ACTUATOR:{RESET} {BOLD}{name}{RESET}({args_str})")

def print_tool_observation(result: dict):
    """Prints the observation output of a tool execution."""
    success = result.get("success", False)
    marker = f"{GREEN}✔ SUCCESS{RESET}" if success else f"{RED}✘ FAILED{RESET}"
    msg = result.get("message", result.get("error", "No message details provided."))
    print(f"  {GRAY}└─{RESET} {marker} : {msg}")

def print_success_card(summary: str):
    """Displays a stylized success dashboard."""
    print(f"\n{GREEN}{BOLD}🎉 TASK SUCCESS ACKNOWLEDGED (PASS){RESET}")
    print(f"  {GREEN}Summary:{RESET} {summary}")
    print_horizontal_divider(SINGLE_LINE, GREEN)

def print_failure_card(reason: str, steps_executed: int):
    """Renders a beautiful high-tech diagnostic diagnostic/failure card."""
    width = min(get_terminal_width(), 75)
    inner_width = width - 4
    
    print(f"\n{RED}{CORNER_TL}{BOX_HORIZONTAL * inner_width}{CORNER_TR}{RESET}")
    
    header = "🚨 COGNITIVE SYSTEM FAILURE DIAGNOSTICS".center(inner_width)
    print(f"{RED}{BOX_VERTICAL}{RESET}{RED}{BOLD}{header}{RESET}{RED}{BOX_VERTICAL}{RESET}")
    print(f"{RED}{BOX_VERTICAL}{GRAY}{SINGLE_LINE * inner_width}{RESET}{RED}{BOX_VERTICAL}{RESET}")
    
    # Wrap text manually if it's too long
    lines = []
    current_line = []
    for word in f"Failure Reason: {reason}".split():
        if sum(len(w) + 1 for w in current_line) + len(word) < inner_width - 4:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    for line in lines:
        padded_line = line.ljust(inner_width - 2)
        print(f"{RED}{BOX_VERTICAL}{RESET} {RED}{BOLD}{padded_line}{RESET} {RED}{BOX_VERTICAL}{RESET}")
        
    steps_str = f"Steps executed: {steps_executed}".ljust(inner_width - 2)
    print(f"{RED}{BOX_VERTICAL}{RESET} {GRAY}{steps_str}{RESET} {RED}{BOX_VERTICAL}{RESET}")
    
    remedy = "Action: Check logs/agent.log and screenshots/ folders for recovery cues.".ljust(inner_width - 2)
    print(f"{RED}{BOX_VERTICAL}{RESET} {YELLOW}{remedy}{RESET} {RED}{BOX_VERTICAL}{RESET}")
    
    print(f"{RED}{CORNER_BL}{BOX_HORIZONTAL * inner_width}{CORNER_BR}{RESET}\n")

def print_error_boundary(title: str, error_message: str):
    """Prints system core exception alerts."""
    print(f"\n{ORANGE}{BOLD}⚠ SYSTEM ALERT: {title}{RESET}")
    print(f"  {GRAY}Details:{RESET} {error_message}")
    print_horizontal_divider(SINGLE_LINE, ORANGE)
