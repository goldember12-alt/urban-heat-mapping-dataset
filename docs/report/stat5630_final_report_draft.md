\begin{titlepage}
\centering
\vspace*{0.75in}

{\Large STAT 5630 Statistical Machine Learning\par}
\vspace{0.65in}

{\huge\bfseries Cross-City Urban Heat Hotspot Screening:\par}
\vspace{0.12in}
{\huge\bfseries A 30 m Dataset and City-Held-Out Transfer Benchmark\par}
\vspace{0.75in}

{\Large Final Report\par}
\vspace{0.5in}

{\large Collaborators\par}
\vspace{0.12in}
{\Large Max Clements and Nicholas Machado\par}

\vfill

{\large April 26, 2026\par}
\end{titlepage}

\newpage

## Main Text

### 1. Background Information

Extreme urban heat is a public-health, infrastructure, and planning problem because thermal exposure is not distributed evenly across a city. At fine spatial scales, differences in pavement, roof surfaces, vegetation, water proximity, terrain, building density, and local land cover can produce large contrasts in surface heat across neighborhoods that are close together. A citywide average therefore hides the places where heat-mitigation investments, additional monitoring, or planning attention may be most useful. For a statistical learning project, the practical question is not only whether a city contains hot areas, but whether publicly available spatial variables can help rank local cells for screening when direct thermal labels are limited.

Remote sensing is central to this problem because satellites can observe spatial patterns that are difficult to measure with ground stations alone. Thermal infrared sensors measure emitted radiation from the land surface and can be converted into land surface temperature, or LST. LST is not the same as the two-meter air temperature reported in a weather forecast: it describes how warm the observed surface would feel to the touch, so a roof, road, tree canopy, irrigated field, or bare soil patch may all behave differently. NASA's land-surface-temperature documentation emphasizes that land heats and cools differently from the air, and ECOSTRESS documentation describes a thermal mission that measures surface temperature at fine spatial detail from the International Space Station. That distinction is important for this report. The target is based on surface temperature, so the results should be interpreted as surface hotspot screening rather than direct human heat-exposure measurement.

Urban thermal remote sensing has a long history, but the literature also shows why this project needs a careful validation design. Voogt and Oke (2003) review thermal remote sensing of urban climates and note that many urban thermal studies historically emphasized qualitative maps of thermal patterns and simple correlations with surface descriptors. Later Landsat-based work gave more quantitative evidence for specific predictors. Weng, Lu, and Schubring (2004) studied the relationship between land surface temperature and vegetation abundance in Indianapolis and treated NDVI as a standard indicator of vegetation abundance in urban heat-island analysis. Yuan and Bauer (2007) compared NDVI and impervious surface as indicators of surface urban heat-island effects in the Twin Cities and found that percent impervious surface had a strong relationship with LST across seasons, while NDVI remained useful but more seasonally variable. Together, this work motivates the feature set used here: vegetation, imperviousness, land cover, terrain, and water proximity are not arbitrary columns, but physically plausible surface descriptors.

Vegetation matters because evapotranspiration and shading can lower surface temperatures, while low vegetation often leaves more exposed built or bare surfaces. Impervious surfaces matter because roads, roofs, sidewalks, and parking areas store and reradiate heat and reduce evaporative cooling. Land-cover class provides a compact description of surface type, distinguishing developed, forested, grass, wetland, and other covers. Water proximity matters because water bodies and riparian corridors can be associated with local cooling or with land-cover transitions. Terrain is also relevant: elevation, slope context, and valley or coastal settings can influence radiation, drainage, and local thermal patterns. This report uses elevation directly and keeps distance-to-water as a simple hydrologic-context variable, while avoiding a larger feature expansion in the headline model so the first benchmark stays interpretable.

The data-access workflow also follows established remote-sensing practice. AppEEARS, the Application for Extracting and Exploring Analysis Ready Samples, is a NASA Earthdata/LP DAAC tool for spatial, temporal, and layer subsetting of remote-sensing products. In this project it supports reproducible area requests for MODIS/Terra NDVI and ECOSTRESS LST over city study regions. ECOSTRESS provides atmospherically corrected LST and emissivity products, while AppEEARS helps reduce those products to the city polygons and seasonal windows used for analysis. This matters for reproducibility because the report does not rely on manually downloaded images; it uses consistent acquisition and preprocessing rules tied to the same city definitions used for modeling.

The main research gap is transfer. Many urban LST studies are single-city studies, descriptive mapping exercises, or correlation analyses. Even when prediction models are used, ordinary random row or cell splits can be too easy for spatial data because nearby cells and cells from the same city can appear in both training and testing. Roberts et al. (2017) argue that ignoring spatial, temporal, or hierarchical structure in cross-validation can underestimate predictive error, and Meyer et al. (2018) show that target-oriented validation can reveal much weaker performance than random folds when models must predict beyond familiar locations. This project applies the same principle at the city scale: the relevant test is not whether the model can interpolate among nearby cells in one city, but whether it can prioritize cells likely to fall in the within-city top decile in cities whose labels were completely unseen during training.

The final project therefore builds a standardized multi-city dataset and evaluates a city-held-out ranking task. The completed dataset contains 71,394,894 rows and 17 columns, with one row representing one analytic 30 m grid cell in one of 30 selected U.S. cities. The cities are balanced across three broad climate groups: 10 hot-arid, 10 hot-humid, and 10 mild-cool cities. This design keeps the report centered on cross-city transfer instead of a Phoenix-only feasibility example or a conventional same-city prediction task. Figure 1 shows the selected city locations, and Table 2 summarizes the final audited dataset by climate group.

The dataset combines public geospatial and remote-sensing sources that describe both the urban surface and the thermal outcome. 2020 Census urban-area geometry defines each study region. Annual NLCD 2021 land-cover and impervious-surface products provide categorical land cover and built-intensity measures. USGS 3DEP elevation supplies terrain information, while NHDPlus HR hydrography supports a distance-to-water feature. MODIS/Terra MOD13A1.061 NDVI, acquired through AppEEARS for May 1-August 31, 2023, summarizes warm-season vegetation. ECOSTRESS ECO_L2T_LSTE.002 land surface temperature, also acquired through AppEEARS for the same May-August 2023 window, provides the thermal measurement used to define the hotspot label. Table 1 lists these source layers and the final variables constructed from them.

