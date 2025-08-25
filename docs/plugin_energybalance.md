# Energy Balance Plugin Documentation {#EnergyBalanceDoc}

## Overview

The Energy Balance plugin provides GPU-accelerated thermal modeling and surface temperature calculations for plant canopies and individual primitives. It computes surface temperatures based on local energy balance equations, including radiation absorption, convection, and transpiration processes.

The plugin supports both steady-state and dynamic (time-stepping) calculations, making it suitable for a wide range of thermal modeling applications from instantaneous temperature estimation to long-term thermal dynamics simulation.

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **GPU**: NVIDIA GPU with CUDA support (required)
- **Dependencies**: CUDA Toolkit installed
- **Memory**: Scales with geometry complexity and simulation duration

## Installation

The Energy Balance plugin is included in the following build profiles:
- `gpu-accelerated`: High-performance GPU features
- `research`: Comprehensive research suite  
- `physics`: Comprehensive physics modeling

### Build with Energy Balance

```bash
# Using profile
build_scripts/build_helios --interactive

# Explicit selection
build_scripts/build_helios --plugins energybalance

# Check if available
python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
```

### Verify Installation

```python
from pyhelios import EnergyBalanceModel
from pyhelios.plugins.registry import get_plugin_registry

registry = get_plugin_registry()
if registry.is_plugin_available('energybalance'):
    print("Energy Balance plugin is available")
else:
    print("Energy Balance plugin is not available")
```

## Quick Start

```python
from pyhelios import Context, EnergyBalanceModel
from pyhelios.types import *

# Create context and add geometry
with Context() as context:
    # Add a patch to simulate
    patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
    
    with EnergyBalanceModel(context) as energy_balance:
        # Add radiation band for flux calculations
        energy_balance.addRadiationBand("SW")  # Shortwave radiation
        
        # Run steady-state energy balance
        energy_balance.run()
        print("Steady-state energy balance complete")
        
        # Run dynamic simulation with 60-second timestep
        energy_balance.run(dt=60.0)
        print("Dynamic energy balance complete")
```

## API Reference

### EnergyBalanceModel Class

#### Constructor

```python
EnergyBalanceModel(context: Context)
```

Initialize EnergyBalanceModel with a Helios context.

**Parameters:**
- `context`: Active Helios Context instance

**Raises:**
- `TypeError`: If context is not a Context instance
- `EnergyBalanceModelError`: If energy balance plugin not available
- `RuntimeError`: If initialization fails

#### Core Methods

##### run()

```python
run(uuids: Optional[List[int]] = None, dt: Optional[float] = None) -> None
```

Run the energy balance model with flexible execution modes.

**Parameters:**
- `uuids`: Optional list of primitive UUIDs to process. If None, processes all primitives.
- `dt`: Optional timestep in seconds for dynamic simulation. If None, runs steady-state.

**Execution Modes:**
- `run()` - Steady state for all primitives
- `run(dt=60.0)` - Dynamic with timestep for all primitives
- `run(uuids=[1, 2, 3])` - Steady state for specific primitives
- `run(uuids=[1, 2, 3], dt=60.0)` - Dynamic with timestep for specific primitives

**Raises:**
- `ValueError`: If parameters are invalid
- `EnergyBalanceModelError`: If energy balance calculation fails

**Example:**
```python
# Steady state for all primitives
energy_balance.run()

# Dynamic simulation with 60-second timestep
energy_balance.run(dt=60.0)

# Steady state for specific patches
energy_balance.run(uuids=[patch1_uuid, patch2_uuid])

# Dynamic simulation for specific patches
energy_balance.run(uuids=[patch1_uuid, patch2_uuid], dt=30.0)
```

##### addRadiationBand()

```python
addRadiationBand(band: Union[str, List[str]]) -> None
```

Add a radiation band or bands for absorbed flux calculations.

**Parameters:**
- `band`: Name of radiation band (e.g., "SW", "PAR", "NIR", "LW") or list of band names

**Raises:**
- `ValueError`: If band name is invalid
- `EnergyBalanceModelError`: If operation fails

**Example:**
```python
energy_balance.addRadiationBand("SW")  # Single band
energy_balance.addRadiationBand(["SW", "LW"])  # Multiple bands
```



##### enableAirEnergyBalance()

```python
enableAirEnergyBalance(canopy_height_m: Optional[float] = None, 
                     reference_height_m: Optional[float] = None) -> None
```

Enable air energy balance model for canopy-scale thermal calculations.

**Parameters:**
- `canopy_height_m`: Optional canopy height in meters. If not provided, computed automatically.
- `reference_height_m`: Optional reference height in meters where ambient conditions are measured.

**Raises:**
- `ValueError`: If parameters are invalid
- `EnergyBalanceModelError`: If operation fails

**Example:**
```python
# Automatic canopy height detection
energy_balance.enableAirEnergyBalance()

# Manual canopy and reference heights
energy_balance.enableAirEnergyBalance(canopy_height_m=5.0, reference_height_m=10.0)
```

