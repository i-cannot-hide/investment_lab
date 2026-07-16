import json
from pathlib import Path
from dataclasses import asdict


class Recorder:

    def __init__(self, folder: str):
        self.folder = Path(folder)

        self.snapshots_folder = self.folder / "snapshots"
        self.steps_file = self.folder / "steps.jsonl"

        self.folder.mkdir(parents=True, exist_ok=True)
        self.snapshots_folder.mkdir(exist_ok=True)


    def save_snapshot(self, step: int, context):
        path = self.snapshots_folder / f"{step:06d}.json"

        with open(path, "w") as f:
            json.dump(
                asdict(context),
                f,
                default=str,
                indent=2
            )

        return path


    def record_step(self, step_data: dict):
        with open(self.steps_file, "a") as f:
            f.write(
                json.dumps(step_data, default=str)
                + "\n"
            )