The modeling setup deliberately excludes the thermal variables from the predictive feature set. ECOSTRESS LST is used to define the outcome, not to predict it. The first-pass headline models use non-thermal, transferable predictors: impervious percentage, land-cover class, elevation, distance to water, median May-August NDVI, and broad climate group. This feature contract makes the prediction task harder, but it avoids leaking the answer and keeps the model closer to a screening workflow that could be applied before collecting city-specific hotspot labels.

### 2. Research Questions

The primary research question is:

Can a model trained on a multi-city urban heat dataset rank 30 m grid cells by their likelihood of being among the locally hottest cells in cities that were entirely excluded from training?

This question is evaluated as a transfer problem. The unit of analysis is a 30 m grid cell, but the unit of evaluation is the city: a held-out city must remain fully unseen while model preprocessing, imputation, scaling, encoding, and tuning are learned from other cities. The target population for inference is 30 m grid cells inside buffered Census urban-area study regions for the selected U.S. cities, with cautious extension to similar urban areas.

The project also asks three secondary questions. First, do non-thermal geospatial predictors contain enough transferable signal to screen for the locally hottest urban grid cells? Second, does a nonlinear random forest improve cross-city ranking or retrieval compared with logistic regression and simple baselines? Third, does model performance vary systematically by city or climate group?

The outcome is `hotspot_10pct`, a city-relative binary label. A positive cell is one of the hottest 10% of valid eligible cells within its own city, based on median May-August ECOSTRESS LST after final filtering. This is not an absolute national heat threshold. A positive cell in Boston and a positive cell in Phoenix both represent the upper tail of their local city distributions, even though their absolute temperatures may differ. That choice makes the target appropriate for relative within-city screening across a cross-climate city set, where a practical planning question is often which local cells should be prioritized for closer inspection.

### 3. Dataset Construction

The dataset construction workflow starts with city selection and study-region definition. The project uses 30 U.S. cities, balanced across three broad climate groups: hot-arid, hot-humid, and mild-cool. The city list should be interpreted as a purposive benchmark set rather than a probability sample of all U.S. cities. Ten cities were assigned to each group to create a transfer test spanning dry western metros, humid southern and eastern metros, and cooler or milder metros. The climate groups are intentionally coarse design labels. They are not meant to replace formal climatology or local meteorology, but they make the transfer question more interpretable by asking whether a model trained across one mixture of cities behaves differently across broad regional climate contexts. This balance also prevents the benchmark from becoming only a large-city or only a hot-desert exercise.

For each selected city, the study region begins with the 2020 Census urban area containing the city center. That urban-area polygon is used as the core geometry, and the analysis also preserves it separately from the buffered study area. The default study area then applies a 2 km buffer around the core urban area. The buffer matters because heat patterns, water adjacency, and built/natural land-cover transitions do not stop exactly at administrative or Census boundaries. It is a fixed design choice rather than an optimized parameter, so it can include some fringe land differently across cities. Preserving the unbuffered core geometry keeps the original urban-area definition available for comparing core-city and buffered-area filters.

Each city receives a master 30 m grid built in a local UTM coordinate reference system. This is a practical geospatial choice. A local projected CRS makes distances and cell areas meaningful within a city, which is necessary for 30 m cell construction and for the distance-to-water feature. The grid is the analytic backbone of the project: every final row is one grid cell, and every raster or vector source is converted into a value for that same cell. Without a master grid, differences in source resolution, projection, and pixel alignment could create hidden inconsistencies across variables.

The phrase "30 m dataset" therefore refers to the analytic grid and row unit, not to the native resolution of every source variable. NLCD is naturally close to the grid scale, but MODIS/Terra NDVI is coarser, ECOSTRESS has its own thermal-pixel and overpass structure, and vector-derived quantities such as distance to water are summarized to cell centroids or cell geometry. The resulting table is valuable because it gives every city a common modeling unit, but it should not be interpreted as 71.4 million independent 30 m native-resolution measurements of every phenomenon.

The source layers are then prepared against this grid. NLCD 2021 land cover supplies a categorical surface class for each cell, and NLCD 2021 imperviousness supplies a continuous percent-impervious value. USGS 3DEP elevation is aligned to the grid to provide terrain context. NHDPlus HR hydrography is handled as vector information: water features are clipped to the city study area and converted to a distance from each grid cell to the nearest selected hydro feature. MODIS/Terra NDVI and ECOSTRESS LST are acquired through AppEEARS using the city area of interest and summarized for May-August 2023. The project uses median May-August NDVI as the vegetation predictor and median May-August ECOSTRESS LST as the thermal outcome ingredient.

The May-August seasonal summary is a compromise between heat relevance and data robustness. It focuses the target and vegetation feature on the warm season, when surface heat is most relevant to the urban heat problem, while aggregating over multiple observations rather than depending on one satellite pass. ECOSTRESS also has irregular overpass timing because it is mounted on the International Space Station, so the analysis records `n_valid_ecostress_passes` as a quality-support field. Cells with fewer than three valid ECOSTRESS observations are removed when LST is available. This filter reduces the chance that a cell is labeled from an unstable or nearly missing thermal summary, but pass count alone does not make all cities observationally identical. Overpass time, clouds, seasonality within May-August, and weather conditions can still vary across cities and remain part of the remote-sensing limitation.

The final assembly step merges the per-city feature tables into a single modeling-ready dataset, with CSV also written as a compatibility output. Open-water cells are dropped where `land_cover_class == 11`, because open water is a different thermal surface and would complicate the urban land-cell screening target. After the water and ECOSTRESS pass-count filters, the hotspot label is recomputed within each city. This recomputation is essential: the positive class should represent the hottest 10% of the eligible modeling population in that city, not the top decile of a larger pre-filtered set that included cells no longer eligible for modeling.

