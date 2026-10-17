### minutes  (best: E_lightgbm; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 5.462 | 7.033 | -0.264 | 3.859 | 0.801 | 0.999 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 5.076 | 6.546 | 0.075 | 3.574 | 0.801 | 0.999 | -0.285 [-0.295, -0.274] | n/a | competitive |
| C_role_blend | development | 149265 | 4.913 | 6.381 | -0.014 | 3.492 | 0.800 | 0.999 | -0.367 [-0.379, -0.357] | n/a | competitive |
| D_role_plus_context | development | 149265 | 4.888 | 6.346 | -0.016 | 3.472 | 0.800 | 0.999 | -0.387 [-0.399, -0.376] | n/a | competitive |
| E_lightgbm | development | 149265 | 4.776 | 6.181 | -0.132 | 3.387 | 0.800 | 0.999 | -0.472 [-0.486, -0.460] | n/a | best |
| F_stack | development | 149265 | 4.775 | 6.179 | -0.121 | 3.385 | 0.800 | 0.999 | -0.474 [-0.488, -0.462] | n/a | competitive |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 4.635 | 5.981 | 0.193 | 3.286 | 0.800 | 0.999 | -0.573 [-0.589, -0.559] | n/a | competitive |
| ORACLE_knows_starters | development | 149265 | 4.478 | 5.751 | 0.149 | 3.169 | 0.801 | 0.999 | -0.690 [-0.705, -0.675] | n/a | oracle |
| A_season_avg_shrunk | validation | 52127 | 5.606 | 7.220 | -0.094 | 3.951 | 0.784 | 1.038 | +0.000 [+0.000, +0.000] | -0.517 [-0.555, -0.482] | baseline |
| B_ewma_shrunk | validation | 52127 | 5.197 | 6.694 | 0.100 | 3.639 | 0.790 | 1.026 | -0.313 [-0.334, -0.293] | -0.837 [-0.864, -0.809] | competitive |
| C_role_blend | validation | 52127 | 5.022 | 6.534 | -0.029 | 3.562 | 0.790 | 1.028 | -0.389 [-0.411, -0.369] | -0.897 [-0.926, -0.871] | competitive |
| D_role_plus_context | validation | 52127 | 4.995 | 6.492 | 0.002 | 3.539 | 0.788 | 1.028 | -0.412 [-0.435, -0.391] | -0.914 [-0.944, -0.886] | competitive |
| E_lightgbm | validation | 52127 | 4.843 | 6.281 | 0.091 | 3.430 | 0.790 | 1.022 | -0.522 [-0.546, -0.497] | -0.988 [-1.022, -0.954] | best |
| F_stack | validation | 52127 | 4.845 | 6.281 | 0.083 | 3.428 | 0.791 | 1.022 | -0.523 [-0.548, -0.499] | -0.990 [-1.024, -0.957] | competitive |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 4.618 | 5.976 | 0.143 | 3.273 | 0.798 | 1.003 | -0.679 [-0.706, -0.649] | -1.141 [-1.177, -1.105] | competitive |
| ORACLE_knows_starters | validation | 52127 | 4.454 | 5.755 | 0.103 | 3.155 | 0.799 | 0.997 | -0.797 [-0.827, -0.766] | -1.255 [-1.293, -1.218] | oracle |
| incumbent_sim_rotation | validation | 50171 | 6.058 | 7.940 | -2.308 | 4.404 | 0.810 | 0.925 | +0.517 [+0.482, +0.555] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 5.510 | 7.132 | -0.317 | 3.897 | 0.799 | 0.999 | +0.000 [+0.000, +0.000] | -0.686 [-0.724, -0.651] | baseline |
| E_lightgbm | holdout | 52796 | 4.764 | 6.218 | 0.086 | 3.392 | 0.800 | 0.990 | -0.505 [-0.529, -0.479] | -1.145 [-1.181, -1.110] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 4.547 | 5.918 | 0.305 | 3.238 | 0.807 | 0.975 | -0.658 [-0.688, -0.628] | -1.293 [-1.332, -1.255] | competitive |
| ORACLE_knows_starters | holdout | 52796 | 4.379 | 5.689 | 0.262 | 3.118 | 0.810 | 0.970 | -0.779 [-0.808, -0.747] | -1.412 [-1.454, -1.373] | oracle |
| incumbent_sim_rotation | holdout | 50615 | 6.168 | 8.130 | -2.419 | 4.523 | 0.819 | 0.906 | +0.686 [+0.651, +0.724] | n/a | incumbent |