##### evaluateAirEnergyBalance()

```python
evaluateAirEnergyBalance(dt_sec: float, time_advance_sec: float,
                        uuids: Optional[List[int]] = None) -> None
```

Advance the air energy balance over time.

**Parameters:**
- `dt_sec`: Timestep in seconds for integration
- `time_advance_sec`: Total time to advance in seconds (must be >= dt_sec)
- `uuids`: Optional list of primitive UUIDs. If None, processes all primitives.

**Raises:**
- `ValueError`: If parameters are invalid
- `EnergyBalanceModelError`: If operation fails

**Example:**
```python
# Advance air energy balance by 1 hour using 60-second timesteps
energy_balance.evaluateAirEnergyBalance(dt_sec=60.0, time_advance_sec=3600.0)

# Advance for specific primitives
energy_balance.evaluateAirEnergyBalance(
    dt_sec=30.0, time_advance_sec=1800.0, uuids=[patch1_uuid, patch2_uuid])
```

#### Utility Methods

##### optionalOutputPrimitiveData()

```python
optionalOutputPrimitiveData(label: str) -> None
```

Add optional output primitive data to the Context.

**Parameters:**
- `label`: Name of data field to add (e.g., "vapor_pressure_deficit")

**Example:**
```python
energy_balance.optionalOutputPrimitiveData("vapor_pressure_deficit")
energy_balance.optionalOutputPrimitiveData("net_radiation")
```

##### printDefaultValueReport()

```python
printDefaultValueReport(uuids: Optional[List[int]] = None) -> None
```

Print diagnostic report of default input value usage.

**Parameters:**
- `uuids`: Optional list of primitive UUIDs to report on. If None, reports on all primitives.

##### enableMessages() / disableMessages()

```python
enableMessages() -> None
disableMessages() -> None
```

Control console output from the energy balance model.

## Examples

### Basic Energy Balance Calculation

```python
from pyhelios import Context, EnergyBalanceModel
from pyhelios.types import *

with Context() as context:
    # Add geometry
    patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
    
    with EnergyBalanceModel(context) as energy_balance:
        # Configure radiation bands
        energy_balance.addRadiationBand("SW")
        
        # Run steady-state calculation
        energy_balance.run()
        print("Steady-state energy balance complete")
        
        # Check primitive data for temperature
        temperature = context.getPrimitiveData(patch_uuid, "temperature")
        print(f"Surface temperature: {temperature[0]:.2f} K")
```

### Dynamic Thermal Simulation

```python
from pyhelios import Context, EnergyBalanceModel
from pyhelios.types import *
import numpy as np

with Context() as context:
    # Create canopy geometry
    patch_uuids = []
    for i in range(10):
        for j in range(10):
            uuid = context.addPatch(
                center=vec3(i*0.5, j*0.5, 2.0), 
                size=vec2(0.4, 0.4)
            )
            patch_uuids.append(uuid)
    
    with EnergyBalanceModel(context) as energy_balance:
        # Configure model
        energy_balance.addRadiationBand(["SW", "LW"])
        
        # Run time series simulation
        timesteps = np.arange(0, 3600, 60)  # 1 hour, 60s steps
        temperatures = []
        
        for t in timesteps:
            energy_balance.run(dt=60.0)
            
            # Collect temperature data
            temp_data = []
            for uuid in patch_uuids[:5]:  # Sample first 5 patches
                temp = context.getPrimitiveData(uuid, "temperature")
                temp_data.append(temp[0])
            temperatures.append(np.mean(temp_data))
            
            print(f"t={t:4.0f}s: Mean temperature = {temperatures[-1]:.2f} K")
```

### Air Energy Balance Modeling

```python
from pyhelios import Context, EnergyBalanceModel
from pyhelios.types import *

with Context() as context:
    # Create layered canopy
    for layer in range(3):  # 3 canopy layers
        z_height = (layer + 1) * 1.5
        for i in range(8):
            for j in range(8):
                context.addPatch(
                    center=vec3(i*0.6, j*0.6, z_height),
                    size=vec2(0.5, 0.5)
                )
    
    with EnergyBalanceModel(context) as energy_balance:
        # Configure radiation and air model
        energy_balance.addRadiationBand("SW")
        energy_balance.enableAirEnergyBalance(
            canopy_height_m=4.5,    # 3 layers * 1.5m
            reference_height_m=10.0  # 10m reference height
        )
        
        # Add optional outputs
        energy_balance.optionalOutputPrimitiveData("air_temperature")
        energy_balance.optionalOutputPrimitiveData("air_humidity")
        
        # Run air energy balance simulation
        energy_balance.evaluateAirEnergyBalance(
            dt_sec=60.0,           # 1-minute timesteps
            time_advance_sec=7200.0 # 2-hour simulation
        )
        
        print("Air energy balance simulation complete")
```

### Integration with Radiation Modeling