The target, `hotspot_10pct`, is therefore city-specific. A cell is positive if its median May-August LST falls in the top 10% among valid eligible cells in its own city. This design supports cross-climate comparison because it asks about local hotspot screening rather than one absolute national LST threshold. A Phoenix hotspot and a Boston hotspot may have different absolute surface temperatures, but both represent locally high surface temperature within their urban context. The top-decile target is useful for screening because it turns each city into a ranked local prioritization problem. The tradeoff is that the target should not be interpreted as an absolute human heat-risk standard or as a direct planning action without local validation.

The final dataset contains the city identifier and name, broad climate group, cell identifier, cell centroid longitude and latitude, six headline predictors, ECOSTRESS-derived LST and pass count, the `hotspot_10pct` label, and three neighborhood-context variables constructed for later model extensions. The main benchmark keeps the six-feature specification fixed and does not use those neighborhood variables in the logistic-versus-random-forest comparison. This separation is important because it lets richer-feature experiments be reported as extensions rather than silent changes to the main benchmark.

The completed audit confirms 30 cities, 71,394,894 rows, and 7,139,588 hotspot-positive cells. Because `hotspot_10pct` is recomputed within city, overall prevalence is approximately 10% by construction, and each climate group has nearly the same hotspot prevalence despite large differences in total row count. The feature-missingness summary is favorable for the headline predictors: imperviousness, land cover, distance to water, and climate group have no missing values in the final table; elevation is missing for only 3,426 cells, and median May-August NDVI is missing for 99,625 cells, about 0.14% of the dataset. The row-count distribution is uneven across cities because study-area extents differ substantially; Appendix Figure A1 is included as support for that point.

The large row count should not be read as 71.4 million independent observations. Nearby 30 m cells share land cover, repeated coarser-source summaries, sensor conditions, spatial context, and thermal structure, so the effective independent information is much smaller than the raw row count. The city-held-out design addresses one major source of leakage across cities, but it does not erase within-city spatial dependence. This is a construct-validity limitation, not a reason to discard the dataset: the common grid is what makes consistent cross-city modeling possible, while spatial dependence limits how strongly the raw row count should be interpreted.

Figure 2 summarizes the end-to-end dataset construction workflow. The key modeling implication is that the final table is not an ad hoc spreadsheet: it starts from public data sources, aligns every layer to a 30 m city grid, applies explicit row filters, and creates a target suitable for testing generalization to unseen cities.

### 4. Model and Method

Given that construction, the statistical learning task is to estimate, for each grid cell in an unseen city, the probability that the cell belongs to the hottest 10% of valid eligible cells in its own city. The response variable is `hotspot_10pct`, and the headline models use only the six non-thermal predictors in the main benchmark: `impervious_pct`, `land_cover_class`, `elevation_m`, `dist_to_water_m`, `ndvi_median_may_aug`, and `climate_group`.

Several columns are intentionally excluded from the predictive feature set. The target itself, `hotspot_10pct`, cannot be used as an input. The thermal variables `lst_median_may_aug` and `n_valid_ecostress_passes` are also excluded because LST defines the label and ECOSTRESS pass count is a data-quality support variable rather than a stable urban-form predictor. Cell identifiers, city identifiers, city names, and centroid coordinates are excluded because they could let a model memorize location-specific patterns instead of learning a portable relationship between urban surface characteristics and hotspot status.

The central evaluation design is grouped cross-validation by city, shown schematically in Figure 3. The 30 cities are partitioned into five deterministic outer folds, with six complete cities held out in each fold and the remaining 24 cities used for training. Every city is held out exactly once. This design is stricter than a random cell-level split because all rows from a test city are unseen during model fitting. For each outer fold, all preprocessing, imputation, scaling, categorical encoding, feature construction inside the model pipeline, and hyperparameter tuning are fit using training-city rows only. The held-out cities are touched only after the full training pipeline has been selected and fit.

This train-city-only rule is the core leakage control in the report. Numeric imputation values, scaling parameters, categorical encodings, and tuned hyperparameters are all learned without looking at the held-out cities. The rule also applies to model selection: inner cross-validation for tuning is performed only inside the training-city portion of each outer fold. As a result, a held-out city's labels cannot influence preprocessing choices, feature encodings, or tuning decisions. The final held-out prediction table is therefore a genuine transfer test at the city level, not a same-city interpolation exercise.

Within-city held-out validation would answer a related but easier question: how well models interpolate to unseen cells from a city that is already represented in training. Those results would be useful diagnostic context for how much performance improves when train and test data share the same city, but they would not replace the unseen-city transfer benchmark reported here.

The report compares simple transfer baselines, logistic regression, and random forest. The simple baselines provide sanity checks for whether a learned model improves beyond very limited rules. The baseline set includes a no-skill prevalence reference, a global-mean baseline, a land-cover-only baseline, an impervious-only baseline, and a climate-only baseline. These baselines are useful because they show how much performance can be obtained from single-feature or prevalence-style transfer rules before fitting a richer model.

The logistic regression model is the main linear benchmark. Missing-value imputation, numeric scaling, one-hot encoding of categorical features, and the classifier are fit together inside each training fold. The classifier uses the `saga` solver, which supports regularized logistic regression over the six-feature set. In course terms, logistic regression models the log-odds of hotspot status as an additive function of the predictors. It is useful here because it is relatively interpretable and because a strong linear model is a fair reference point for asking whether nonlinear structure adds value.

The random forest model is the main nonlinear benchmark. It uses the same training-only preprocessing rule. Numeric predictors are imputed, categorical predictors are encoded inside the training fold, and the forest is tuned over tree count, tree depth, feature subsampling, and minimum leaf size. A random forest averages predictions from many decision trees, allowing threshold effects and interactions among variables such as land cover, vegetation, imperviousness, and climate group. The model is therefore a natural test of whether nonlinear relationships improve city-held-out screening under the same six-feature contract.

The primary metric is precision-recall area under the curve, or PR AUC. PR AUC summarizes how well a model ranks true hotspots above non-hotspots across possible score thresholds. It is more informative than raw accuracy in this project because the positive class is intentionally about 10% of cells. A trivial model that predicts "not hotspot" for every cell would be highly accurate but useless for finding hotspots. PR AUC focuses instead on the tradeoff between precision, the share of predicted positives that are true positives, and recall, the share of true positives recovered.