### points  (best: E_lightgbm+empirical; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 4.607 | 5.953 | -0.209 | 3.234 | 0.763 | 1.089 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 4.561 | 5.881 | 0.004 | 3.187 | 0.761 | 1.093 | -0.047 [-0.051, -0.044] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 4.431 | 5.769 | -0.061 | 3.109 | 0.767 | 1.081 | -0.125 [-0.131, -0.120] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 4.424 | 5.757 | -0.031 | 3.102 | 0.767 | 1.082 | -0.132 [-0.138, -0.126] | n/a | competitive |
| E_lightgbm+empirical | development | 149265 | 4.425 | 5.757 | -0.030 | 3.096 | 0.800 | 0.999 | -0.138 [-0.144, -0.133] | n/a | best |
| F_stack | development | 149265 | 4.417 | 5.744 | -0.038 | 3.095 | 0.767 | 1.082 | -0.138 [-0.144, -0.133] | n/a | competitive |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 4.389 | 5.697 | 0.098 | 3.067 | 0.764 | 1.088 | -0.167 [-0.173, -0.161] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 4.750 | 6.155 | -0.083 | 3.325 | 0.755 | 1.107 | +0.000 [+0.000, +0.000] | -0.187 [-0.204, -0.169] | baseline |
| B_ewma_shrunk | validation | 52127 | 4.692 | 6.074 | 0.095 | 3.272 | 0.754 | 1.107 | -0.052 [-0.059, -0.046] | -0.239 [-0.255, -0.223] | competitive |
| C_minutes_x_rate | validation | 52127 | 4.547 | 5.943 | 0.093 | 3.181 | 0.763 | 1.091 | -0.144 [-0.155, -0.133] | -0.309 [-0.326, -0.292] | competitive |
| D_opp_adjusted | validation | 52127 | 4.537 | 5.931 | 0.071 | 3.175 | 0.763 | 1.093 | -0.149 [-0.160, -0.138] | -0.315 [-0.331, -0.298] | competitive |
| E_lightgbm+empirical | validation | 52127 | 4.519 | 5.911 | 0.066 | 3.159 | 0.799 | 1.002 | -0.166 [-0.177, -0.155] | -0.330 [-0.348, -0.314] | best |
| F_stack | validation | 52127 | 4.525 | 5.914 | 0.061 | 3.167 | 0.762 | 1.092 | -0.158 [-0.168, -0.148] | -0.323 [-0.340, -0.306] | competitive |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 4.443 | 5.818 | 0.073 | 3.110 | 0.763 | 1.092 | -0.215 [-0.227, -0.203] | -0.379 [-0.397, -0.361] | competitive |
| incumbent_sim | validation | 50171 | 4.878 | 6.538 | -1.243 | 3.527 | 0.790 | 0.985 | +0.187 [+0.169, +0.204] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 4.750 | 6.163 | -0.232 | 3.341 | 0.751 | 1.117 | +0.000 [+0.000, +0.000] | -0.229 [-0.248, -0.210] | baseline |
| E_lightgbm+empirical | holdout | 52796 | 4.518 | 5.909 | -0.033 | 3.166 | 0.792 | 1.015 | -0.175 [-0.187, -0.165] | -0.383 [-0.401, -0.366] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 4.454 | 5.822 | 0.129 | 3.117 | 0.761 | 1.098 | -0.224 [-0.237, -0.210] | -0.431 [-0.451, -0.412] | competitive |
| incumbent_sim | holdout | 50615 | 4.933 | 6.577 | -1.222 | 3.590 | 0.795 | 0.978 | +0.229 [+0.210, +0.248] | n/a | incumbent |

