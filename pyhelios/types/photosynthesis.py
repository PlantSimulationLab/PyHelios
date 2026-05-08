"""
Photosynthesis parameter structures and data classes for PyHelios.

This module provides Python data structures that mirror the C++ parameter
classes used by the PhotosynthesisModel plugin, with proper defaults and
validation support.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
import math

# Known species in the photosynthesis library (21 species with aliases)
PHOTOSYNTHESIS_SPECIES = [
    "Almond", "Apple", "Cherry", "Prune", "Pear", 
    "PistachioFemale", "PistachioMale", "Walnut",
    "Grape",  # cv. Cabernet Sauvignon
    "Elderberry", "Toyon", "Big_Leaf_Maple", "Western_Redbud", "Baylaurel", "Olive",
    "EasternRedbudSunlit", "EasternRedbudShaded"
]

# Species aliases for case-insensitive and format-flexible lookup
SPECIES_ALIASES = {
    # Standard names (already in PHOTOSYNTHESIS_SPECIES)
    "almond": "Almond",
    "apple": "Apple", 
    "cherry": "Cherry",
    "prune": "Prune",
    "pear": "Pear",
    "pistachiofemale": "PistachioFemale",
    "pistachiomale": "PistachioMale",
    "walnut": "Walnut",
    "grape": "Grape",
    "elderberry": "Elderberry",
    "toyon": "Toyon",
    "big_leaf_maple": "Big_Leaf_Maple",
    "western_redbud": "Western_Redbud",
    "baylaurel": "Baylaurel",
    "olive": "Olive",
    "easternredbudsunlit": "EasternRedbudSunlit",
    "easternredbudshaded": "EasternRedbudShaded",
    
    # Common aliases and variations
    "bigleafmaple": "Big_Leaf_Maple",
    "bigmaple": "Big_Leaf_Maple",
    "westernredbud": "Western_Redbud",
    "redbud": "Western_Redbud",
    "easternredbud": "EasternRedbudSunlit",  # Default to sunlit
    "pistachio": "PistachioFemale",  # Default to female
    "cabernet": "Grape",
    "cabernetSauvignon": "Grape",
    "grapevine": "Grape"
}


@dataclass
class PhotosyntheticTemperatureResponseParameters:
    """
    Temperature response parameters for photosynthetic processes.
    
    These parameters define how photosynthetic rates vary with temperature
    using the modified Arrhenius equation.
    
    Attributes:
        value_at_25C: Value of the parameter at 25°C
        dHa: Activation energy (rate of increase parameter)
        dHd: Deactivation energy (rate of decrease parameter)  
        Topt: Optimum temperature in Kelvin (10000K means no optimum)
    """
    value_at_25C: float = 100.0
    dHa: float = 60.0
    dHd: float = 600.0
    Topt: float = 10000.0  # Very high = no temperature optimum
    
    def __post_init__(self):
        """Validate parameter values after initialization."""
        if not math.isfinite(self.value_at_25C):
            raise ValueError("value_at_25C must be finite")
        if not math.isfinite(self.dHa) or self.dHa < 0:
            raise ValueError("dHa must be finite and non-negative")
        if not math.isfinite(self.dHd) or self.dHd < 0:
            raise ValueError("dHd must be finite and non-negative")
        if not math.isfinite(self.Topt) or self.Topt < 0:
            raise ValueError("Topt must be finite and non-negative")


@dataclass
class EmpiricalModelCoefficients:
    """
    Empirical photosynthesis model coefficients.
    
    This model uses empirical relationships to estimate photosynthetic
    rates based on environmental conditions.
    
    Attributes:
        Tref: Reference temperature (K)
        Ci_ref: Reference CO2 concentration (μmol CO2/mol air)
        Asat: Light-saturated photosynthetic rate (μmol/m²/s)
        theta: Half-saturation light level (W/m²)
        Tmin: Minimum temperature for photosynthesis (K)
        Topt: Optimum temperature for photosynthesis (K)
        q: Temperature response parameter (unitless)
        R: Respiration temperature coefficient (μmol·K^0.5/m²/s)
        ER: Respiration activation energy (1/K)
        kC: CO2 response coefficient (unitless)
    """
    Tref: float = 298.0      # K
    Ci_ref: float = 290.0    # μmol CO2/mol air
    Asat: float = 18.18      # μmol/m²/s
    theta: float = 62.03     # W/m²
    Tmin: float = 290.0      # K
    Topt: float = 303.0      # K  
    q: float = 0.344         # unitless
    R: float = 1.663e5       # μmol·K^0.5/m²/s
    ER: float = 3740.0       # 1/K
    kC: float = 0.791        # unitless
    
    def __post_init__(self):
        """Validate parameter values after initialization."""
        if self.Tref <= 0:
            raise ValueError("Reference temperature must be positive")
        if self.Ci_ref <= 0:
            raise ValueError("Reference CO2 concentration must be positive")
        if self.Asat < 0:
            raise ValueError("Light-saturated photosynthetic rate cannot be negative")
        if self.theta <= 0:
            raise ValueError("Half-saturation light level must be positive")
        if self.Tmin <= 0:
            raise ValueError("Minimum temperature must be positive")
        if self.Topt <= 0:
            raise ValueError("Optimum temperature must be positive")
        if self.Tmin >= self.Topt:
            raise ValueError("Minimum temperature must be less than optimum temperature")
        if self.q <= 0:
            raise ValueError("Temperature response parameter must be positive")
        if self.R < 0:
            raise ValueError("Respiration coefficient cannot be negative")
        if self.ER < 0:
            raise ValueError("Respiration activation energy cannot be negative")
        if self.kC < 0:
            raise ValueError("CO2 response coefficient cannot be negative")
    
    def to_array(self) -> List[float]:
        """Convert to float array for C++ interface."""
        return [
            self.Tref, self.Ci_ref, self.Asat, self.theta, self.Tmin,
            self.Topt, self.q, self.R, self.ER, self.kC
        ]
    
    @classmethod
    def from_array(cls, coefficients: List[float]) -> 'EmpiricalModelCoefficients':
        """Create from float array (from C++ interface)."""
        if len(coefficients) < 10:
            raise ValueError("Need at least 10 coefficients for empirical model")
        return cls(
            Tref=coefficients[0], Ci_ref=coefficients[1], Asat=coefficients[2],
            theta=coefficients[3], Tmin=coefficients[4], Topt=coefficients[5],
            q=coefficients[6], R=coefficients[7], ER=coefficients[8], kC=coefficients[9]
        )


@dataclass  
class FarquharModelCoefficients:
    """
    Farquhar-von Caemmerer-Berry photosynthesis model coefficients.
    
    This model provides a mechanistic description of leaf photosynthesis
    based on biochemical limitations and temperature responses.
    
    Core Parameters (at 25°C):
        Vcmax: Maximum carboxylation rate (μmol/m²/s, -1 = uninitialized)
        Jmax: Maximum electron transport rate (μmol/m²/s, -1 = uninitialized)  
        alpha: Quantum efficiency of photosystem II (μmol electrons/μmol photons)
        Rd: Dark respiration rate (μmol/m²/s, -1 = uninitialized)
        O: Ambient oxygen concentration (mmol/mol)
        TPU_flag: Enable triose phosphate utilization limitation (0/1)
        
    Temperature Response Parameters:
        c_*: Scaling factor for Arrhenius equation
        dH_*: Activation energy for temperature response
    """
    # Core parameters at 25°C
    Vcmax: float = -1.0      # μmol/m²/s (uninitialized)
    Jmax: float = -1.0       # μmol/m²/s (uninitialized)
    alpha: float = -1.0      # unitless (uninitialized)
    Rd: float = -1.0         # μmol/m²/s (uninitialized)
    O: float = 213.5         # ambient oxygen concentration (mmol/mol)
    TPU_flag: int = 0        # enable TPU limitation
    
    # Temperature scaling factors (c_*)
    c_Rd: float = 18.72
    c_Vcmax: float = 26.35
    c_Jmax: float = 18.86
    c_Gamma: float = 19.02
    c_Kc: float = 38.05
    c_Ko: float = 20.30
    
    # Activation energies (dH_*)  
    dH_Rd: float = 46.39
    dH_Vcmax: float = 65.33
    dH_Jmax: float = 46.36
    dH_Gamma: float = 37.83
    dH_Kc: float = 79.43
    dH_Ko: float = 36.38

    # Mesophyll conductance gm (helios-core 1.3.72+). The default math.inf reproduces
    # the legacy Cc = Ci behaviour (no mesophyll diffusion limitation). When packed into
    # the flat coefficient array, slots [18..21] are (gm_at_25C, dHa, Topt_C, dHd) using
    # the same -1 sentinel convention as the C4 model: dHa < 0 → constant gm with no
    # temperature response.
    gm_at_25C: float = float('inf')   # mol CO2 / m^2 / s / bar
    dHa_gm: float = -1.0              # kJ/mol; -1 disables temperature response
    Topt_gm_C: float = -1.0           # Celsius; -1 → monotonic Arrhenius
    dHd_gm: float = -1.0              # kJ/mol; -1 → default

    # Temperature response parameter containers
    _vcmax_temp_response: Optional[PhotosyntheticTemperatureResponseParameters] = field(default=None, init=False)
    _jmax_temp_response: Optional[PhotosyntheticTemperatureResponseParameters] = field(default=None, init=False)
    _rd_temp_response: Optional[PhotosyntheticTemperatureResponseParameters] = field(default=None, init=False)
    _alpha_temp_response: Optional[PhotosyntheticTemperatureResponseParameters] = field(default=None, init=False)
    _theta_temp_response: Optional[PhotosyntheticTemperatureResponseParameters] = field(default=None, init=False)
    
    def __post_init__(self):
        """Validate parameter values after initialization."""
        if self.O <= 0:
            raise ValueError("Oxygen concentration must be positive")
        if self.TPU_flag not in (0, 1):
            raise ValueError("TPU_flag must be 0 or 1")
        
        # Validate temperature parameters
        for param_name, value in [
            ('c_Rd', self.c_Rd), ('c_Vcmax', self.c_Vcmax), ('c_Jmax', self.c_Jmax),
            ('c_Gamma', self.c_Gamma), ('c_Kc', self.c_Kc), ('c_Ko', self.c_Ko),
            ('dH_Rd', self.dH_Rd), ('dH_Vcmax', self.dH_Vcmax), ('dH_Jmax', self.dH_Jmax),
            ('dH_Gamma', self.dH_Gamma), ('dH_Kc', self.dH_Kc), ('dH_Ko', self.dH_Ko)
        ]:
            if not math.isfinite(value):
                raise ValueError(f"Temperature parameter {param_name} must be finite")
    
    def setVcmax(self, vcmax_at_25c: float, dha: Optional[float] = None, 
                 topt: Optional[float] = None, dhd: Optional[float] = None) -> None:
        """Set Vcmax with temperature response (mimics C++ overloads)."""
        if dha is None:
            # 1-parameter version
            self._vcmax_temp_response = PhotosyntheticTemperatureResponseParameters(vcmax_at_25c)
        elif topt is None:
            # 2-parameter version
            self._vcmax_temp_response = PhotosyntheticTemperatureResponseParameters(vcmax_at_25c, dha)
        elif dhd is None:
            # 3-parameter version
            self._vcmax_temp_response = PhotosyntheticTemperatureResponseParameters(vcmax_at_25c, dha, topt)
        else:
            # 4-parameter version
            self._vcmax_temp_response = PhotosyntheticTemperatureResponseParameters(vcmax_at_25c, dha, dhd, topt)
        
        self.Vcmax = vcmax_at_25c
    
    def setJmax(self, jmax_at_25c: float, dha: Optional[float] = None,
                topt: Optional[float] = None, dhd: Optional[float] = None) -> None:
        """Set Jmax with temperature response (mimics C++ overloads)."""
        if dha is None:
            self._jmax_temp_response = PhotosyntheticTemperatureResponseParameters(jmax_at_25c)
        elif topt is None:
            self._jmax_temp_response = PhotosyntheticTemperatureResponseParameters(jmax_at_25c, dha)
        elif dhd is None:
            self._jmax_temp_response = PhotosyntheticTemperatureResponseParameters(jmax_at_25c, dha, topt)
        else:
            self._jmax_temp_response = PhotosyntheticTemperatureResponseParameters(jmax_at_25c, dha, dhd, topt)
        
        self.Jmax = jmax_at_25c
    
    def setRd(self, rd_at_25c: float, dha: Optional[float] = None,
              topt: Optional[float] = None, dhd: Optional[float] = None) -> None:
        """Set dark respiration with temperature response (mimics C++ overloads)."""
        if dha is None:
            self._rd_temp_response = PhotosyntheticTemperatureResponseParameters(rd_at_25c)
        elif topt is None:
            self._rd_temp_response = PhotosyntheticTemperatureResponseParameters(rd_at_25c, dha)
        elif dhd is None:
            self._rd_temp_response = PhotosyntheticTemperatureResponseParameters(rd_at_25c, dha, topt)
        else:
            self._rd_temp_response = PhotosyntheticTemperatureResponseParameters(rd_at_25c, dha, dhd, topt)
        
        self.Rd = rd_at_25c
    
    def setQuantumEfficiency_alpha(self, alpha_at_25c: float, dha: Optional[float] = None,
                                   topt: Optional[float] = None, dhd: Optional[float] = None) -> None:
        """Set quantum efficiency with temperature response (mimics C++ overloads).""" 
        if dha is None:
            self._alpha_temp_response = PhotosyntheticTemperatureResponseParameters(alpha_at_25c)
        elif topt is None:
            self._alpha_temp_response = PhotosyntheticTemperatureResponseParameters(alpha_at_25c, dha)
        elif dhd is None:
            self._alpha_temp_response = PhotosyntheticTemperatureResponseParameters(alpha_at_25c, dha, topt)
        else:
            self._alpha_temp_response = PhotosyntheticTemperatureResponseParameters(alpha_at_25c, dha, dhd, topt)
        
        self.alpha = alpha_at_25c
    
    def setLightResponseCurvature_theta(self, theta_at_25c: float, dha: Optional[float] = None,
                                        topt: Optional[float] = None, dhd: Optional[float] = None) -> None:
        """Set light response curvature with temperature response (mimics C++ overloads)."""
        if dha is None:
            self._theta_temp_response = PhotosyntheticTemperatureResponseParameters(theta_at_25c)
        elif topt is None:
            self._theta_temp_response = PhotosyntheticTemperatureResponseParameters(theta_at_25c, dha)
        elif dhd is None:
            self._theta_temp_response = PhotosyntheticTemperatureResponseParameters(theta_at_25c, dha, topt)
        else:
            self._theta_temp_response = PhotosyntheticTemperatureResponseParameters(theta_at_25c, dha, dhd, topt)
    
    def getVcmaxTempResponse(self) -> PhotosyntheticTemperatureResponseParameters:
        """Get Vcmax temperature response parameters."""
        if self._vcmax_temp_response is None:
            return PhotosyntheticTemperatureResponseParameters(self.Vcmax if self.Vcmax > 0 else 100.0)
        return self._vcmax_temp_response
    
    def getJmaxTempResponse(self) -> PhotosyntheticTemperatureResponseParameters:
        """Get Jmax temperature response parameters."""
        if self._jmax_temp_response is None:
            return PhotosyntheticTemperatureResponseParameters(self.Jmax if self.Jmax > 0 else 100.0)
        return self._jmax_temp_response
    
    def getRdTempResponse(self) -> PhotosyntheticTemperatureResponseParameters:
        """Get dark respiration temperature response parameters."""
        if self._rd_temp_response is None:
            return PhotosyntheticTemperatureResponseParameters(self.Rd if self.Rd > 0 else 1.0)
        return self._rd_temp_response
    
    def getQuantumEfficiencyTempResponse(self) -> PhotosyntheticTemperatureResponseParameters:
        """Get quantum efficiency temperature response parameters."""
        if self._alpha_temp_response is None:
            return PhotosyntheticTemperatureResponseParameters(self.alpha if self.alpha > 0 else 0.3)
        return self._alpha_temp_response
    
    def getLightResponseCurvatureTempResponse(self) -> PhotosyntheticTemperatureResponseParameters:
        """Get light response curvature temperature response parameters.""" 
        if self._theta_temp_response is None:
            return PhotosyntheticTemperatureResponseParameters(0.7)
        return self._theta_temp_response
    
    def to_array(self) -> List[float]:
        """Convert to float array for C++ interface (22 floats; helios-core 1.3.72+).

        Slots 0..17 are the legacy Farquhar fields (Vcmax/Jmax/alpha/Rd/O/TPU_flag plus
        the 12 c_*/dH_* temperature constants). Slots 18..21 carry the mesophyll
        conductance gm temperature response: (gm_at_25C, dHa, Topt_C, dHd) using the
        -1 sentinel convention (dHa < 0 → constant gm with no temperature response,
        Topt_C < 0 → monotonic Arrhenius, dHd < 0 → default deactivation energy).
        Default ``gm_at_25C`` is ``+inf`` which reproduces the legacy ``Cc = Ci`` behaviour.
        """
        return [
            self.Vcmax, self.Jmax, self.alpha, self.Rd, self.O, float(self.TPU_flag),
            # Temperature scaling factors
            self.c_Vcmax, self.dH_Vcmax, self.c_Jmax, self.dH_Jmax,
            self.c_Rd, self.dH_Rd, self.c_Kc, self.dH_Kc,
            self.c_Ko, self.dH_Ko, self.c_Gamma, self.dH_Gamma,
            # Mesophyll conductance gm temperature response (1.3.72+)
            self.gm_at_25C, self.dHa_gm, self.Topt_gm_C, self.dHd_gm,
        ]

    @classmethod
    def from_array(cls, coefficients: List[float]) -> 'FarquharModelCoefficients':
        """Create from float array (from C++ interface).

        Accepts both the legacy 18-float layout (pre-1.3.72) and the 22-float layout
        with mesophyll conductance gm in slots 18..21. When the array is 18 floats,
        gm defaults to +infinity (legacy ``Cc = Ci`` behaviour).
        """
        if len(coefficients) < 18:
            raise ValueError("Need at least 18 coefficients for Farquhar model")

        gm_at_25C = coefficients[18] if len(coefficients) > 18 else float('inf')
        dHa_gm = coefficients[19] if len(coefficients) > 19 else -1.0
        Topt_gm_C = coefficients[20] if len(coefficients) > 20 else -1.0
        dHd_gm = coefficients[21] if len(coefficients) > 21 else -1.0

        return cls(
            Vcmax=coefficients[0], Jmax=coefficients[1], alpha=coefficients[2],
            Rd=coefficients[3], O=coefficients[4], TPU_flag=int(coefficients[5]),
            c_Vcmax=coefficients[6], dH_Vcmax=coefficients[7],
            c_Jmax=coefficients[8], dH_Jmax=coefficients[9],
            c_Rd=coefficients[10], dH_Rd=coefficients[11],
            c_Kc=coefficients[12], dH_Kc=coefficients[13],
            c_Ko=coefficients[14], dH_Ko=coefficients[15],
            c_Gamma=coefficients[16], dH_Gamma=coefficients[17],
            gm_at_25C=gm_at_25C, dHa_gm=dHa_gm, Topt_gm_C=Topt_gm_C, dHd_gm=dHd_gm,
        )


def validate_species_name(species: str) -> str:
    """
    Validate and normalize species name for photosynthesis library.
    
    Args:
        species: Species name (case insensitive, supports aliases)
        
    Returns:
        Normalized species name
        
    Raises:
        ValueError: If species is not recognized
    """
    if not species:
        raise ValueError("Species name cannot be empty")
    
    # Try exact match first (case sensitive)
    if species in PHOTOSYNTHESIS_SPECIES:
        return species
    
    # Try case-insensitive match
    species_lower = species.lower()
    if species_lower in SPECIES_ALIASES:
        return SPECIES_ALIASES[species_lower]
    
    # Try case-insensitive match against known species
    for known_species in PHOTOSYNTHESIS_SPECIES:
        if known_species.lower() == species_lower:
            return known_species
    
    # Species not found - provide helpful error message
    available_species = sorted(set(list(PHOTOSYNTHESIS_SPECIES) + list(SPECIES_ALIASES.keys())))
    raise ValueError(
        f"Unknown species '{species}'. Available species and aliases:\n"
        f"  {', '.join(available_species[:8])}\n"
        f"  {', '.join(available_species[8:16])}\n"
        f"  {', '.join(available_species[16:])}"
    )


def get_available_species() -> List[str]:
    """Get list of available species in the photosynthesis library."""
    return sorted(PHOTOSYNTHESIS_SPECIES.copy())


def get_species_aliases() -> dict:
    """Get dictionary of species aliases."""
    return SPECIES_ALIASES.copy()