The report also uses mean city PR AUC and recall at the top 10% predicted risk. Pooled PR AUC weights cities roughly by their sampled held-out row counts, so larger cities can influence the aggregate more strongly. Mean city PR AUC first computes PR AUC for each held-out city and then averages across cities, giving each city equal interpretive weight. Recall at top 10% predicted risk is a screening-oriented metric: it asks what fraction of true hotspots would be recovered if a city inspected only the cells the model ranked in the highest-risk decile. Because the target itself is also a top-decile label, this metric is easy to interpret as top-decile retrieval.

Sampling and benchmark scope are important for interpreting the numbers. The benchmark results are sampled all-fold runs, not exhaustive model fitting and scoring over all 71,394,894 rows. The main comparison uses 5,000 rows sampled per city with target-rate stratification: 500 positives and 4,500 negatives per city, using random state 42. The same sampled city preload is used for training rows and held-out scoring rows, so each outer fold trains on 120,000 sampled rows from 24 cities and tests on 30,000 sampled rows from six held-out cities. The matched 5k comparison is the headline logistic-versus-random-forest comparison because both models share the same sample cap and fold design. A 20,000 rows-per-city logistic run is included only as higher-sample linear context. This sampling choice is a computational caveat, not a change in the grouped evaluation design: cities are still held out as complete units, and training-only preprocessing and tuning are still required.

The sampled design is also an inferential choice. It gives each city the same benchmark row count, which keeps train and test sizes comparable across held-out cities instead of letting the largest study areas dominate every model comparison. Target-rate stratification preserves the 10% hotspot prevalence in each sampled city, so PR AUC and top-decile recall are evaluated under the same class balance used to define the target. What it does not preserve exactly is full spatial density, all within-city clustering, or the exact full-population distribution of land cover, imperviousness, vegetation, and terrain. The retained benchmark should therefore be read as a sampled transfer-screening comparison, not exhaustive full-city scoring. Repeated samples or full-city scoring would be needed to quantify sampling variability.

### 5. Analysis, Conclusion and Discussion

The city-held-out benchmark supports a cautious answer to the research question. The retained predictors show limited but real transferable ranking signal, strongest in hot-arid cities; the current model is not a robust all-city classifier for local heat extremes. As shown in Table 3 and Figure 4, the random-forest 5k model reaches pooled PR AUC 0.1486, above the 0.1000 prevalence reference and above the 0.1353 land-cover-only baseline. The logistic SAGA 5k model reaches 0.1421. These values are not large in absolute terms, which is expected for a difficult transfer task with a 10% positive class, but they are consistently above a no-skill ranking reference on pooled PR AUC.

The prevalence context is important. Because the hotspot label is defined as the top 10% of eligible cells within each city, a weak ranking model has little room to look impressive by accuracy alone. PR AUC is therefore a more relevant summary than overall correct classification. A PR AUC modestly above 0.10 indicates that the model is ranking true hotspots above non-hotspots better than a prevalence-level reference, but it does not imply reliable cell-by-cell classification. The benchmark should be read as evidence for partial transferable ranking signal.

The gains over simple baselines are modest. On pooled PR AUC, random forest improves by about 0.0133 over the land-cover-only baseline and 0.0135 over the impervious-only baseline. On recall at the top 10% predicted risk, random forest reaches 0.1961, but the impervious-only baseline already reaches 0.1858. That is only about a one percentage point absolute gain. In practical screening terms, much of the transferable retrieval signal in this six-feature contract is already captured by simple built-intensity information.

The cleanest learned-model comparison is the matched 5,000 rows-per-city logistic-versus-random-forest result. On pooled PR AUC, random forest improves from 0.1421 to 0.1486. On recall at the top 10% predicted risk, random forest improves from 0.1647 to 0.1961. At the same time, logistic regression remains slightly stronger on mean city PR AUC, with 0.1803 for logistic compared with 0.1781 for random forest. The 20,000 rows-per-city logistic run reaches pooled PR AUC 0.1457 and recall at top 10% of 0.1709, which provides useful context but is not the headline comparison because it uses a larger sample than the 5k random-forest run.

The fold-level results in Table 5 show why point estimates should not be overread. Random forest improves PR AUC in folds 0, 3, and 4, but trails logistic regression in folds 1 and 2. Its recall gains are also fold-dependent: positive in folds 0, 3, and 4, negative in folds 1 and 2. Table 6 gives the city-level paired summary. Across 30 cities, the mean RF-minus-logistic PR AUC delta is -0.0023, the median delta is -0.0136, and logistic wins 21 city-level PR AUC comparisons while random forest wins 9. For recall at top 10%, the mean delta is +0.0106 but the median delta is -0.0150, again with logistic winning 21 cities. This is evidence of heterogeneous model behavior rather than a uniform nonlinear improvement.

City and climate-group summaries explain where the random-forest gains appear. Table 4 shows that random forest has positive mean gains in hot-arid cities: +0.0336 in PR AUC and +0.0762 in recall at top 10% relative to the matched logistic model. In contrast, hot-humid cities average -0.0123 in PR AUC and -0.0164 in recall, while mild-cool cities average -0.0281 in PR AUC and -0.0280 in recall. The win counts tell the same story. Random forest wins PR AUC in 5 of 10 hot-arid cities, but only 2 of 10 hot-humid and 2 of 10 mild-cool cities. For recall at top 10%, random forest wins 6 hot-arid cities, 2 hot-humid cities, and 1 mild-cool city.

Figure 5 shows the city-level deltas behind those climate summaries. The largest random-forest gains occur in hot-arid cities such as Las Vegas, Bakersfield, Tucson, and Fresno. Several hot-humid and mild-cool cities favor logistic regression, with large random-forest losses in places such as San Jose, Chicago, Portland, and Atlanta. This heterogeneity is one of the most important findings in the report. One interpretation is that dry urban landscapes may have sharper nonlinear contrasts among vegetation, imperviousness, land cover, and LST, while humid and mild-cool cities may contain thermal patterns that are less well captured by the current six-feature benchmark. The report does not directly test that physical mechanism, so the climate interpretation should be read as a hypothesis generated by the benchmark rather than as an established causal explanation. The safer conclusion is that the retained benchmark argues against a one-size-fits-all transfer story.