### rebounds  (best: F_stack+mixture; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 1.944 | 2.552 | -0.041 | 1.355 | 0.795 | 1.010 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 1.931 | 2.530 | 0.008 | 1.341 | 0.795 | 1.011 | -0.013 [-0.015, -0.012] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 1.877 | 2.478 | -0.043 | 1.308 | 0.798 | 1.002 | -0.047 [-0.049, -0.045] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 1.875 | 2.471 | -0.018 | 1.304 | 0.799 | 1.002 | -0.050 [-0.053, -0.048] | n/a | competitive |
| E_lightgbm | development | 149265 | 1.882 | 2.478 | -0.012 | 1.308 | 0.799 | 1.003 | -0.047 [-0.049, -0.044] | n/a | competitive |
| F_stack+mixture | development | 149265 | 1.874 | 2.468 | -0.016 | 1.300 | 0.793 | 1.016 | -0.054 [-0.057, -0.052] | n/a | best |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 1.873 | 2.460 | 0.034 | 1.298 | 0.797 | 1.006 | -0.057 [-0.059, -0.055] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 1.946 | 2.551 | 0.010 | 1.350 | 0.792 | 1.016 | +0.000 [+0.000, +0.000] | -0.074 [-0.081, -0.067] | baseline |
| B_ewma_shrunk | validation | 52127 | 1.925 | 2.523 | 0.039 | 1.334 | 0.792 | 1.015 | -0.016 [-0.018, -0.013] | -0.090 [-0.096, -0.083] | competitive |
| C_minutes_x_rate | validation | 52127 | 1.868 | 2.467 | 0.035 | 1.296 | 0.799 | 1.000 | -0.054 [-0.058, -0.050] | -0.121 [-0.128, -0.115] | competitive |
| D_opp_adjusted | validation | 52127 | 1.864 | 2.463 | 0.016 | 1.294 | 0.798 | 1.002 | -0.056 [-0.060, -0.051] | -0.123 [-0.130, -0.117] | competitive |
| E_lightgbm | validation | 52127 | 1.865 | 2.462 | 0.025 | 1.294 | 0.798 | 1.000 | -0.056 [-0.059, -0.051] | -0.123 [-0.130, -0.116] | competitive |
| F_stack+mixture | validation | 52127 | 1.863 | 2.461 | 0.019 | 1.290 | 0.791 | 1.018 | -0.060 [-0.064, -0.055] | -0.127 [-0.134, -0.120] | best |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 1.843 | 2.437 | 0.029 | 1.278 | 0.800 | 0.999 | -0.072 [-0.077, -0.067] | -0.139 [-0.145, -0.131] | competitive |
| incumbent_sim | validation | 50171 | 1.978 | 2.655 | -0.252 | 1.428 | 0.800 | 0.990 | +0.074 [+0.067, +0.081] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 1.941 | 2.550 | -0.052 | 1.353 | 0.789 | 1.021 | +0.000 [+0.000, +0.000] | -0.108 [-0.116, -0.101] | baseline |
| F_stack+mixture | holdout | 52796 | 1.870 | 2.462 | 0.005 | 1.295 | 0.789 | 1.024 | -0.058 [-0.063, -0.054] | -0.159 [-0.166, -0.152] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 1.853 | 2.437 | 0.046 | 1.283 | 0.796 | 1.008 | -0.070 [-0.075, -0.065] | -0.171 [-0.179, -0.163] | competitive |
| incumbent_sim | holdout | 50615 | 2.014 | 2.715 | -0.390 | 1.467 | 0.793 | 0.992 | +0.108 [+0.101, +0.116] | n/a | incumbent |

