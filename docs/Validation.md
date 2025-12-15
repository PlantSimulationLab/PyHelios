\page Validation Verification and Validation

The following sections summarize past verification and validation efforts for Helios models. PyHelios provides Python bindings to these validated C++ implementations.

\tableofcontents

\section RadiationValidation Radiation Model Validation

The Helios radiation model plug-in has automated verification tests that are run each time a new version of the code is committed to GitHub. These tests include both simple "toy problem" configurations with known analytical solutions, as well as more complex canopy architectures where theoretical solutions exist for certain metrics. The tests are implemented in `plugins/radiation/tests/selfTest.cpp` and are run using the doctest framework.

\subsection RadiationModelVerificationToy "Toy Problem" Verification Tests

The radiation model has been verified against analytical solutions for several simple geometric configurations that do not involve complex canopy structures. These "toy problem" tests verify fundamental radiation transport physics including view factors, emission, reflection, and scattering.

<b>90-Degree Common-Edge Squares</b>: Two perpendicular square patches sharing a common edge are tested with both shortwave (collimated solar radiation) and longwave (thermal emission) bands. The test verifies proper handling of geometric view factors and reflection between surfaces at right angles.

<b>Black Parallel Rectangles</b>: Two parallel black rectangular patches separated by a known distance are used to test diffuse radiation exchange. The model results are compared against the analytical view factor solution for parallel rectangles, validating the Monte Carlo ray tracing accuracy for view factor calculations.

<b>Gray Parallel Rectangles</b>: An extension of the black rectangle test that includes non-unity emissivity and reflectivity values to verify proper handling of gray body radiation exchange and multiple scattering between surfaces.

<b>Sphere Radiation Source</b>: A spherical radiation source positioned above a rectangular patch tests the implementation of spherical radiation sources and verifies the geometric view factor calculation between a sphere and a planar surface using analytical solutions.

<b>Second Law Equilibrium Test</b>: An enclosed box with uniform temperature is used to verify that the radiation model satisfies the second law of thermodynamics. All surfaces in thermal equilibrium should emit exactly their black-body radiation times their emissivity, regardless of the complexity of multiple reflections within the enclosure.

<b>Anisotropic Diffuse Radiation</b>: Tests verify that horizontal patches receive the correct amount of diffuse radiation when anisotropic extinction coefficients are applied, ensuring proper implementation of directionally-dependent radiation attenuation.

All toy problem tests achieve Monte Carlo convergence with relative errors below 0.5% when averaged over 500 ensemble runs, demonstrating the accuracy of the fundamental radiation transport implementation.

\subsection RadiationModelVerificationCanopy Canopy Verification Tests

For simplified canopy architectures, theoretical solutions exist for

1 - <b>Canopy Light Interception</b>: The homogeneous canopy patch test validates light interception calculations against Beer's law analytical solutions. A synthetic canopy is constructed with randomly positioned and oriented square leaf patches distributed throughout a 3D domain. The test compares both direct and diffuse radiation interception between model predictions and theoretical expectations.

   For direct radiation at solar zenith angle \f$\theta_s\f$, the theoretical canopy light interception follows:
   \f[I_{direct} = 1 - \exp\left(-\frac{0.5 \times LAI}{\cos(\theta_s)}\right)\f]

   For diffuse radiation, the theoretical interception integrates over all sky directions:
   \f[I_{diffuse} = \int_0^{\pi/2} 2\left(1 - \exp\left(-\frac{0.5 \times LAI}{\cos(\theta)}\right)\right) \cos(\theta) \sin(\theta) d\theta\f]

   The test creates a canopy with leaf area index (LAI) = 2.0, distributed over a 50m x 50m domain with 3m height. Ground-based radiation measurements and leaf-intercepted radiation are calculated within a central 40m x 40m area to minimize edge effects. Both direct (solar zenith angle = 36 degrees) and diffuse radiation scenarios are tested.

   Model results demonstrate excellent agreement with theoretical predictions, with relative errors below 1% for both direct and diffuse radiation interception. This validates the accuracy of the Monte Carlo ray tracing implementation for randomly oriented surfaces in complex 3D canopy geometries (plugins/radiation/tests/selfTest.cpp:731).