Supplemental feature-importance evidence is shown in Appendix Figure A2 and should be treated cautiously. The random-forest permutation summaries and logistic coefficients are consistent with vegetation, imperviousness, land cover, elevation, and climate group carrying predictive signal. That does not prove that changing any one feature would cause a specific LST response. The predictors are correlated with broader urban form, land management, local climate, and sensor-observation conditions. Their value in this report is predictive and diagnostic, not causal.

These results support a sharper conclusion than simple feasibility. The positive contribution is not a deployment-ready classifier; it is a transfer benchmark showing that cross-city hotspot screening is possible but fragile. Public non-thermal geospatial predictors carry some transferable ranking signal, simple imperviousness and land-cover baselines are difficult to beat, and nonlinear gains are heterogeneous rather than universal. The strongest random-forest gains are concentrated in selected hot-arid cities and in pooled top-decile retrieval. City-held-out validation therefore changes how urban heat model performance should be interpreted: it turns apparently simple hotspot prediction into a harder test of whether surface-form relationships travel to unseen cities.

Validity can be organized into six parts. Leakage and internal validity are relatively strong because cities are held out as complete groups and preprocessing, encoding, imputation, scaling, and tuning are fit only on training-city rows. Sampling validity is bounded because the benchmark uses 5,000 sampled rows per city rather than exhaustive all-row training and scoring over the full 71.4 million-row dataset; the sample preserves target prevalence and city balance, but not every spatial or feature-distribution detail. Spatial validity is improved by city holdout, but nearby cells within each held-out city still share land cover, sensor conditions, and thermal structure, so spatial dependence and clustered errors remain. Construct validity is limited because LST hotspots are surface-temperature hotspots, not direct air temperature, thermal comfort, or human exposure, and because not every source layer has native 30 m resolution. External validity is limited because the 30 selected cities are a useful benchmark set, not a complete representation of all U.S. urban forms, climates, coastal settings, and topographies. Model-comparison validity is also bounded: random-forest gains are modest and heterogeneous, and the report gives descriptive variability evidence rather than formal confidence intervals.

Future work should treat this as a screening benchmark rather than an operational heat-risk product. The most important next steps are to score larger held-out samples or full held-out cities, add uncertainty summaries over cities, test whether neighborhood-context predictors improve transfer without overfitting city-specific structure, and compare the LST-based target with air-temperature, exposure, or vulnerability measures where such data are available.

## References

Meyer, H., Reudenbach, C., Hengl, T., Katurji, M., & Nauss, T. (2018). Improving performance of spatio-temporal machine learning models using forward feature selection and target-oriented validation. *Environmental Modelling & Software, 101*, 1-9. https://doi.org/10.1016/j.envsoft.2017.12.001

NASA Earthdata. (n.d.). *AppEEARS*. https://www.earthdata.nasa.gov/data/tools/appeears

NASA Earthdata. (n.d.). *ECOSTRESS Swath Land Surface Temperature and Emissivity Instantaneous L2 Global 70 m V002*. https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l2-lste-002

NASA Science. (n.d.). *Land Surface Temperature*. https://science.nasa.gov/earth/earth-observatory/global-maps/land-surface-temperature/

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schroeder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography, 40*(8), 913-929. https://doi.org/10.1111/ecog.02881

Voogt, J. A., & Oke, T. R. (2003). Thermal remote sensing of urban climates. *Remote Sensing of Environment, 86*(3), 370-384. https://doi.org/10.1016/S0034-4257(03)00079-8

Weng, Q., Lu, D., & Schubring, J. (2004). Estimation of land surface temperature-vegetation abundance relationship for urban heat island studies. *Remote Sensing of Environment, 89*(4), 467-483. https://doi.org/10.1016/j.rse.2003.11.005

Yuan, F., & Bauer, M. E. (2007). Comparison of impervious surface area and normalized difference vegetation index as indicators of surface urban heat island effects in Landsat imagery. *Remote Sensing of Environment, 106*(3), 375-386. https://doi.org/10.1016/j.rse.2006.09.003

## Tables and Figures

Tables and figures are organized here rather than interleaved with the main text. Appendix tables provide additional city, fold, and model-specification details.

### Table 1. Data Sources and Constructed Variables

\begingroup
\small

| Source | Raw product / layer | Constructed final variable(s) | Spatial role | Used in headline model? |
| --- | --- | --- | --- | --- |
| U.S. Census urban areas | 2020 Census TIGERweb urban-area polygon containing each selected city center | Study-area and core-city geometry; 30 m city grid | Defines the city footprint, 2 km buffered study area, and grid alignment target | No |
| NLCD | Annual NLCD 2021 Collection 1 land-cover class raster | `land_cover_class` | Categorical built and natural surface-cover predictor; open-water filter where class 11 is present | Yes |
| NLCD | Annual NLCD 2021 Collection 1 impervious percentage raster | `impervious_pct` | Cell-level built-intensity predictor aligned to the 30 m grid | Yes |
| USGS 3DEP | 3DEP 1 arc-second digital elevation model | `elevation_m` | Terrain predictor aligned to the 30 m grid | Yes |
| NHDPlus HR | NHDPlus High Resolution hydrography water features | `dist_to_water_m` | Distance-to-nearest-water predictor derived from clipped vector water features | Yes |
| MODIS/Terra via AppEEARS | MOD13A1.061 500 m 16-day NDVI observations, May 1-August 31, 2023 | `ndvi_median_may_aug` | Summertime vegetation predictor summarized to each grid cell | Yes |
| ECOSTRESS via AppEEARS | ECO_L2T_LSTE.002 daytime land-surface-temperature observations, May 1-August 31, 2023 | `lst_median_may_aug`; `n_valid_ecostress_passes`; `hotspot_10pct` | Thermal outcome source, LST quality support field, and within-city top-decile target | No |

\endgroup

All constructed variables in Table 1 are ultimately summarized to the 30 m grid-cell row used for modeling. The MODIS NDVI source has coarser native resolution than the grid, and ECOSTRESS has its own thermal-pixel and overpass structure, so the cell-level vegetation and LST variables should be interpreted as aligned warm-season summaries rather than independent 30 m native-resolution observations.