### assists  (best: E_lightgbm+mixture; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 1.288 | 1.763 | -0.067 | 0.877 | 0.797 | 1.007 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 1.284 | 1.744 | -0.003 | 0.868 | 0.798 | 1.007 | -0.009 [-0.010, -0.008] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 1.254 | 1.721 | -0.041 | 0.852 | 0.798 | 1.005 | -0.026 [-0.027, -0.024] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 1.252 | 1.716 | -0.021 | 0.849 | 0.798 | 1.004 | -0.028 [-0.029, -0.027] | n/a | competitive |
| E_lightgbm+mixture | development | 149265 | 1.254 | 1.715 | 0.012 | 0.848 | 0.794 | 1.012 | -0.030 [-0.031, -0.028] | n/a | best |
| F_stack | development | 149265 | 1.250 | 1.710 | -0.004 | 0.847 | 0.799 | 1.001 | -0.031 [-0.032, -0.030] | n/a | competitive |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 1.249 | 1.702 | 0.040 | 0.842 | 0.799 | 0.999 | -0.036 [-0.037, -0.034] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 1.347 | 1.835 | -0.065 | 0.921 | 0.796 | 1.011 | +0.000 [+0.000, +0.000] | -0.036 [-0.041, -0.031] | baseline |
| B_ewma_shrunk | validation | 52127 | 1.337 | 1.811 | -0.005 | 0.908 | 0.797 | 1.007 | -0.013 [-0.015, -0.011] | -0.049 [-0.053, -0.045] | competitive |
| C_minutes_x_rate | validation | 52127 | 1.302 | 1.781 | -0.034 | 0.887 | 0.799 | 1.001 | -0.034 [-0.036, -0.031] | -0.065 [-0.070, -0.061] | competitive |
| D_opp_adjusted | validation | 52127 | 1.302 | 1.778 | -0.010 | 0.885 | 0.799 | 1.000 | -0.035 [-0.038, -0.033] | -0.067 [-0.071, -0.063] | competitive |
| E_lightgbm+mixture | validation | 52127 | 1.298 | 1.770 | 0.003 | 0.881 | 0.797 | 1.004 | -0.040 [-0.043, -0.037] | -0.071 [-0.075, -0.067] | best |
| F_stack | validation | 52127 | 1.298 | 1.771 | -0.003 | 0.882 | 0.799 | 0.998 | -0.039 [-0.041, -0.036] | -0.070 [-0.074, -0.066] | competitive |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 1.284 | 1.751 | 0.007 | 0.871 | 0.800 | 0.995 | -0.050 [-0.053, -0.047] | -0.081 [-0.086, -0.077] | competitive |
| incumbent_sim | validation | 50171 | 1.365 | 1.918 | -0.285 | 0.964 | 0.778 | 1.033 | +0.036 [+0.031, +0.041] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 1.368 | 1.855 | -0.067 | 0.937 | 0.795 | 1.013 | +0.000 [+0.000, +0.000] | -0.056 [-0.060, -0.051] | baseline |
| E_lightgbm+mixture | holdout | 52796 | 1.323 | 1.795 | 0.000 | 0.899 | 0.797 | 1.008 | -0.037 [-0.040, -0.035] | -0.089 [-0.094, -0.085] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 1.314 | 1.779 | 0.039 | 0.891 | 0.799 | 1.001 | -0.046 [-0.050, -0.043] | -0.098 [-0.103, -0.093] | competitive |
| incumbent_sim | holdout | 50615 | 1.402 | 1.965 | -0.329 | 1.002 | 0.778 | 1.031 | +0.056 [+0.051, +0.060] | n/a | incumbent |

