"""Collector for Databricks job run data."""

from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog

from costpulse.collectors.base import BaseCollector

logger = structlog.get_logger()


class JobCollector(BaseCollector):
    """Collect job run information from Databricks workspace."""

    def __init__(self, host: str, token: str, lookback_hours: int = 24):
        super().__init__(host, token)
        self.lookback_hours = lookback_hours

    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch recent job runs from the workspace.

        Returns:
            List of raw job run records
        """
        try:
            jobs = list(self.client.jobs.list(expand_tasks=False))
            raw_data = []

            for job in jobs:
                try:
                    runs = list(
                        self.client.jobs.list_runs(
                            job_id=job.job_id,
                            expand_tasks=False,
                            limit=10,
                        )
                    )
                    for run in runs:
                        raw_data.append(
                            {
                                "job_id": str(job.job_id),
                                "job_name": (
                                    job.settings.name if job.settings else f"job-{job.job_id}"
                                ),
                                "run_id": str(run.run_id),
                                "creator_user_name": job.creator_user_name,
                                "state": (
                                    run.state.life_cycle_state.value
                                    if run.state and run.state.life_cycle_state
                                    else None
                                ),
                                "result_state": (
                                    run.state.result_state.value
                                    if run.state and run.state.result_state
                                    else None
                                ),
                                "start_time": run.start_time,
                                "end_time": run.end_time,
                                "run_type": run.run_type.value if run.run_type else None,
                                "cluster_id": (
                                    run.cluster_instance.cluster_id
                                    if run.cluster_instance
                                    else None
                                ),
                                "tasks": run.tasks or [],
                                "schedule": (
                                    job.settings.schedule.quartz_cron_expression
                                    if job.settings and job.settings.schedule
                                    else None
                                ),
                                "tags": (
                                    job.settings.tags if job.settings and job.settings.tags else {}
                                ),
                            }
                        )
                except Exception as e:
                    logger.warning("Failed to get runs for job", job_id=job.job_id, error=str(e))

            logger.info("Collected job runs", count=len(raw_data))
            return raw_data
        except Exception as e:
            logger.error("Failed to collect jobs", error=str(e))
            raise

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform job run data into standardized format.

        Args:
            data: Raw job run records

        Returns:
            List of transformed job run records
        """
        transformed = []

        for run in data:
            start_time = run.get("start_time")
            end_time = run.get("end_time")
            duration_seconds = 0

            if start_time and end_time:
                if isinstance(start_time, (int, float)):
                    start_dt = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
                    end_dt = datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)
                else:
                    start_dt = start_time
                    end_dt = end_time
                duration_seconds = int((end_dt - start_dt).total_seconds())
            else:
                start_dt = None
                end_dt = None

            # Estimate DBU consumption based on duration
            duration_hours = duration_seconds / 3600 if duration_seconds > 0 else 0
            estimated_dbu = duration_hours * 2.0  # Base estimate: 2 DBU/hour

            from costpulse.core.constants import DBU_RATES

            dbu_rate = DBU_RATES.get("JOBS_COMPUTE", 0.15)
            cost_usd = estimated_dbu * dbu_rate

            num_tasks = len(run.get("tasks", []))
            if num_tasks == 0:
                num_tasks = 1

            transformed.append(
                {
                    "job_id": run["job_id"],
                    "run_id": run["run_id"],
                    "job_name": run.get("job_name"),
                    "creator_email": run.get("creator_user_name"),
                    "cluster_id": run.get("cluster_id"),
                    "run_type": run.get("run_type"),
                    "state": run.get("state"),
                    "result_state": run.get("result_state"),
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "duration_seconds": duration_seconds,
                    "dbu_consumed": estimated_dbu,
                    "cost_usd": cost_usd,
                    "num_tasks": num_tasks,
                    "tags": run.get("tags", {}),
                    "schedule": run.get("schedule"),
                }
            )

        return transformed