2 - <b>Canopy Sunlit/Shaded Leaf Area Fraction</b>

   Analytical expressions are available for calculating the fraction of sunlit and shaded leaf area, both in homogeneous canopies and in heterogeneous canopies. The equations for which are given in <a href="https://doi.org/10.1016/j.agrformet.2025.110680">Bailey (2025)</a>.

   The <a href="https://baileylab.ucdavis.edu/software/helios/doc/html/radiation__BeersLaw_8cpp-example.html">Beer's Law Tutorial</a> in the native Helios documentation provides a detailed walkthrough of the sunlit-shaded leaf area calculation for a homogeneous canopy, which yields an agreement between Helios and the analytical solution with relative errors around 1%.

   The figure below from <a href="https://doi.org/10.1016/j.agrformet.2025.110680">Bailey (2025)</a> shows the result for 3 different crown types. It should be noted that the theoretical solution has some error, particularly for the conical crown shape since it results in very short radiative path lengths that violate the assumptions of a turbid medium.

   \image html fsun_Bailey_2025.jpg width=600
   <b>Figure.</b> Comparison of theoretical model for \f$f_{sun}\f$ and the value computed by the 3D model for four different single, isolated crown shapes: (a) spherical crown, (b) ellipsoidal crown, and (c) conical crown. Three different leaf angle distributions were simulated (spherical \f$\circ\f$, planophile \f$\triangle\f$, and erectophile \f$\square\f$). The dotted diagonal line corresponds to perfect 1:1 agreement.

3 - <b>Canopy Absorbed Flux Probability Distributions</b>

   Analytical expressions for the probability distribution of absorbed direct, diffuse, and scattered radiation fluxes within a horizontally homogeneous canopy are given in <a href="https://doi.org/10.1016/j.agrformet.2022.109034">Bailey and Fu (2022)</a>. This is a particularly strong verification test of the radiation model because it shows that it not only produces correct integrated fluxes, but also correctly predicts the probability distribution of fluxes across the canopy.

   \image html directPDF_BaileyFu_2022.jpg width=600
   <b>Figure.</b> Probability density function of absorbed direct radiation flux within a horizontally homogeneous canopy of \f$LAI = 1\f$. The absorbed direct radiation flux, \f$R_{L,dir}\f$, is normalized by the incoming direct radiation flux on a surface perpendicular to the sun direction, \f$R_{0,dir}\f$. Azimuthally isotropic leaf angle distributions of spherical, uniform, planophile, and erectophile are shown in each pane as indicated by the title. Each line corresponds to a different solar zenith angle. Open symbols correspond to the distribution obtained from 3D simulation.

   \image html diffusePDF_BaileyFu_2022.jpg width=600
   <b>Figure.</b> Probability density function of absorbed diffuse radiation flux within a horizontally homogeneous canopy of \f$LAI = 1\f$. The absorbed diffuse radiation flux, \f$R_{L,diff}\f$, is normalized by the incoming diffuse radiation flux on a surface perpendicular to the sun direction, \f$R_{0,diff}\f$. Azimuthally isotropic leaf angle distributions of spherical, uniform, planophile, and erectophile are shown in each pane as indicated by the title. Each line corresponds to a different angular distribution of incoming diffuse radiation. Open symbols correspond to the distribution obtained from 3D simulation. In all cases shown, the solar zenith angle was 0 (vertical).

   \image html scatterPDF_BaileyFu_2022.jpg width=600
   <b>Figure.</b> Probability density function of absorbed scattered radiation flux within a horizontally homogeneous canopy of \f$LAI = 1\f$. Azimuthally isotropic leaf angle distributions of spherical, uniform, planophile, and erectophile are shown in each pane as indicated by the title. Each line corresponds to a different solar zenith angle. Open symbols correspond to the distribution obtained from 3D simulation. In all cases, the diffuse radiation fraction was \f$f_{diff}\f$.

4 - <b>ROMC Radiation Camera Tests</b>

   The radiation camera model has been verified against several tests from the <a href="https://romc.jrc.ec.europa.eu">ROMC benchmark suite</a>. These tests involve comparing synthetic images generated by the radiation camera model against reference images for a variety of geometric and radiometric scenarios. Select results are given below, with more detailed description and analysis given in <a href="https://doi.org/10.34133/plantphenomics.0189">Lei et al. (2024)</a>.

   | ROMC Test    | SKILL Score |
   |--------------|-------------|
   | brfpp_uc_sgl | 98.00       |
   | brfpp_co_sgl | 92.65       |
   | brfop        | 97.52       |
   | fabs         | 99.98       |

   \image html ROMC_HET51_DIS_UNI_NIR_00.jpg width=700
   <b>Figure.</b> The bi-directional reflectance factor (BRF) curve of experiment HET51_DIS_UNI_NIR_00 measured in the ROMC case brfop and corresponding synthetic images captured by simulated cameras at multiple viewing zenith angles (red numbers below images).

   \image html ROMC_Wellington.jpeg width=450
   <b>Figure.</b> The BRF (brfpp) curves of the actual scene "Wellington Citrus Orchard" obtained by RAMI IV benchmark models and the present ray-tracing model (Helios-RT).

