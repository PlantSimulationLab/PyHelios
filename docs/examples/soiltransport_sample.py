"""
Soil water infiltration with the SoilTransport plugin.

A uniform, moderately dry loam receives steady surface infiltration and drains freely at its base.
The script runs one hour of the full 3D solver and prints the near-surface water content and the
water balance: the change in stored water equals the net water that entered through the boundaries.
"""

from pyhelios import Context, SoilTransportModel, SolverType
from pyhelios.types import vec3

with Context() as context:
    with SoilTransportModel(context) as soil:
        # A 1 m x 1 m x 1 m block of soil, 20 x 20 x 40 cells. The origin is the top surface,
        # so the soil occupies -1 <= z <= 0.
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, 1))
        soil.setGridResolution(20, 20, 40)
        soil.setSolverType(SolverType.SOLVER_3D)

        soil.setSoilPropertiesFromTexture("loam")
        soil.setInitialCondition(-1.0)          # uniform pressure head [m]
        soil.setTopBoundaryFlux(2e-6)           # steady infiltration [m/s]
        soil.setBottomBoundaryFreeDrainage()

        storage_start = soil.getTotalWaterStorage()
        for step in range(60):
            soil.run(60.0)                      # advance 60 s

        print("Near-surface water content:", soil.getWaterContent(vec3(0.5, 0.5, -0.1)), "m^3/m^3")
        print("Change in storage:", soil.getTotalWaterStorage() - storage_start, "m^3")
        print("Net boundary inflow:", soil.getCumulativeBoundaryInflux(), "m^3")
