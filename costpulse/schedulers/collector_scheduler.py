"""Scheduled data collection from Databricks."""

import asyncio

import structlog

from costpulse.core.config import settings
from costpulse.models.base import get_session_ctx

logger = structlog.get_logger()


async def run_collection_cycle():
    """Run a full data collection cycle."""
    logger.info("Starting scheduled collection cycle")

    try:
        host = settings.databricks.host
        token = settings.databricks.token

        # Collect billing data
        from costpulse.collectors.system_tables import SystemTablesCollector

        billing_collector = SystemTablesCollector(host, token)
        billing_data = await billing_collector.run()
        logger.info("Billing data collected", records=len(billing_data))

        # Collect cluster data
        from costpulse.collectors.cluster_collector import ClusterCollector

        cluster_collector = ClusterCollector(host, token)
        cluster_data = await cluster_collector.run()
        logger.info("Cluster data collected", records=len(cluster_data))

        # Collect job data
        from costpulse.collectors.job_collector import JobCollector

        job_collector = JobCollector(host, token)
        job_data = await job_collector.run()
        logger.info("Job data collected", records=len(job_data))

        # Store in database
        async with get_session_ctx() as session:
            from costpulse.models.cluster import ClusterInfo
            from costpulse.models.cost_record import CostRecord

            for record in billing_data:
                session.add(CostRecord(**record))

            for cluster in cluster_data:
                session.add(
                    ClusterInfo(
                        workspace_id=settings.databricks.host,
                        **cluster,
                    )
                )

        logger.info("Collection cycle complete")

    except Exception as e:
        logger.error("Collection cycle failed", error=str(e))


async def run_analysis_cycle():
    """Run analysis: anomaly detection, recommendations, alert checks."""
    logger.info("Starting analysis cycle")

    try:
        async with get_session_ctx() as session:
            # Check alerts
            from costpulse.services.alert_service import AlertService

            alert_service = AlertService(session)
            triggered = await alert_service.check_alerts()
            if triggered:
                logger.info("Alerts triggered", count=len(triggered))

            # Generate recommendations
            from costpulse.services.recommendation_service import RecommendationService

            rec_service = RecommendationService(session)
            recs = await rec_service.generate_all_recommendations()
            logger.info("Recommendations generated", count=len(recs))

            # Detect anomalies
            from costpulse.services.anomaly_detection import AnomalyDetectionService

            anomaly_service = AnomalyDetectionService(session)
            anomalies = await anomaly_service.detect_anomalies()
            logger.info("Anomalies detected", count=len(anomalies))

        logger.info("Analysis cycle complete")

    except Exception as e:
        logger.error("Analysis cycle failed", error=str(e))


async def scheduler_loop():
    """Main scheduler loop — runs collection and analysis periodically."""
    if settings.polling_interval <= 0:
        raise ValueError(f"polling_interval must be positive, got {settings.polling_interval}")
    interval = settings.polling_interval * 60  # Convert to seconds (default: 30 min)
    logger.info("Scheduler started", interval_minutes=settings.polling_interval)

    while True:
        await run_collection_cycle()
        await run_analysis_cycle()
        await asyncio.sleep(interval)
