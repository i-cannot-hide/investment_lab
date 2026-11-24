import importlib
import pkgutil

import researches


def main() -> None:
    """Run every research module that defines ``run``."""
    for module_info in pkgutil.iter_modules(researches.__path__):
        module = importlib.import_module(f"researches.{module_info.name}")
        run = getattr(module, "run", None)
        if callable(run):
            run()


if __name__ == "__main__":
    main()
