import sys
import logging
import argparse
import agent.config as config
from agent.agent import WebsiteAutomationAgent
import agent.theme as theme

def main():
    """Main entrypoint to run the Website Automation Agent in a persistent browser console."""
    # Ensure standard logging is set up
    logger = logging.getLogger("main")
    
    # Setup argparse CLI parameter parser
    parser = argparse.ArgumentParser(description="AI Website Automation Agent CLI Console")
    parser.add_argument("-u", "--url", type=str, help="Default target URL to load on launch")
    parser.add_argument("--headless", action="store_true", help="Launch browser in headless mode")
    parser.add_argument("--headful", action="store_true", help="Launch browser in headful mode (visible window)")
    parser.add_argument("-t", "--theme", type=str, choices=["cyberpunk", "retro", "matrix"], default="cyberpunk", help="Console theme aesthetic")
    parser.add_argument("-s", "--max-steps", type=int, help="Maximum cognitive steps allowed per task")
    args = parser.parse_args()

    # Apply command line options to configuration
    if args.url:
        config.TARGET_URL = args.url
    if args.headless:
        config.HEADLESS = True
    elif args.headful:
        config.HEADLESS = False
    if args.max_steps:
        config.MAX_STEPS = args.max_steps
        
    # Apply dynamic color theme
    theme.set_theme(args.theme)
    
    theme.print_welcome_banner()
    
    # Initialize the persistent agent
    agent = WebsiteAutomationAgent()
    
    try:
        while True:
            # 1. Prompt user for website link
            default_url = config.TARGET_URL
            user_url = input(f"\nEnter Website Link to load [Default: {default_url}, or 'stop' to exit]: ").strip()
            
            # Check exit criteria
            if user_url.lower() in ("stop", "exit"):
                print("\nExiting agent console. Goodbye!")
                break
                
            target_url = user_url if user_url else default_url
            
            # Prepend protocol if domain only
            if target_url and not target_url.startswith(("http://", "https://")):
                target_url = "https://" + target_url
                
            # Launch the browser if not already open or if it has been closed
            if not agent.is_session_healthy:
                agent.close_session()
                print(f"🚀 Launching browser context (headless={config.HEADLESS})...")
                if not agent.start_session(headless=config.HEADLESS):
                    print("❌ Error starting browser. Please check configuration.")
                    continue
            
            # Navigate to the website
            print(f"🌐 Navigating to {target_url}...")
            if not agent.navigate_to(target_url):
                print(f"❌ Error navigating to {target_url}.")
                # If navigation fails, we close the session to ensure clean state
                agent.close_session()
                continue
                
            theme.print_status_card("CONNECTED TO WEB HOST", target_url, "CONNECTED")
            
            # 2. Task execution loop for the current page
            while True:
                task_details = input(f"\nTask for {target_url} (or 'exit'/'stop'): ").strip()
                
                # Check exit commands
                if task_details.lower() == "exit":
                    print(f"🔌 Closing browser session for {target_url}...")
                    agent.close_session()
                    break
                    
                if task_details.lower() == "stop":
                    print("\nExiting agent console. Goodbye!")
                    agent.close_session()
                    sys.exit(0)
                    
                if not task_details:
                    if "google.com" in target_url:
                        task_details = "Type 'playwright python' into the search input and click the search button to submit."
                        print("📝 Using default Google search instructions.")
                    else:
                        task_details = (
                            "Locate the demo form. In this form:\n"
                            "- Fill the Name (labeled 'Bug Title' or with id '#form-rhf-demo-title') with 'John Doe'.\n"
                            "- Fill the Description field (id '#form-rhf-demo-description') with 'This is a test description filled by an automation agent.'\n"
                            "- Submit the form by clicking the black Submit button.\n"
                            "- Capture a screenshot of the popup confirmation and mark the task complete."
                        )
                        print("📝 Using default Shadcn form-filling instructions.")
                    
                theme.print_status_card("EXECUTING AUTONOMOUS AGENT", target_url, "ACTIVE")
                success = agent.run_task(task_details)
                
                theme.print_horizontal_divider(theme.SINGLE_LINE, theme.CYAN)
                print(" Ready for next task on this page...")
                theme.print_horizontal_divider(theme.SINGLE_LINE, theme.CYAN)
                
    except KeyboardInterrupt:
        print("\n\nSession interrupted. Cleaning up...")
    finally:
        # Guarantee cleanup
        if agent.session_active:
            agent.close_session()
            
    sys.exit(0)

if __name__ == "__main__":
    main()
