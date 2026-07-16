import json
from pathlib import Path
from dataclasses import asdict
from shutil import rmtree


class Recorder:

    def __init__(self, folder: str):
        self.folder = Path(folder)

        if self.folder.exists():
            rmtree(self.folder)

        self.snapshots_folder = self.folder / "snapshots"
        self.steps_file = self.folder / "steps.jsonl"

        self.snapshots_folder.mkdir(parents=True)


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