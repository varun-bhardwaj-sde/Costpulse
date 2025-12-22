"""Calculate costs from DBU usage."""

from decimal import Decimal
from typing import Dict, Optional

from costpulse.core.constants import DBU_RATES, VM_COSTS


class CostCalculator:
    """Calculate costs from DBU usage."""

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None):
        """Initialize the cost calculator.

        Args:
            custom_rates: Optional custom DBU rates to override defaults
        """
        self.rates = {**DBU_RATES}
        if custom_rates:
            self.rates.update(custom_rates)

    def calculate_dbu_cost(
        self, sku_name: str, dbu_count: float, photon_enabled: bool = False
    ) -> Decimal:
        """Calculate cost from DBU count.

        Args:
            sku_name: SKU name (e.g., "JOBS_COMPUTE")
            dbu_count: Number of DBUs consumed
            photon_enabled: Whether Photon is enabled

        Returns:
            Cost in USD
        """
        # Adjust SKU for Photon if needed
        if photon_enabled and "_PHOTON" not in sku_name:
            photon_sku = f"{sku_name}_PHOTON"
            if photon_sku in self.rates:
                sku_name = photon_sku

        rate = Decimal(str(self.rates.get(sku_name, 0.15)))
        count = Decimal(str(dbu_count))

        return rate * count

    def calculate_cluster_cost(
        self,
        sku_name: str,
        node_type: str,
        num_workers: int,
        runtime_hours: float,
        cloud: str = "AWS",
        photon_enabled: bool = False,
    ) -> Dict[str, Decimal]:
        """Calculate total cluster cost including DBU and VM costs.

        Args:
            sku_name: SKU name
            node_type: VM instance type
            num_workers: Number of worker nodes
            runtime_hours: Hours the cluster ran
            cloud: Cloud provider (AWS, AZURE, GCP)
            photon_enabled: Whether Photon is enabled

        Returns:
            Dictionary with dbu_cost, vm_cost, and total_cost
        """
        # DBU cost
        dbu_per_hour = self._get_dbu_per_hour(sku_name, num_workers, photon_enabled)
        dbu_cost = self.calculate_dbu_cost(
            sku_name, dbu_per_hour * runtime_hours, photon_enabled
        )

        # VM cost
        vm_rate = Decimal(str(VM_COSTS.get(cloud, {}).get(node_type, 0)))
        vm_cost = vm_rate * Decimal(str(runtime_hours)) * Decimal(num_workers + 1)

        return {"dbu_cost": dbu_cost, "vm_cost": vm_cost, "total_cost": dbu_cost + vm_cost}

    def _get_dbu_per_hour(
        self, sku_name: str, num_workers: int, photon_enabled: bool
    ) -> float:
        """Estimate DBU consumption per hour.

        Args:
            sku_name: SKU name
            num_workers: Number of worker nodes
            photon_enabled: Whether Photon is enabled

        Returns:
            Estimated DBUs per hour
        """
        # Base DBU per node (varies by instance type, simplified here)
        base_dbu = 2.0 if photon_enabled else 1.0
        return base_dbu * (num_workers + 1)  # Workers + driver

    def estimate_query_cost(
        self,
        warehouse_type: str,
        estimated_duration_seconds: float,
        cluster_size: str = "Small",
    ) -> Decimal:
        """Estimate cost for a SQL query.

        Args:
            warehouse_type: Warehouse type (e.g., "SERVERLESS", "CLASSIC")
            estimated_duration_seconds: Estimated query duration in seconds
            cluster_size: Warehouse cluster size

        Returns:
            Estimated cost in USD
        """
        # Size multipliers
        size_multipliers = {
            "2X-Small": 0.5,
            "X-Small": 0.75,
            "Small": 1.0,
            "Medium": 2.0,
            "Large": 4.0,
            "X-Large": 8.0,
            "2X-Large": 16.0,
            "3X-Large": 32.0,
            "4X-Large": 64.0,
        }

        base_sku = (
            "SQL_COMPUTE_SERVERLESS"
            if "SERVERLESS" in warehouse_type.upper()
            else "SQL_COMPUTE"
        )
        base_rate = Decimal(str(self.rates.get(base_sku, 0.22)))

        multiplier = Decimal(str(size_multipliers.get(cluster_size, 1.0)))
        hours = Decimal(str(estimated_duration_seconds / 3600))

        return base_rate * multiplier * hours
