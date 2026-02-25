"""Predictive cost forecasting service using time-series analysis."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.cost_record import CostRecord
from costpulse.models.forecast import CostForecast

logger = structlog.get_logger()


class ForecastService:
    """Generate cost forecasts using Prophet or fallback to linear regression."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_forecast(
        self,
        horizon_days: int = 30,
        workspace_id: Optional[str] = None,
        team_id: Optional[str] = None,
        granularity: str = "daily",
    ) -> List[Dict[str, Any]]:
        """Generate cost forecast for the next N days.

        Args:
            horizon_days: Number of days to forecast
            workspace_id: Optional workspace filter
            team_id: Optional team filter
            granularity: daily, weekly, or monthly

        Returns:
            List of forecast data points
        """
        # Fetch historical data (90 days minimum for good forecasts)
        historical = await self._get_historical_costs(
            lookback_days=90,
            workspace_id=workspace_id,
            granularity=granularity,
        )

        if len(historical) < 14:
            logger.warning("Insufficient data for forecasting", data_points=len(historical))
            return []

        # Try Prophet first, fall back to simple methods
        try:
            forecasts = self._prophet_forecast(historical, horizon_days)
        except Exception as e:
            logger.warning("Prophet forecast failed, using linear regression", error=str(e))
            forecasts = self._linear_forecast(historical, horizon_days)

        # Persist forecasts
        for fc in forecasts:
            forecast_record = CostForecast(
                workspace_id=workspace_id,
                team_id=team_id,
                forecast_date=fc["date"],
                predicted_cost=fc["predicted_cost"],
                lower_bound=fc["lower_bound"],
                upper_bound=fc["upper_bound"],
                confidence_level=0.95,
                model_type=fc.get("model", "linear"),
                granularity=granularity,
                model_metrics=fc.get("metrics", {}),
            )
            self.session.add(forecast_record)

        await self.session.flush()
        logger.info("Forecast generated", horizon_days=horizon_days, data_points=len(forecasts))
        return forecasts

    async def _get_historical_costs(
        self,
        lookback_days: int,
        workspace_id: Optional[str] = None,
        granularity: str = "daily",
    ) -> List[Dict[str, Any]]:
        """Fetch historical cost data grouped by time period."""
        start_date = datetime.utcnow() - timedelta(days=lookback_days)

        trunc_func = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }.get(granularity, "day")

        query = (
            select(
                func.date_trunc(trunc_func, CostRecord.usage_date).label("period"),
                func.sum(CostRecord.cost_usd).label("cost"),
                func.sum(CostRecord.dbu_count).label("dbu"),
            )
            .where(CostRecord.usage_date >= start_date)
            .group_by(func.date_trunc(trunc_func, CostRecord.usage_date))
            .order_by(func.date_trunc(trunc_func, CostRecord.usage_date))
        )

        if workspace_id:
            query = query.where(CostRecord.workspace_id == workspace_id)

        result = await self.session.execute(query)
        return [
            {"date": row.period, "cost": float(row.cost), "dbu": float(row.dbu)}
            for row in result.all()
        ]

    def _prophet_forecast(
        self, historical: List[Dict], horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Generate forecast using Facebook Prophet."""
        import pandas as pd
        from prophet import Prophet

        df = pd.DataFrame(historical)
        df = df.rename(columns={"date": "ds", "cost": "y"})
        df["ds"] = pd.to_datetime(df["ds"])

        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)

        # Only return future dates
        future_forecast = forecast[forecast["ds"] > df["ds"].max()]

        return [
            {
                "date": row["ds"].to_pydatetime(),
                "predicted_cost": max(0, float(row["yhat"])),
                "lower_bound": max(0, float(row["yhat_lower"])),
                "upper_bound": float(row["yhat_upper"]),
                "model": "prophet",
                "metrics": {},
            }
            for _, row in future_forecast.iterrows()
        ]

    def _linear_forecast(
        self, historical: List[Dict], horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Simple linear regression forecast as fallback."""
        costs = np.array([h["cost"] for h in historical])
        x = np.arange(len(costs))

        # Fit linear regression
        coeffs = np.polyfit(x, costs, 1)
        slope, intercept = coeffs

        # Calculate residual standard deviation
        predicted = np.polyval(coeffs, x)
        residuals = costs - predicted
        std_dev = np.std(residuals)

        # Generate forecasts
        last_date = historical[-1]["date"]
        forecasts = []

        for i in range(1, horizon_days + 1):
            future_x = len(costs) + i - 1
            predicted_cost = max(0, slope * future_x + intercept)
            margin = 1.96 * std_dev  # 95% confidence

            if isinstance(last_date, datetime):
                forecast_date = last_date + timedelta(days=i)
            else:
                forecast_date = datetime.utcnow() + timedelta(days=i)

            forecasts.append({
                "date": forecast_date,
                "predicted_cost": float(predicted_cost),
                "lower_bound": max(0, float(predicted_cost - margin)),
                "upper_bound": float(predicted_cost + margin),
                "model": "linear",
                "metrics": {
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "std_dev": float(std_dev),
                },
            })

        return forecasts

    async def get_forecast_summary(
        self, horizon_days: int = 30
    ) -> Dict[str, Any]:
        """Get a summary of cost forecasts."""
        result = await self.session.execute(
            select(CostForecast)
            .where(CostForecast.forecast_date >= datetime.utcnow())
            .order_by(CostForecast.forecast_date)
            .limit(horizon_days)
        )
        forecasts = result.scalars().all()

        if not forecasts:
            return {"status": "no_forecasts", "data": []}

        total_predicted = sum(f.predicted_cost for f in forecasts)
        return {
            "status": "ok",
            "horizon_days": len(forecasts),
            "total_predicted_cost": total_predicted,
            "avg_daily_cost": total_predicted / len(forecasts) if forecasts else 0,
            "data": [
                {
                    "date": f.forecast_date.isoformat(),
                    "predicted": f.predicted_cost,
                    "lower": f.lower_bound,
                    "upper": f.upper_bound,
                }
                for f in forecasts
            ],
        }
