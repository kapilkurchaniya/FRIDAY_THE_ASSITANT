import subprocess
import sys

if __name__ == "__main__":
    print("Starting JARVIS Web Interface...")
    print("Please open http://localhost:5000 in your Chrome/Edge browser.")
    
    # Run the Flask app
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\nShutting down...")