### Table 2. Final Dataset Summary by Climate Group

\begingroup
\small

| Climate group | City count | Total rows | Total hotspot positives | Hotspot prevalence | Min city rows | Median city rows | Max city rows | Median valid ECOSTRESS passes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hot-arid | 10 | 12,814,143 | 1,281,427 | 0.1000 | 382,964 | 1,100,156 | 3,199,440 | 30.0 |
| Hot-humid | 10 | 27,098,157 | 2,709,866 | 0.1000 | 700,063 | 1,788,622 | 7,081,699 | 21.5 |
| Mild-cool | 10 | 31,482,594 | 3,148,295 | 0.1000 | 817,627 | 2,889,018 | 6,722,963 | 33.0 |

\endgroup

### Table 3. Main City-Held-Out Benchmark Metrics

Rows labeled 5,000 sampled use the same target-rate-stratified per-city sample and can be compared directly.

\begingroup
\small

| Model checkpoint | Rows per city | Pooled PR AUC | Mean city PR AUC | Recall at top 10% | Runtime (min) |
| --- | --- | ---: | ---: | ---: | ---: |
| No-skill / prevalence reference | 5,000 sampled | 0.1000 | 0.1000 | 0.1000 | n/a |
| Global-mean baseline | 5,000 sampled | 0.0982 | 0.0997 | 0.0971 | n/a |
| Climate-only baseline | 5,000 sampled | 0.0982 | 0.0997 | 0.0975 | n/a |
| Impervious-only baseline | 5,000 sampled | 0.1351 | 0.1519 | 0.1858 | n/a |
| Land-cover-only baseline | 5,000 sampled | 0.1353 | 0.1479 | 0.1672 | n/a |
| Logistic SAGA 5k | 5,000 sampled | 0.1421 | 0.1803 | 0.1647 | 35.6 |
| Logistic SAGA 20k context | 20,000 sampled | 0.1457 | 0.1796 | 0.1709 | 156.6 |
| Random forest 5k | 5,000 sampled | 0.1486 | 0.1781 | 0.1961 | 97.2 |

\endgroup

Notes: the impervious-only baseline is the strongest simple baseline on recall, and the land-cover-only baseline is the strongest simple baseline on pooled PR AUC. The 5k logistic model is the matched linear comparison for the 5k random forest, while the 20k logistic row is higher-sample linear context rather than the headline comparison. The global-mean and climate-only baselines are effectively constant or near-constant ranking rules, so small deviations around the 0.1000 prevalence reference reflect tie handling rather than meaningful below-reference skill.

### Table 4. RF Minus Logistic Performance by Climate Group

Positive deltas mean the random forest performed better than the matched logistic model within that climate group.

\begingroup
\small

| Climate group | City count | RF PR AUC wins | Logistic PR AUC wins | Mean PR AUC delta | RF recall wins | Logistic recall wins | Mean recall-at-top-10% delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hot-arid | 10 | 5 | 5 | +0.0336 | 6 | 4 | +0.0762 |
| Hot-humid | 10 | 2 | 8 | -0.0123 | 2 | 8 | -0.0164 |
| Mild-cool | 10 | 2 | 8 | -0.0281 | 1 | 9 | -0.0280 |

\endgroup

### Table 5. Fold-Level RF Minus Logistic Comparison

\begingroup
\small

| Outer fold | Train rows | Test rows | Test positives | Test prevalence | Logistic PR AUC | RF PR AUC | RF minus logistic PR AUC | Logistic recall@top10 | RF recall@top10 | RF minus logistic recall@top10 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 120,000 | 30,000 | 3,000 | 0.1000 | 0.1610 | 0.1773 | +0.0163 | 0.2170 | 0.2217 | +0.0047 |
| 1 | 120,000 | 30,000 | 3,000 | 0.1000 | 0.2006 | 0.1598 | -0.0408 | 0.2563 | 0.2087 | -0.0477 |
| 2 | 120,000 | 30,000 | 3,000 | 0.1000 | 0.1436 | 0.1301 | -0.0135 | 0.1777 | 0.1443 | -0.0333 |
| 3 | 120,000 | 30,000 | 3,000 | 0.1000 | 0.1267 | 0.1606 | +0.0340 | 0.1463 | 0.2133 | +0.0670 |
| 4 | 120,000 | 30,000 | 3,000 | 0.1000 | 0.1471 | 0.1493 | +0.0022 | 0.1640 | 0.2020 | +0.0380 |

\endgroup

### Table 6. City-Level Paired RF Minus Logistic Summary

\begingroup
\small

| Metric | Mean delta | Median delta | SD delta | Min delta | Max delta | RF wins | Logistic wins | Ties |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| City PR AUC | -0.0023 | -0.0136 | 0.0602 | -0.0743 | 0.1945 | 9 | 21 | 0 |
| City recall@top10 | +0.0106 | -0.0150 | 0.0901 | -0.0700 | 0.3420 | 9 | 21 | 0 |

\endgroup

### Figure 1. Study City Locations

![Study City Locations](figures/study_city_points.png){width=0.95\textwidth}

The 30 benchmark cities span western, southern, and northern U.S. regions and are colored by broad climate group. Appendix Table A4 lists full city names, climate groups, row counts, and fold assignments.

### Figure 2. Dataset Construction Workflow

![Dataset Construction Workflow](figures/workflow_overview.png){width=0.95\textwidth}

Buffered Census urban-area study regions and local 30 m grids feed aligned per-city feature assembly, including MODIS/Terra MOD13A1.061 NDVI and ECOSTRESS LST acquired through AppEEARS for May-August 2023, followed by final dataset generation, audit, city-held-out folds, and model evaluation.

### Figure 3. City-Held-Out Evaluation Design

![City-Held-Out Evaluation Design](figures/evaluation_design.png){width=0.95\textwidth}

Each outer fold holds out six complete cities and trains on the remaining 24 cities. All preprocessing and tuning are fit using training-city rows only.

### Figure 4. Benchmark Metric Comparison

![Benchmark Metric Comparison](figures/benchmark_metrics.png){width=0.95\textwidth}