### threes  (best: F_stack+mixture; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 0.808 | 1.153 | -0.043 | 0.530 | 0.797 | 1.009 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 0.808 | 1.150 | -0.018 | 0.528 | 0.797 | 1.007 | -0.002 [-0.003, -0.002] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 0.794 | 1.141 | -0.033 | 0.522 | 0.795 | 1.014 | -0.008 [-0.009, -0.007] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 0.795 | 1.139 | -0.015 | 0.521 | 0.795 | 1.011 | -0.009 [-0.010, -0.009] | n/a | competitive |
| E_lightgbm | development | 149265 | 0.798 | 1.139 | 0.002 | 0.520 | 0.799 | 1.002 | -0.010 [-0.011, -0.009] | n/a | competitive |
| F_stack+mixture | development | 149265 | 0.795 | 1.136 | -0.008 | 0.519 | 0.793 | 1.015 | -0.011 [-0.012, -0.010] | n/a | best |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 0.798 | 1.135 | 0.014 | 0.518 | 0.800 | 1.000 | -0.012 [-0.013, -0.011] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 0.869 | 1.218 | -0.019 | 0.570 | 0.798 | 1.003 | +0.000 [+0.000, +0.000] | -0.019 [-0.021, -0.016] | baseline |
| B_ewma_shrunk | validation | 52127 | 0.868 | 1.215 | -0.001 | 0.568 | 0.799 | 1.000 | -0.002 [-0.003, -0.001] | -0.021 [-0.023, -0.019] | competitive |
| C_minutes_x_rate | validation | 52127 | 0.853 | 1.201 | 0.001 | 0.559 | 0.798 | 1.002 | -0.011 [-0.012, -0.010] | -0.028 [-0.030, -0.026] | competitive |
| D_opp_adjusted | validation | 52127 | 0.852 | 1.199 | 0.002 | 0.558 | 0.798 | 1.003 | -0.012 [-0.013, -0.011] | -0.029 [-0.031, -0.027] | competitive |
| E_lightgbm | validation | 52127 | 0.850 | 1.198 | -0.003 | 0.557 | 0.799 | 0.999 | -0.013 [-0.014, -0.012] | -0.030 [-0.032, -0.028] | competitive |
| F_stack+mixture | validation | 52127 | 0.850 | 1.197 | -0.001 | 0.557 | 0.794 | 1.008 | -0.013 [-0.015, -0.012] | -0.031 [-0.033, -0.029] | best |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 0.846 | 1.193 | -0.002 | 0.554 | 0.799 | 0.999 | -0.016 [-0.017, -0.015] | -0.033 [-0.035, -0.031] | competitive |
| incumbent_sim | validation | 50171 | 0.879 | 1.254 | -0.134 | 0.596 | 0.783 | 1.036 | +0.019 [+0.016, +0.021] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 0.899 | 1.249 | -0.040 | 0.595 | 0.794 | 1.020 | +0.000 [+0.000, +0.000] | -0.024 [-0.026, -0.021] | baseline |
| F_stack+mixture | holdout | 52796 | 0.882 | 1.229 | -0.006 | 0.581 | 0.792 | 1.021 | -0.014 [-0.015, -0.012] | -0.036 [-0.038, -0.034] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 0.878 | 1.224 | 0.014 | 0.578 | 0.798 | 1.009 | -0.017 [-0.019, -0.016] | -0.039 [-0.042, -0.037] | competitive |
| incumbent_sim | holdout | 50615 | 0.918 | 1.290 | -0.139 | 0.627 | 0.780 | 1.042 | +0.024 [+0.021, +0.026] | n/a | incumbent |