\subsection RadiationModelValidation Field Validation

1 - <b>Vineyard Canopy Light Interception</b>

   <a href="">Ponce de Leon et al. (2025)</a> conducted a field validation of the Helios radiation model in five different vineyard designs. Measurements consisted of differential measurements of all-wave solar radiation flux above and below the canopy. Results are summarized in the figure below.

   \image html vineyard_radiation_validation.jpg width=800
   <b>Figure.</b> Measured and simulated radiation flux reaching the inter-row in the PAR and NIR band (\f$R_{inter-row}\f$) in five different vineyard designs. This includes split grape canopy cases with rows orientated NE-SW (Site 1) and NW-SE (Site 2) at Barrelli Creek, Cloverdale CA; a double vertical grape canopy case with rows oriented E-W (Site 3) and a split canopy case with rows oriented E-W (Site 4) at Madera, CA; and a split grape canopy with rows oriented E-W in Lodi, CA (Site 5). Measurements and simulations were conducted every 1 min (Sites 1, 2, and 4) and every 15 min (Sites 3 and 5). The dashed magenta line is the measurement, and the solid black like is the Helios simulation. \f$Q_0\f$ indicates the incoming radiation flux.

2 - <b>Orchard Canopy Light Interception</b>

   Ponce de Leon et al. (under review) conducted a field validation of the Helios radiation model in an almond and olive orchard canopy. Measurements consisted of differential measurements of all-wave solar radiation flux above and below the canopy. Results are summarized in the figure below.

   \image html orchard_radiation_validation.png width=600
   <b>Figure.</b> Measured and simulated 15-minute radiation flux reaching the inter-row in the PAR and NIR band (\f$R_{inter-row}\f$, W m<sup>-2</sup>) in an (a) almond orchard with rows orientated: NE-SW at Solano, CA on July 18, 2023 and in an (b) olive orchard with rows oriented N-S at Glenn, CA on July 18, 2024.

3 - <b>Soybean Net Radiation Measurements</b>

   <a href="https://doi.org/10.1016/j.agrformet.2025.110941">Wang et al. (2026)</a> measured and validated net radiation based on measurements above a soybean canopy across a season. The model prediction agreed well with the measurements, with an overall R<sup>2</sup> of 0.94.

   \image html soybean_radiation_validation.png width=450
   <b>Figure.</b> Validation of Helios net radiation against measurements of net radiation from an eddy covariance tower above a soybean canopy.

\section EnergyBalanceTemperature Energy Balance Surface Temperature Model Validation

\subsection EnergyBalanceTemperatureVerification Verification Tests

An important verification test of the energy balance model, aside from verifying energy balance closure, is to verify that the model satisfies the second law of thermodynamics. This is tested by setting the absorbed radiation flux of all elements in a simulated canopy scene to zero, and setting the longwave flux from the sky equal to \f$\sigma T^4\f$, where \f$T\f$ is an arbitrary temperature in Kelvin. After running the energy balance, all elements in the scene should have the same computed temperature of \f$T\f$. This test is implemented in `plugins/energybalance/tests/selfTest.cpp`, and is explored in more detail in <a href="http://dx.doi.org/doi:10.1016/j.ecolmodel.2017.11.022">Bailey (2018)</a>.

\subsection EnergyBalanceTemperatureValidation Field Validation

1 - <b>Grape Berry Temperature Measurements</b>

<a href="https://doi.org/10.1016/j.agrformet.2021.108431">Ponce de Leon and Bailey (2021)</a>

\image html berry_temperature_validation.jpg width=700
<b>Figure.</b> Daily course of simulated and average measured grape berry temperature in the east and west side of the vine for trellis systems (a) VSP, (b) Wye, (c) Goblet and (d) Unilateral.

2 - <b>Cowpea Leaf Temperature Measurements</b>

<a href="https://doi.org/10.34133/plantphenomics.0169">Mayanja et al. (2024)</a>

\image html cowpea_leaf_temperature_validation.png width=400
<b>Figure.</b> Measured and simulated cowpea leaf temperature (T<sub>leaf</sub>, degrees C) for four different cowpea genotypes.

3 - <b>Redbud Tree Leaf Temperature Measurements</b>

\image html redbud_leaf_temperature_validation.png width=600
<b>Figure.</b> Comparison between simulated leaf temperature and an ensemble of measurements using a LICOR LI-600 porometer across a day.

\section ETValidation Canopy Evapotranspiration Validation

1 - <b>Almond Lysimeter Measurements</b>