Sampled city-held-out benchmark metrics compare the no-skill reference, simple baselines, matched 5k logistic and random-forest models, and the 20k logistic context run. The dashed line marks the 10% prevalence reference.

### Figure 5. City-Level RF Minus Logistic Deltas

![City-Level RF Minus Logistic Deltas](figures/city_metric_deltas.png){width=0.95\textwidth}

Horizontal bars show random-forest minus logistic deltas for each city, sorted by PR AUC delta and colored by climate group. Large random-forest gains are concentrated in Las Vegas, Bakersfield, Tucson, and Fresno, while San Jose, Chicago, Portland, and Atlanta are among the clearest logistic-favoring cities.

\newpage

## Appendix

### Appendix Table A1. Final Dataset Columns

\begingroup
\small

| Column | Definition | Role in report | Used in headline model? |
| --- | --- | --- | --- |
| `city_id` | Integer city identifier used for joins and grouped cross-validation. | Grouping / metadata | No |
| `city_name` | Human-readable city name. | Metadata | No |
| `climate_group` | Broad climate grouping label for the city. | Predictor / stratifier | Yes |
| `cell_id` | Cell identifier within the city grid. | Cell metadata | No |
| `centroid_lon` | Cell centroid longitude in WGS84. | Mapping metadata | No |
| `centroid_lat` | Cell centroid latitude in WGS84. | Mapping metadata | No |
| `impervious_pct` | NLCD impervious percentage for the cell. | Predictor | Yes |
| `land_cover_class` | NLCD land-cover class code for the cell. | Predictor / water filter | Yes |
| `elevation_m` | DEM-derived elevation in meters. | Predictor | Yes |
| `dist_to_water_m` | Distance from the cell to the nearest hydro feature in meters. | Predictor | Yes |
| `ndvi_median_may_aug` | Median May-August NDVI derived from AppEEARS MODIS/Terra MOD13A1.061 inputs. | Predictor | Yes |
| `lst_median_may_aug` | Median May-August 2023 daytime land surface temperature derived from ECOSTRESS/AppEEARS inputs. | Outcome ingredient | No |
| `n_valid_ecostress_passes` | Number of valid ECOSTRESS observations contributing to the cell-level LST summary. | Quality filter / support field | No |
| `hotspot_10pct` | Binary indicator for whether the cell falls in the within-city top 10% of valid LST values. | Target | Target only |
| `tree_cover_proxy_pct_270m` | Share of nearby 30 m cells within an approximately 270 m neighborhood in NLCD forest classes 41/42/43. | Supplemental neighborhood-context feature | No |
| `vegetated_cover_proxy_pct_270m` | Share of nearby 30 m cells within an approximately 270 m neighborhood in selected NLCD vegetated classes. | Supplemental neighborhood-context feature | No |
| `impervious_pct_mean_270m` | Neighborhood mean NLCD impervious percentage within an approximately 270 m window. | Supplemental neighborhood-context feature | No |

\endgroup

### Appendix Table A2. Model Run Metadata

\begingroup
\small

| Model checkpoint | Preset | Rows per city | Outer folds | Inner CV splits | Candidate settings | Estimated inner fits | Scoring |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| Logistic SAGA 5k | full | 5,000 | 0-4 | 4 | 20 | 400 | average precision |
| Random forest 5k | targeted RF search | 5,000 | 0-4 | 3 | 8 | 120 | average precision |

\endgroup

Metrics: Logistic SAGA 5k reached PR AUC 0.1421, mean city PR AUC 0.1803, and recall@top10 0.1647. Random forest 5k reached PR AUC 0.1486, mean city PR AUC 0.1781, and recall@top10 0.1961.

The logistic run tuned regularization strength and `l1_ratio` values corresponding to L2, L1, and elastic-net variants. The random-forest run tuned tree count, maximum depth, feature subsampling, and minimum leaf size. Selected hyperparameters varied by outer fold.

### Appendix Table A3. Model and Baseline Specifications

\begingroup
\small

| Model / baseline | Predictors | Preprocessing | Tuning grid or rule | Scoring | Grouped CV? |
| --- | --- | --- | --- | --- | --- |
| No-skill / prevalence reference | None | None | Reference PR AUC and top-decile recall equal to the 10% target rate. | PR AUC and recall@top10 | Reference only |
| Global-mean baseline | None | Training-city target mean | Predict the training-city hotspot prevalence for all held-out rows. | PR AUC and recall@top10 | Outer city folds only |
| Climate-only baseline | `climate_group` | Training-city category means | Predict training-city hotspot prevalence by climate group. | PR AUC and recall@top10 | Outer city folds only |
| Land-cover-only baseline | `land_cover_class` | Training-city category means | Predict training-city hotspot prevalence by land-cover class. | PR AUC and recall@top10 | Outer city folds only |
| Impervious-only baseline | `impervious_pct` | Training-city decile bins | Predict training-city hotspot prevalence by imperviousness bin. | PR AUC and recall@top10 | Outer city folds only |
| Logistic SAGA 5k | Six non-thermal predictors | Training-only imputation, numeric scaling, and categorical one-hot encoding inside sklearn Pipeline | `C` = 0.01, 0.1, 1.0, 10.0; `l1_ratio` = 0.0, 0.2, 0.5, 0.8, 1.0 | Inner-CV average precision; held-out PR AUC and recall@top10 | Yes, grouped outer folds and grouped inner CV |
| Random forest 5k | Same six non-thermal predictors | Training-only imputation and categorical one-hot encoding inside sklearn Pipeline | `n_estimators` = 200, 300; `max_depth` = 10, 20; `max_features` = sqrt; `min_samples_leaf` = 1, 5 | Inner-CV average precision; held-out PR AUC and recall@top10 | Yes, grouped outer folds and grouped inner CV |

\endgroup

### Appendix Table A4. City and Fold Composition

\begingroup
\small