### pra  (best: E_lightgbm+nb; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 6.146 | 7.840 | -0.317 | 4.334 | 0.774 | 1.058 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 6.045 | 7.695 | 0.009 | 4.242 | 0.773 | 1.063 | -0.092 [-0.098, -0.087] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 5.802 | 7.460 | -0.117 | 4.090 | 0.780 | 1.047 | -0.244 [-0.254, -0.235] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 5.791 | 7.442 | -0.051 | 4.079 | 0.779 | 1.048 | -0.255 [-0.264, -0.246] | n/a | competitive |
| E_lightgbm+nb | development | 149265 | 5.801 | 7.450 | -0.024 | 4.082 | 0.779 | 1.048 | -0.252 [-0.261, -0.244] | n/a | best |
| F_stack | development | 149265 | 5.786 | 7.429 | -0.048 | 4.072 | 0.779 | 1.048 | -0.262 [-0.271, -0.254] | n/a | competitive |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 5.728 | 7.342 | 0.164 | 4.019 | 0.776 | 1.056 | -0.315 [-0.325, -0.305] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 6.382 | 8.122 | -0.137 | 4.477 | 0.759 | 1.095 | +0.000 [+0.000, +0.000] | -0.319 [-0.347, -0.291] | baseline |
| B_ewma_shrunk | validation | 52127 | 6.252 | 7.957 | 0.129 | 4.375 | 0.759 | 1.094 | -0.102 [-0.112, -0.092] | -0.422 [-0.447, -0.397] | competitive |
| C_minutes_x_rate | validation | 52127 | 5.972 | 7.690 | 0.104 | 4.197 | 0.769 | 1.072 | -0.280 [-0.297, -0.262] | -0.562 [-0.587, -0.535] | competitive |
| D_opp_adjusted | validation | 52127 | 5.956 | 7.671 | 0.080 | 4.188 | 0.768 | 1.073 | -0.289 [-0.306, -0.272] | -0.572 [-0.597, -0.545] | competitive |
| E_lightgbm+nb | validation | 52127 | 5.947 | 7.656 | 0.118 | 4.179 | 0.769 | 1.068 | -0.297 [-0.315, -0.280] | -0.579 [-0.606, -0.554] | best |
| F_stack | validation | 52127 | 5.949 | 7.656 | 0.089 | 4.181 | 0.768 | 1.073 | -0.296 [-0.312, -0.279] | -0.578 [-0.604, -0.552] | competitive |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 5.811 | 7.490 | 0.126 | 4.083 | 0.769 | 1.072 | -0.394 [-0.414, -0.373] | -0.674 [-0.702, -0.646] | competitive |
| incumbent_sim | validation | 50171 | 6.597 | 8.707 | -1.781 | 4.795 | 0.787 | 0.986 | +0.319 [+0.291, +0.347] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 6.352 | 8.119 | -0.350 | 4.484 | 0.760 | 1.093 | +0.000 [+0.000, +0.000] | -0.428 [-0.460, -0.401] | baseline |
| E_lightgbm+nb | holdout | 52796 | 5.923 | 7.643 | -0.028 | 4.176 | 0.771 | 1.068 | -0.308 [-0.326, -0.289] | -0.700 [-0.728, -0.672] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 5.797 | 7.479 | 0.211 | 4.077 | 0.770 | 1.070 | -0.407 [-0.429, -0.384] | -0.798 [-0.830, -0.766] | competitive |
| incumbent_sim | holdout | 50615 | 6.713 | 8.848 | -1.942 | 4.917 | 0.792 | 0.970 | +0.428 [+0.401, +0.460] | n/a | incumbent |

### fga  (best: E_lightgbm+mixture; readiness READY)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 149265 | 2.861 | 3.688 | -0.104 | 2.014 | 0.795 | 1.012 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 149265 | 2.800 | 3.601 | 0.030 | 1.963 | 0.794 | 1.012 | -0.051 [-0.054, -0.049] | n/a | competitive |
| C_minutes_x_rate | development | 149265 | 2.672 | 3.469 | -0.037 | 1.880 | 0.799 | 1.000 | -0.135 [-0.139, -0.130] | n/a | competitive |
| D_opp_adjusted | development | 149265 | 2.666 | 3.458 | -0.014 | 1.874 | 0.799 | 1.000 | -0.140 [-0.145, -0.136] | n/a | competitive |
| E_lightgbm+mixture | development | 149265 | 2.670 | 3.464 | 0.017 | 1.875 | 0.810 | 0.969 | -0.140 [-0.144, -0.135] | n/a | best |
| F_stack | development | 149265 | 2.662 | 3.453 | -0.002 | 1.871 | 0.799 | 0.999 | -0.143 [-0.148, -0.139] | n/a | competitive |
| E_inj_lightgbm_teammate_absence_proxy | development | 149265 | 2.627 | 3.400 | 0.123 | 1.841 | 0.797 | 1.003 | -0.173 [-0.179, -0.169] | n/a | competitive |
| A_season_avg_shrunk | validation | 52127 | 2.949 | 3.808 | -0.008 | 2.067 | 0.780 | 1.044 | +0.000 [+0.000, +0.000] | -0.176 [-0.189, -0.162] | baseline |
| B_ewma_shrunk | validation | 52127 | 2.881 | 3.714 | 0.087 | 2.013 | 0.782 | 1.040 | -0.054 [-0.059, -0.049] | -0.230 [-0.242, -0.219] | competitive |
| C_minutes_x_rate | validation | 52127 | 2.734 | 3.560 | 0.067 | 1.915 | 0.791 | 1.020 | -0.152 [-0.160, -0.143] | -0.308 [-0.321, -0.295] | competitive |
| D_opp_adjusted | validation | 52127 | 2.726 | 3.551 | 0.037 | 1.911 | 0.791 | 1.021 | -0.156 [-0.165, -0.147] | -0.312 [-0.325, -0.300] | competitive |
| E_lightgbm+mixture | validation | 52127 | 2.720 | 3.544 | 0.058 | 1.904 | 0.803 | 0.992 | -0.163 [-0.172, -0.154] | -0.319 [-0.331, -0.307] | best |
| F_stack | validation | 52127 | 2.721 | 3.545 | 0.045 | 1.908 | 0.792 | 1.020 | -0.159 [-0.168, -0.150] | -0.316 [-0.328, -0.303] | competitive |
| E_inj_lightgbm_teammate_absence_proxy | validation | 52127 | 2.634 | 3.439 | 0.059 | 1.847 | 0.795 | 1.010 | -0.220 [-0.230, -0.208] | -0.375 [-0.388, -0.361] | competitive |
| incumbent_sim | validation | 50171 | 3.072 | 4.125 | -1.011 | 2.237 | 0.799 | 0.944 | +0.176 [+0.162, +0.189] | n/a | incumbent |
| A_season_avg_shrunk | holdout | 52796 | 2.943 | 3.810 | -0.143 | 2.075 | 0.779 | 1.047 | +0.000 [+0.000, +0.000] | -0.236 [-0.250, -0.221] | baseline |
| E_lightgbm+mixture | holdout | 52796 | 2.723 | 3.554 | 0.000 | 1.914 | 0.799 | 0.996 | -0.161 [-0.170, -0.152] | -0.378 [-0.392, -0.366] | best |
| E_inj_lightgbm_teammate_absence_proxy | holdout | 52796 | 2.649 | 3.452 | 0.139 | 1.857 | 0.792 | 1.017 | -0.218 [-0.229, -0.206] | -0.435 [-0.450, -0.419] | competitive |
| incumbent_sim | holdout | 50615 | 3.147 | 4.231 | -1.137 | 2.310 | 0.799 | 0.935 | +0.236 [+0.221, +0.250] | n/a | incumbent |