Whole-plant ET was validated in Helios by comparing against measurements of an almond tree in a weighing lysimeter. One Nonpareil almond tree was planted in a large weighing lysimeter at the Kearney Agricultural Research and Extension Center (KARE). The surrounding orchard consisted of 50% Nonpareil, 25% Wood Colony, and 25% Monterrey trees. Inputs for Helios included LiDAR scans for reconstruction, ambient weather data, and leaf-level gas exchange measurements.

The figure below shows validation results across two seasons, which indicate good model agreement. There are brief periods in which the experimental ET drops dramatically when irrigation is withheld during hull split, which was not explicitly represented in the simulations.

\image html lysimeter_ET_validation.png width=600
<b>Figure.</b> Validation of Helios whole-tree almond ET based on weighing lysimeter data.

\section PhotosynthesisValidation Canopy Photosynthesis Validation

1 - <b>Soybean Eddy Covariance Measurements</b>

<a href="https://doi.org/10.1016/j.agrformet.2025.110941">Wang et al. (2026)</a> validated Helios predictions of gross primary production (GPP) against measurements collected from an eddy covariance tower above a soybean field across a season.

\image html soybean_photosynthesis_validation_timeseries.png width=450
<b>Figure.</b> Validation of Helios against measurements of GPP collected from an eddy covariance tower above a soybean field across time. Different simulation lines correspond to a different scheme for representing spatial heterogeneity in photosynthesis parameters (see <a href="https://doi.org/10.1016/j.agrformet.2025.110941">Wang et al. (2026)</a> for details).

\image html soybean_photosynthesis_validation_scatter.png width=700
<b>Figure.</b> Validation of Helios against measurements of GPP collected from an eddy covariance tower above a soybean field. Each subplot corresponds to a different scheme for representing spatial heterogeneity in photosynthesis parameters (see <a href="https://doi.org/10.1016/j.agrformet.2025.110941">Wang et al. (2026)</a> for details). (a-e): performance for data from DOY 178 to DOY 195; (f-j): performance for data from DOY 240 to DOY 255.

\section LiDARValidation LiDAR Canopy Measurement Validation

\subsection LiDARVerification LiDAR Verification Tests

The Helios LiDAR plug-in has many verification checks that are run each time a new version of Helios is released. These tests use synthetic LiDAR data to generate test data, where the exact scanned geometries are known, enabling accurate error calculations.

The leaf angle distribution calculations are verified by generating canopies of known leaf angle distribution, generating synthetic scan data based on them, then applying the leaf angle algorithm to the simulated data. A similar process is used to verify the leaf area inversion calculations.

<a href="https://doi.org/10.1016/j.rse.2024.114229">Kent and Bailey (2024)</a> conducted a detailed study of errors in Helios' LiDAR-based leaf area inversion using synthetic data, and estimated expected errors across a range of scenarios. Similarly, <a href="https://ieeexplore.ieee.org/document/9591661">Halubok et al. (2022)</a> used synthetic data to quantify errors in Helios' aerial LiDAR inversion of leaf area density.

\subsection LiDARField LiDAR Field Validation

1 - <b>Leaf Angle Distribution Measurements</b>

<a href="http://dx.doi.org/doi:10.1016/j.rse.2017.03.011">Bailey and Mahaffee (2017a)</a> compared Helios-derived leaf angle distribution measurements from LiDAR data against manual measurements across a tree crown. Error in the LiDAR-based measurements was likely comparable to that of the manual measurements, as illustrated as part of the study. The paper highlights the importance of properly weighting LiDAR-derived leaf angles based on their projection in the direction of the scanner.

2 - <b>Leaf Angle Distribution Method Intercomparison Study</b>

<a href="https://doi.org/10.1111/nph.70379">Mutugi Murithi et al. (2025)</a> performed an intercomparison study to evaluate different methods for estimating the leaf angle distribution from LiDAR data. The study concluded that the best performing algorithm was that used by Helios, which outperformed much newer algorithms both in terms of accuracy and in computational speed. The main failure of other methods is that they do not properly weight leaf angles based on their projection in the direction of the scanner, as recommended by <a href="http://dx.doi.org/doi:10.1016/j.rse.2017.03.011">Bailey and Mahaffee (2017a)</a>.

3 - <b>Leaf Area Measurements</b>

<a href="http://dx.doi.org/doi:10.1088/1361-6501/aa5cfd">Bailey and Mahaffee (2017b)</a> compared Helios-derived leaf area density measurements from LiDAR data against manually measured leaf area density in a tree. The index of agreement between LiDAR-derived and manually measured leaf area density was \f$d=0.98\f$.