| City ID | City | Climate group | Final rows | Hotspot count | Hotspot prevalence | Outer fold |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Phoenix | Hot-arid | 3,199,440 | 319,949 | 0.1000 | 2 |
| 2 | Tucson | Hot-arid | 1,779,906 | 177,991 | 0.1000 | 0 |
| 3 | Las Vegas | Hot-arid | 1,718,669 | 171,867 | 0.1000 | 3 |
| 4 | Albuquerque | Hot-arid | 1,336,755 | 133,676 | 0.1000 | 4 |
| 5 | El Paso | Hot-arid | 738,527 | 73,853 | 0.1000 | 4 |
| 6 | Denver | Hot-arid | 1,859,393 | 185,943 | 0.1000 | 1 |
| 7 | Salt Lake City | Hot-arid | 863,557 | 86,356 | 0.1000 | 1 |
| 8 | Fresno | Hot-arid | 459,104 | 45,912 | 0.1000 | 1 |
| 9 | Bakersfield | Hot-arid | 382,964 | 38,297 | 0.1000 | 0 |
| 10 | Reno | Hot-arid | 475,828 | 47,583 | 0.1000 | 2 |
| 11 | Houston | Hot-humid | 5,054,661 | 505,468 | 0.1000 | 2 |
| 12 | Columbia | Hot-humid | 1,055,916 | 105,626 | 0.1000 | 2 |
| 13 | Richmond | Hot-humid | 1,481,846 | 148,185 | 0.1000 | 0 |
| 14 | New Orleans | Hot-humid | 700,063 | 70,008 | 0.1000 | 3 |
| 15 | Tampa | Hot-humid | 2,847,118 | 284,712 | 0.1000 | 0 |
| 16 | Miami | Hot-humid | 3,635,068 | 363,510 | 0.1000 | 3 |
| 17 | Jacksonville | Hot-humid | 1,664,542 | 166,458 | 0.1000 | 2 |
| 18 | Atlanta | Hot-humid | 7,081,699 | 708,171 | 0.1000 | 0 |
| 19 | Charlotte | Hot-humid | 1,896,996 | 189,703 | 0.1000 | 3 |
| 20 | Nashville | Hot-humid | 1,680,248 | 168,025 | 0.1000 | 4 |
| 21 | Seattle | Mild-cool | 2,831,875 | 283,189 | 0.1000 | 2 |
| 22 | Portland | Mild-cool | 1,496,116 | 149,618 | 0.1000 | 1 |
| 23 | San Francisco | Mild-cool | 1,466,276 | 146,628 | 0.1000 | 3 |
| 24 | San Jose | Mild-cool | 817,627 | 81,764 | 0.1000 | 0 |
| 25 | Los Angeles | Mild-cool | 4,736,063 | 473,607 | 0.1000 | 4 |
| 26 | San Diego | Mild-cool | 1,948,679 | 194,869 | 0.1000 | 4 |
| 27 | Chicago | Mild-cool | 6,722,963 | 672,306 | 0.1000 | 1 |
| 28 | Minneapolis | Mild-cool | 2,946,162 | 294,619 | 0.1000 | 1 |
| 29 | Detroit | Mild-cool | 3,702,849 | 370,291 | 0.1000 | 4 |
| 30 | Boston | Mild-cool | 4,813,984 | 481,404 | 0.1000 | 3 |

\endgroup

### Appendix Figure A1. Final Dataset Row Counts by City and Climate Group

![Final Dataset Row Counts by City and Climate Group](figures/final_dataset_city_row_counts.png){width=0.9\textwidth}

Final row counts vary substantially by city because buffered study-area extents differ.

### Appendix Figure A2. Supplemental Feature-Importance Summary

![Supplemental Feature-Importance Summary](figures/feature_importance_ranked_summary.png){width=0.9\textwidth}

Permutation importance and coefficient summaries are included as predictive diagnostics only. They are not causal estimates of how changing an urban feature would change LST.

### Appendix Figure A3. Denver Held-Out Map Triptych

![Denver Held-Out Map Triptych](figures/denver_heldout_map_triptych.png){width=0.95\textwidth}

Representative held-out Denver benchmark snapshot showing predicted hotspots, true hotspots, and error pattern. This is a sampled benchmark slice, not a full citywide deployment map.

### Reproducibility Notes

Report-facing tables and generated figures are regenerated with:

```powershell
C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m src.run_report_artifacts
```

Canonical dataset and modeling-prep artifacts:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`
- `data_processed/modeling/final_dataset_audit.md`
- `data_processed/modeling/final_dataset_audit_summary.json`
- `data_processed/modeling/final_dataset_city_summary.csv`
- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Report table and figure artifacts:

- `docs/report/tables/data_sources_variables.csv`
- `docs/report/tables/final_dataset_by_climate_group.csv`
- `docs/report/tables/benchmark_metrics.csv`
- `docs/report/tables/rf_vs_logistic_by_climate.csv`
- `docs/report/tables/rf_vs_logistic_by_fold.csv`
- `docs/report/tables/rf_vs_logistic_city_paired_summary.csv`
- `docs/report/tables/final_dataset_columns.csv`
- `docs/report/tables/model_baseline_specifications.csv`
- `docs/report/tables/city_fold_composition.csv`
- `docs/report/tables/retained_model_run_metadata.csv`
- `docs/report/figures/study_city_points.png`
- `docs/report/figures/workflow_overview.svg`
- `docs/report/figures/workflow_overview.png`
- `docs/report/figures/evaluation_design.svg`
- `docs/report/figures/evaluation_design.png`
- `docs/report/figures/benchmark_metrics.png`
- `docs/report/figures/city_metric_deltas.png`
- `docs/report/figures/feature_importance_ranked_summary.png`
- `docs/report/figures/denver_heldout_map_triptych.png`
- `docs/report/figures/final_dataset_city_row_counts.png`

The PDF render uses PNG figure files so the report does not depend on local SVG conversion support.

Benchmark source artifacts:

- `outputs/modeling/reporting/cross_city_benchmark_report.md`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_by_climate.csv`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_comparison.csv`
- `outputs/modeling/logistic_saga/full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825/`
- `outputs/modeling/logistic_saga/full_allfolds_s20000_samplecurve-20k_2026-04-08_021152/`
- retained random-forest 5k run directory listed in Appendix Table A2 metadata

Supplemental interpretation and map artifacts, if used, should remain explicitly supplemental:

- `outputs/modeling/supplemental/feature_importance/feature_importance_summary.md`
- `outputs/modeling/reporting/heldout_city_maps/heldout_city_maps.md`
