# ~/work/xyllidium/launch_xyllidium.py
import subprocess, time, socket

def wait_for_port(port, host="127.0.0.1", timeout=15):
    """Wait until a TCP port is open."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"✅ Port {port} is ready.")
                return True
        except OSError:
            time.sleep(0.5)
        if time.time() - start_time > timeout:
            print(f"❌ Timeout waiting for port {port}")
            return False

print("🚀 Starting full Xyllidium core stack...\n")

# Step 1: Launch equilibrium engine (Xyllenor)
engine_proc = subprocess.Popen(["python", "core/xyllenor/engine.py"])

# Wait for WS and HTTP to be ready
wait_for_port(8765)
wait_for_port(8766)

# Step 2: Execute sample intent
print("⚙️  Running executor transaction...")
time.sleep(1)
subprocess.run(["python", "-m", "core.xyllencore.executor"])

print("\n🟢 Xyllidium core is live.")
print("Press Ctrl+C to shut down.\n")

engine_proc.wait()
