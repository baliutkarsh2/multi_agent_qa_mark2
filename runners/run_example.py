"""
Example runner wiring all agents together with comprehensive run logging.
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path and load environment variables first
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables before importing other modules
from core.env_loader import load_env_file
load_env_file()

import agents
import core.logging_config
from core.episode import EpisodeContext
from core.registry import get_agent
from env.android_interface import AndroidDevice
from core.message_bus import subscribe, Message
from core.run_logger_integration import run_logging_session

class App:
    def __init__(self, goal: str, serial: str = None):
        self.goal = goal
        self.device = AndroidDevice(serial)
        self.episode = EpisodeContext(user_goal=goal)
        self.is_done = False
        
        # Initialize agents
        self.planner = get_agent("llm_planner")()
        self.executor = get_agent("llm_executor")(self.device)
        self.verifier = get_agent("llm_verifier")(self.device)
        self.supervisor = get_agent("llm_supervisor")()
        
        # Subscribe to completion message
        subscribe("episode_done", self.on_episode_done)

    def initialize_device_state(self):
        """Initialize device to a known state before starting automation."""
        print("🔧 **Device State Initialization**")
        print("Ensuring device is in a known state before automation...")
        
        # Log initialization start to run logger if available
        from core.run_logger import get_run_logger
        run_logger = get_run_logger()
        
        # Debug device connection status
        print(f"  📱 Device connected: {self.device.device_connected}")
        print(f"  📱 ADB available: {self.device.adb_available}")
        
        try:
            # Step 1: Press home button to go to home screen
            print("  📱 Pressing home button...")
            print(f"    - Calling: self.device.press_key('HOME')")
            self.device.press_key("HOME")
            import time
            time.sleep(1.0)  # Wait for home screen to load
            
            # Log home button action
            if run_logger:
                run_logger.log_event("device_initialization", "RUNNER", {
                    "step": "home_button_press",
                    "action": "press_key",
                    "key": "HOME",
                    "status": "success"
                })
            
            # Step 2: Scroll down once to initialize scroll state
            print("  📜 Scrolling down once to initialize scroll state...")
            print(f"    - Calling: self.device.scroll('down')")
            self.device.scroll("down")
            time.sleep(0.5)  # Brief pause after scroll
            
            # Log scroll action
            if run_logger:
                run_logger.log_event("device_initialization", "RUNNER", {
                    "step": "scroll_initialization",
                    "action": "scroll",
                    "direction": "down",
                    "status": "success"
                })
            
            print("  ✅ Device state initialized successfully!")
            print("  🏠 Device is now on home screen with scroll state initialized")
            
            # Log successful initialization
            if run_logger:
                run_logger.log_event("device_initialization", "RUNNER", {
                    "status": "completed",
                    "device_state": "home_screen",
                    "scroll_state": "initialized"
                })
            
        except Exception as e:
            print(f"  ⚠️  Warning: Device initialization failed: {e}")
            print("  🔄 Continuing with automation anyway...")
            
            # Log initialization failure
            if run_logger:
                run_logger.log_error("RUNNER", f"Device initialization failed: {str(e)}", context={
                    "initialization_step": "device_state_setup",
                    "error_type": "initialization_failure"
                })

    def on_episode_done(self, msg: Message):
        self.is_done = True
        reason = msg.payload.get('reason', 'Unknown reason')
        print(f"Episode is done. Reason: {reason}")
        
        # Log episode completion to run logger if available
        from core.run_logger import get_run_logger
        run_logger = get_run_logger()
        if run_logger:
            # Find the episode ID from the episode context
            episode_id = f"episode_{id(self.episode)}"
            run_logger.log_episode_end(episode_id, "completed", reason)

    def run(self):
        print(f"Goal: {self.goal}")
        
        # Initialize device state first
        self.initialize_device_state()
        
        # Start the first planning step
        ui = self.device.get_ui_tree()
        self.planner.act(self.goal, ui, self.episode)
        
        # Keep the app running until the episode is marked as done
        while not self.is_done:
            pass

def main():
    parser = argparse.ArgumentParser(description="Run Android automation with comprehensive logging")
    parser.add_argument("--goal", required=True, help="Automation goal (e.g., 'Enable Wi-Fi in Android settings')")
    parser.add_argument("--serial", help="Android device serial (e.g., emulator-5554)")
    args = parser.parse_args()
    
    # Use the run logging session to automatically capture all automation activities
    with run_logging_session(args.goal) as run_logger:
        print(f"🚀 Starting automation with comprehensive logging...")
        print(f"📋 Goal: {args.goal}")
        if args.serial:
            print(f"📱 Device: {args.serial}")
        print(f"🆔 Run ID: {run_logger.run_id}")
        print(f"📁 Logs will be saved to: logs/run_{run_logger.run_id}/")
        print("=" * 60)
        
        try:
            # Log automation start
            run_logger.log_event("automation_start", "RUNNER", {
                "goal": args.goal,
                "device_serial": args.serial,
                "run_id": run_logger.run_id
            })
            
            # Create and run the automation app
            app = App(args.goal, args.serial)
            
            # Log episode start
            episode_id = f"episode_{id(app.episode)}"
            run_logger.log_episode_start(episode_id, args.goal)
            
            # Run the automation
            app.run()
            
            # Log automation completion
            run_logger.log_event("automation_complete", "RUNNER", {
                "status": "success",
                "goal": args.goal,
                "episode_id": episode_id
            })
            
            print("=" * 60)
            print("✅ Automation completed successfully!")
            print(f"📊 Run log saved to: logs/run_{run_logger.run_id}/")
            
        except Exception as e:
            # Log automation failure
            run_logger.log_error("RUNNER", f"Automation failed: {str(e)}", context={
                "error_type": "automation_failure",
                "goal": args.goal,
                "device_serial": args.serial
            })
            
            print("=" * 60)
            print(f"❌ Automation failed: {e}")
            print(f"📊 Check the run log for detailed error information: logs/run_{run_logger.run_id}/")
            raise

if __name__ == "__main__":
    main() 