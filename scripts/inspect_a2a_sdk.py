import importlib.util
import os
import pkgutil
import sys

print("Python:", sys.version)
print("sys.path[0]:", sys.path[0])
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print("project_root:", project_root)
# Ensure project root is not shadowing installed packages
try:
    sys.path.remove(project_root)
    print("project_root removed from sys.path")
except ValueError:
    print("project_root not in sys.path")

# Find the a2a package
spec = importlib.util.find_spec("a2a")
print("a2a spec:", spec)
if spec is None:
    print("a2a not found in environment")
    sys.exit(0)

if spec.submodule_search_locations:
    pkgdir = list(spec.submodule_search_locations)[0]
    print("a2a pkgdir:", pkgdir)
    try:
        print("top-level contents:", os.listdir(pkgdir))
    except Exception as e:
        print("listdir error:", e)

    try:
        import a2a

        print("a2a file:", getattr(a2a, "__file__", None))
        print("a2a path:", getattr(a2a, "__path__", None))
        names = [name for _, name, _ in pkgutil.walk_packages(a2a.__path__, a2a.__name__ + ".")]
        print("a2a submodules count:", len(names))
        for name in sorted(names):
            if any(
                k in name
                for k in [
                    "server",
                    "jsonrpc",
                    "fastapi",
                    "request",
                    "handler",
                    "task",
                    "inmemory",
                    "agent",
                    "http",
                    "apps",
                ]
            ):
                print("  candidate:", name)
    except Exception as e:
        print("error importing a2a:", type(e).__name__, e)
else:
    print("a2a has no submodule_search_locations (namespace pkg?)")

# Also try a2a_sdk
spec2 = importlib.util.find_spec("a2a_sdk")
print("a2a_sdk spec:", spec2)
if spec2 and spec2.submodule_search_locations:
    pkgdir2 = list(spec2.submodule_search_locations)[0]
    print("a2a_sdk pkgdir:", pkgdir2)
    try:
        print("a2a_sdk top-level contents:", os.listdir(pkgdir2))
    except Exception as e:
        print("listdir error:", e)
