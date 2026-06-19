import sys
import logging
import agent.config as config
from agent.agent import WebsiteAutomationAgent

def main():
    """Main entrypoint to run the Website Automation Agent in a persistent browser console."""
    # Ensure standard logging is set up
    logger = logging.getLogger("main")
    
    print("\n==================================================================")
    print("  🤖 WELCOME TO THE AI WEBSITE AUTOMATION AGENT CONSOLE")
    print("==================================================================")
    print("  Instructions:")
    print("  1. Press Enter to load the default target (Google), or type a URL.")
    print("  2. Enter website tasks in plain English (e.g. 'search for ...').")
    print("  3. Type 'exit' to switch websites, or 'stop' to exit completely.")
    print("==================================================================\n")
    
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
                
            print("\n--------------------------------------------------------")
            print(f"✅ Connected: {target_url}")
            print("You can now enter tasks for this webpage below.")
            print("Type 'exit' to switch websites, or 'stop' to exit completely.")
            print("--------------------------------------------------------")
            
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
                    
                print(f"🤖 Executing task: '{task_details}'...")
                success = agent.run_task(task_details)
                
                if success:
                    print("\n✅ Task completed successfully (PASS)!")
                else:
                    print("\n❌ Task stopped (FAIL). Check screenshots/ and logs/agent.log for details.")
                    
                print("\n--------------------------------------------------------")
                print("Ready for next task on this page...")
                print("--------------------------------------------------------")
                
    except KeyboardInterrupt:
        print("\n\nSession interrupted. Cleaning up...")
    finally:
        # Guarantee cleanup
        if agent.session_active:
            agent.close_session()
            
    sys.exit(0)

if __name__ == "__main__":
    main()