```python
from pyhelios import Context, RadiationModel, EnergyBalanceModel
from pyhelios.types import *

with Context() as context:
    # Add geometry
    for i in range(5):
        for j in range(5):
            context.addPatch(center=vec3(i, j, 2.0), size=vec2(0.8, 0.8))
    
    # First run radiation model to calculate absorbed flux
    with RadiationModel(context) as radiation:
        radiation.addRadiationBand("SW")
        source_id = radiation.addCollimatedRadiationSource()
        radiation.setSourceFlux(source_id, "SW", 1000.0)  # 1000 W/m²
        radiation.runBand("SW")
    
    # Then run energy balance using radiation results
    with EnergyBalanceModel(context) as energy_balance:
        # Use the same radiation band
        energy_balance.addRadiationBand("SW")
        
        # Enable air energy balance
        energy_balance.enableAirEnergyBalance()
        
        # Run thermal simulation
        energy_balance.run(dt=300.0)  # 5-minute timestep
        
        print("Coupled radiation-thermal simulation complete")
```

### Error Handling

```python
from pyhelios import Context, EnergyBalanceModel, EnergyBalanceModelError

with Context() as context:
    try:
        with EnergyBalanceModel(context) as energy_balance:
            # Configure and run simulation
            energy_balance.addRadiationBand("SW")
            energy_balance.run()
            
    except EnergyBalanceModelError as e:
        print(f"Energy balance error: {e}")
        # Error messages include rebuild instructions
        
    except ValueError as e:
        print(f"Parameter error: {e}")
```

### Parameter Validation Examples

```python
with Context() as context:
    with EnergyBalanceModel(context) as energy_balance:
        # These will raise ValueError with helpful messages
        
        # Invalid timestep
        try:
            energy_balance.run(dt=-1.0)
        except ValueError as e:
            print(f"Invalid timestep: {e}")
        
        # Invalid air energy balance parameters
        try:
            energy_balance.enableAirEnergyBalance(canopy_height_m=-5.0)
        except ValueError as e:
            print(f"Invalid canopy height: {e}")
        
        # Invalid radiation band
        try:
            energy_balance.addRadiationBand("")
        except ValueError as e:
            print(f"Invalid band name: {e}")
```

## Troubleshooting

### Plugin Not Available

If you see "EnergyBalanceModel not available" errors:

1. Check plugin status:
   ```bash
   python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
   ```

2. Rebuild with energy balance plugin:
   ```bash
   build_scripts/build_helios --clean --plugins energybalance
   ```

3. Verify CUDA installation:
   ```bash
   nvidia-smi  # Check GPU status
   nvcc --version  # Check CUDA compiler
   ```

### Build Errors

Common build issues:

- **Missing CUDA**: Install CUDA Toolkit from NVIDIA
- **GPU compatibility**: Energy balance requires CUDA-capable GPU
- **Memory issues**: Ensure sufficient GPU memory for geometry size
- **CMake errors**: Verify CMake version and CUDA paths

### Runtime Errors

- **Parameter validation errors**: Check parameter types, ranges, and combinations
- **CUDA errors**: Verify GPU memory availability and CUDA driver compatibility
- **Context errors**: Ensure Context contains geometry before running energy balance
- **Memory errors**: Use context managers for proper cleanup

### Performance Issues

- **Large geometry**: Energy balance computation scales with primitive count
- **Dynamic simulations**: Small timesteps increase computation time
- **Air energy balance**: Additional computational overhead for canopy-scale modeling
- **Memory usage**: GPU memory scales with geometry complexity

## Performance Notes

- Energy balance computations are GPU-accelerated using CUDA
- Performance scales approximately linearly with primitive count
- Dynamic simulations require more computation than steady-state
- Air energy balance adds computational overhead but provides canopy-scale modeling
- Memory usage is primarily on GPU, scaling with geometry size and simulation duration

## Limitations

- Requires NVIDIA GPU with CUDA support
- GPU memory limits maximum geometry complexity
- Dynamic timesteps must be positive and reasonable for physical simulation
- Air energy balance requires canopy geometry for meaningful results
- Integration with RadiationModel provides best results for absorbed flux calculations

## Advanced Usage

### Custom Output Data Fields

The energy balance model can output various diagnostic quantities:

```python
# Available optional output data
output_fields = [
    "vapor_pressure_deficit",
    "net_radiation", 
    "sensible_heat_flux",
    "latent_heat_flux",
    "boundary_layer_conductance",
    "air_temperature",
    "air_humidity"
]

for field in output_fields:
    energy_balance.optionalOutputPrimitiveData(field)
```

### Multi-Scale Modeling

```python
# Combine surface and air energy balance for comprehensive modeling
energy_balance.enableAirEnergyBalance(canopy_height_m=6.0, reference_height_m=15.0)

# Run surface energy balance
energy_balance.run(dt=60.0)

# Then advance air energy balance
energy_balance.evaluateAirEnergyBalance(dt_sec=60.0, time_advance_sec=3600.0)
```

### Default Value Diagnostics

```python
# Check which primitives are using default parameter values
energy_balance.printDefaultValueReport()

# This helps identify where additional parameter specification might improve results
```