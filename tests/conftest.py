"""Load mapping/entity modules without starting an account or a HA instance."""

import sys
import types
from unittest.mock import AsyncMock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/midea_auto_cloud"
package = types.ModuleType("midea_auto_cloud")
package.__path__ = [str(ROOT)]
package.load_device_config = AsyncMock()
sys.modules[package.__name__] = package
# Entities need the coordinator type annotation, not cloud networking, in these tests.
coordinator = types.ModuleType("midea_auto_cloud.data_coordinator")
coordinator.MideaDataUpdateCoordinator = type("MideaDataUpdateCoordinator", (), {})
sys.modules[coordinator.__name__] = coordinator