### team_points  (best: D_ratings_plus_rest; readiness SHADOW VALIDATION)

| model | split | n | MAE | RMSE | bias | CRPS | cover80 | PITvar | vs A (CRPS) | vs incumbent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_season_avg_shrunk | development | 14112 | 9.588 | 12.041 | -1.173 | 6.776 | 0.801 | 0.993 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | development | 14112 | 9.548 | 11.981 | -0.605 | 6.744 | 0.803 | 0.998 | -0.032 [-0.049, -0.014] | n/a | competitive |
| C_pace_x_efficiency_ridge | development | 14112 | 9.373 | 11.787 | -1.481 | 6.636 | 0.797 | 0.995 | -0.140 [-0.188, -0.092] | n/a | competitive |
| D_ratings_plus_rest | development | 14112 | 9.289 | 11.676 | 0.077 | 6.575 | 0.799 | 1.002 | -0.200 [-0.253, -0.149] | n/a | best |
| A_season_avg_shrunk | validation | 4922 | 9.666 | 12.156 | -0.805 | 6.844 | 0.807 | 0.985 | +0.000 [+0.000, +0.000] | n/a | baseline |
| B_ewma_shrunk | validation | 4922 | 9.593 | 12.053 | -0.285 | 6.790 | 0.804 | 0.985 | -0.055 [-0.087, -0.021] | n/a | competitive |
| C_pace_x_efficiency_ridge | validation | 4922 | 9.443 | 11.845 | -0.993 | 6.664 | 0.805 | 0.991 | -0.180 [-0.266, -0.094] | n/a | competitive |
| D_ratings_plus_rest | validation | 4922 | 9.406 | 11.798 | 0.565 | 6.641 | 0.803 | 0.992 | -0.204 [-0.295, -0.116] | n/a | best |
| A_season_avg_shrunk | holdout | 4924 | 9.950 | 12.466 | -0.492 | 7.037 | 0.784 | 1.025 | +0.000 [+0.000, +0.000] | n/a | baseline |
| D_ratings_plus_rest | holdout | 4924 | 9.460 | 11.875 | 0.702 | 6.698 | 0.794 | 1.002 | -0.339 [-0.420, -0.251] | n/a | best |
