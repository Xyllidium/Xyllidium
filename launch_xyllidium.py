# ~/work/xyllidium/launch_xyllidium.py
import os, sys, time, socket, subprocess, signal

def wait_for_port(port, host="127.0.0.1", timeout=20, label=""):
    """Wait until a TCP port is open (up to timeout seconds)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"✅ Port {port} ready. ({label})")
                return True
        except OSError:
            time.sleep(0.5)
    print(f"❌ Timeout waiting for port {port} ({label})")
    return False

print("🚀 Starting full Xyllidium core stack...\n")

# Ensure we’re in the project root
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Make sure Python sees the project root as a package
env = os.environ.copy()
env["PYTHONPATH"] = ROOT

# Start the engine as a *module* so relative imports work
print("🧠 Launching Xyllenor equilibrium engine...")
engine = subprocess.Popen(
    [sys.executable, "-m", "core.xyllenor.engine"],
    env=env,
    cwd=ROOT
)

# Wait for the HTTP and WebSocket ports
wait_for_port(8766, label="HTTP")
wait_for_port(8765, label="WebSocket")

# Once ready, automatically trigger one test intent
print("⚙️  Running executor transaction...")
subprocess.run([sys.executable, "-m", "core.xyllencore.executor"], check=False)

print("\n🟢 Xyllidium core is live.")
print("Press Ctrl+C to shut down.\n")

try:
    engine.wait()
except KeyboardInterrupt:
    print("\n🧩 Shutting down...")
    try:
        engine.terminate()
        engine.wait(timeout=3)
    except Exception:
        engine.kill()
