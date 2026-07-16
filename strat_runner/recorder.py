import json
from dataclasses import asdict
from pathlib import Path


class Recorder:

    def __init__(self, folder: str):
        self.folder = Path(folder)
        self.snapshots_folder = self.folder / "snapshots"

        self.folder.mkdir(parents=True, exist_ok=True)
        self.snapshots_folder.mkdir(exist_ok=True)

        self.events_file = self.folder / "events.jsonl"


    def record_event(self, event_type: str, data: dict):
        event = {
            "type": event_type,
            "data": data
        }

        with open(self.events_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")


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