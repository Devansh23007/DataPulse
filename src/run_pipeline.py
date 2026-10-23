
from pathlib import Path
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
PIPELINE_LOG = LOG_DIR / "pipeline.log"

STAGES = [
    ("Source validation", [sys.executable, "-m", "src.ingestion"]),
    ("Raw PostgreSQL load", [sys.executable, "-m", "src.load_raw"]),
    ("Data quality checks", [sys.executable, "-m", "src.run_quality_checks"]),
    ("Automated tests", [sys.executable, "-m", "pytest", "-v"]),
]


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                PIPELINE_LOG, encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    run_id = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    logging.info("Pipeline started | run_id=%s", run_id)
    pipeline_started = time.perf_counter()

    for stage_name, command in STAGES:
        stage_started = time.perf_counter()
        logging.info("Starting stage: %s", stage_name)

        try:
            result = subprocess.run(
                command,
                cwd=ROOT_DIR,
                check=False,
            )
        except OSError:
            logging.exception(
                "Could not start stage: %s", stage_name
            )
            sys.exit(1)

        duration = round(
            time.perf_counter() - stage_started, 2
        )

        if result.returncode != 0:
            logging.error(
                "Stage failed: %s | duration=%ss | exit=%s",
                stage_name,
                duration,
                result.returncode,
            )
            logging.error("Pipeline stopped.")
            sys.exit(result.returncode or 1)

        logging.info(
            "Stage passed: %s | duration=%ss",
            stage_name,
            duration,
        )

    total_duration = round(
        time.perf_counter() - pipeline_started, 2
    )

    logging.info(
        "Pipeline completed successfully | run_id=%s | duration=%ss",
        run_id,
        total_duration,
    )


if __name__ == "__main__":
    main()
