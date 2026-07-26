{
  "engine_version": "3.1.0-audited",
  "generated_on": "2026-07-26",
  "next_draw_date": "2026-07-28",
  "random_seed": 20260726,
  "data": {
    "draws": 975,
    "first_date": "2012-03-23",
    "last_date": "2026-07-24",
    "calendar_audit": {
      "expected_dates": 975,
      "actual_dates": 975,
      "missing_dates": [],
      "off_schedule_dates": [],
      "duplicate_dates": 0,
      "pass": true
    },
    "uploaded_crosscheck": {
      "matched": 235,
      "tested": 235,
      "mismatches": 0
    },
    "history_file": "/mnt/data/EuroJackpot_Canonical_History_v3.csv"
  },
  "known_operational_breakpoints": {
    "2014-10-10": "Euro pool 8 to 10",
    "2022-03-25": "Euro pool 10 to 12; Tuesday draw introduced",
    "2024-03-08": "Studio/set sensitivity breakpoint only; no verified draw-machine change assumed"
  },
  "main_pool": {
    "dev_draws": 780,
    "holdout_draws": 195,
    "selected_features": [
      "number_norm",
      "number_sin",
      "number_cos",
      "is_odd",
      "is_high",
      "decade_norm",
      "gap_norm",
      "gap_log"
    ],
    "feature_screen": [
      {
        "group": "identity",
        "selection_votes": 3,
        "runs": 3,
        "mean_permutation_delta": 0.0,
        "median_permutation_p": 0.0,
        "keep": true
      },
      {
        "group": "frequency",
        "selection_votes": 1,
        "runs": 3,
        "mean_permutation_delta": 1.564550192773658e-05,
        "median_permutation_p": 0.4,
        "keep": false
      },
      {
        "group": "ewma",
        "selection_votes": 1,
        "runs": 3,
        "mean_permutation_delta": -5.020210387358699e-06,
        "median_permutation_p": 0.7,
        "keep": false
      },
      {
        "group": "gap",
        "selection_votes": 2,
        "runs": 3,
        "mean_permutation_delta": 2.736562288392226e-05,
        "median_permutation_p": 0.1,
        "keep": true
      },
      {
        "group": "trend",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -1.1027465913380992e-05,
        "median_permutation_p": 0.725,
        "keep": false
      },
      {
        "group": "repeat_transition",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 4.663419431575845e-06,
        "median_permutation_p": 0.3,
        "keep": false
      },
      {
        "group": "pair_triple",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 4.824838172335572e-07,
        "median_permutation_p": 0.45,
        "keep": false
      },
      {
        "group": "position",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -1.2079988783909645e-05,
        "median_permutation_p": 0.725,
        "keep": false
      },
      {
        "group": "draw_composition",
        "selection_votes": 1,
        "runs": 3,
        "mean_permutation_delta": 6.026477192520755e-05,
        "median_permutation_p": 0.15,
        "keep": false
      },
      {
        "group": "rule_calendar",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 0.0,
        "median_permutation_p": 1.0,
        "keep": false
      }
    ],
    "nested_fold_metrics": {
      "Uniform": [
        {
          "brier": 0.09,
          "log_loss": 0.3250829733914481,
          "ece": 2.7755575615628914e-17,
          "avg_hits": 0.46794871794871795,
          "precision_at_k": 0.09358974358974359,
          "mean_winning_rank": 26.075641025641026,
          "draws": 156
        },
        {
          "brier": 0.09,
          "log_loss": 0.32508297339144815,
          "ece": 2.7755575615628914e-17,
          "avg_hits": 0.4935897435897436,
          "precision_at_k": 0.09871794871794873,
          "mean_winning_rank": 25.573076923076922,
          "draws": 156
        },
        {
          "brier": 0.09,
          "log_loss": 0.3250829733914482,
          "ece": 2.7755575615628914e-17,
          "avg_hits": 0.47435897435897434,
          "precision_at_k": 0.09487179487179487,
          "mean_winning_rank": 24.705128205128204,
          "draws": 156
        }
      ],
      "FullFrequency": [
        {
          "brier": 0.09023065901928616,
          "log_loss": 0.3263733753771218,
          "ece": 0.015585747400677842,
          "avg_hits": 0.42948717948717946,
          "precision_at_k": 0.0858974358974359,
          "mean_winning_rank": 26.266666666666666,
          "draws": 156
        },
        {
          "brier": 0.0901627764760912,
          "log_loss": 0.32601452589369995,
          "ece": 0.013169503112193365,
          "avg_hits": 0.4935897435897436,
          "precision_at_k": 0.09871794871794873,
          "mean_winning_rank": 26.351282051282052,
          "draws": 156
        },
        {
          "brier": 0.09003156732068278,
          "log_loss": 0.3252428363161022,
          "ece": 0.0049480613618802325,
          "avg_hits": 0.5256410256410257,
          "precision_at_k": 0.10512820512820513,
          "mean_winning_rank": 25.102564102564102,
          "draws": 156
        }
      ],
      "RollingFrequency": [
        {
          "brier": 0.0905928542357114,
          "log_loss": 0.3284195006559454,
          "ece": 0.01926251526251528,
          "avg_hits": 0.44871794871794873,
          "precision_at_k": 0.08974358974358974,
          "mean_winning_rank": 26.31025641025641,
          "draws": 156
        },
        {
          "brier": 0.09040752369323797,
          "log_loss": 0.32743413390497306,
          "ece": 0.016426129426129442,
          "avg_hits": 0.48717948717948717,
          "precision_at_k": 0.09743589743589744,
          "mean_winning_rank": 25.575641025641026,
          "draws": 156
        },
        {
          "brier": 0.09020877958020815,
          "log_loss": 0.3262779622034829,
          "ece": 0.013531135531135548,
          "avg_hits": 0.5192307692307693,
          "precision_at_k": 0.10384615384615385,
          "mean_winning_rank": 24.71923076923077,
          "draws": 156
        }
      ],
      "EWMA": [
        {
          "brier": 0.09044071556957171,
          "log_loss": 0.3275616081733126,
          "ece": 0.015161648409590976,
          "avg_hits": 0.46794871794871795,
          "precision_at_k": 0.09358974358974359,
          "mean_winning_rank": 26.16794871794872,
          "draws": 156
        },
        {
          "brier": 0.09030601337742408,
          "log_loss": 0.32683490075016275,
          "ece": 0.011635871655688395,
          "avg_hits": 0.5128205128205128,
          "precision_at_k": 0.10256410256410256,
          "mean_winning_rank": 25.993589743589745,
          "draws": 156
        },
        {
          "brier": 0.09009046906332756,
          "log_loss": 0.3255698215213444,
          "ece": 0.00896563480765937,
          "avg_hits": 0.5448717948717948,
          "precision_at_k": 0.10897435897435896,
          "mean_winning_rank": 24.664102564102564,
          "draws": 156
        }
      ],
      "BetaBinomial": [
        {
          "brier": 0.09021648630279235,
          "log_loss": 0.3262928267388705,
          "ece": 0.015332183871119003,
          "avg_hits": 0.42948717948717946,
          "precision_at_k": 0.0858974358974359,
          "mean_winning_rank": 26.266666666666666,
          "draws": 156
        },
        {
          "brier": 0.09015529101558391,
          "log_loss": 0.3259708997953736,
          "ece": 0.01285939142259318,
          "avg_hits": 0.4935897435897436,
          "precision_at_k": 0.09871794871794873,
          "mean_winning_rank": 26.351282051282052,
          "draws": 156
        },
        {
          "brier": 0.09002908023076997,
          "log_loss": 0.3252296844187017,
          "ece": 0.004757791425599572,
          "avg_hits": 0.5256410256410257,
          "precision_at_k": 0.10512820512820513,
          "mean_winning_rank": 25.102564102564102,
          "draws": 156
        }
      ],
      "HierarchicalBayes": [
        {
          "brier": 0.09029576140415238,
          "log_loss": 0.3267463494497238,
          "ece": 0.016645419788226225,
          "avg_hits": 0.42948717948717946,
          "precision_at_k": 0.0858974358974359,
          "mean_winning_rank": 26.266666666666666,
          "draws": 156
        },
        {
          "brier": 0.09019580260906003,
          "log_loss": 0.3262078999112718,
          "ece": 0.014142018318460174,
          "avg_hits": 0.4935897435897436,
          "precision_at_k": 0.09871794871794873,
          "mean_winning_rank": 26.351282051282052,
          "draws": 156
        },
        {
          "brier": 0.09004281404036965,
          "log_loss": 0.3253025618671899,
          "ece": 0.0053486880769999245,
          "avg_hits": 0.5256410256410257,
          "precision_at_k": 0.10512820512820513,
          "mean_winning_rank": 25.102564102564102,
          "draws": 156
        }
      ],
      "DynamicState": [
        {
          "brier": 0.09008549932689733,
          "log_loss": 0.3255534720723418,
          "ece": 0.0076804658100123,
          "avg_hits": 0.48717948717948717,
          "precision_at_k": 0.09743589743589744,
          "mean_winning_rank": 25.861538461538462,
          "draws": 156
        },
        {
          "brier": 0.09002208589221712,
          "log_loss": 0.3251919085583386,
          "ece": 0.0036931158900113947,
          "avg_hits": 0.5128205128205128,
          "precision_at_k": 0.10256410256410256,
          "mean_winning_rank": 24.964102564102564,
          "draws": 156
        },
        {
          "brier": 0.08997579663640762,
          "log_loss": 0.3249479897032397,
          "ece": 0.0012988936777465084,
          "avg_hits": 0.5256410256410257,
          "precision_at_k": 0.10512820512820513,
          "mean_winning_rank": 24.714102564102564,
          "draws": 156
        }
      ],
      "Logistic_L2": [
        {
          "brier": 0.0900828021539019,
          "log_loss": 0.3255364006100499,
          "ece": 0.006323051660920948,
          "avg_hits": 0.46794871794871795,
          "precision_at_k": 0.09358974358974359,
          "mean_winning_rank": 25.82948717948718,
          "draws": 156
        },
        {
          "brier": 0.09004012069386573,
          "log_loss": 0.32529591905374805,
          "ece": 0.004476587659295463,
          "avg_hits": 0.4230769230769231,
          "precision_at_k": 0.08461538461538462,
          "mean_winning_rank": 25.655128205128204,
          "draws": 156
        },
        {
          "brier": 0.09002561435636326,
          "log_loss": 0.3252250998487792,
          "ece": 0.00197175340844808,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.07692307692307693,
          "mean_winning_rank": 25.793589743589745,
          "draws": 156
        }
      ],
      "ElasticNet": [
        {
          "brier": 0.0900088871746369,
          "log_loss": 0.3251323523859081,
          "ece": 0.0033547039425587677,
          "avg_hits": 0.46794871794871795,
          "precision_at_k": 0.09358974358974359,
          "mean_winning_rank": 26.075641025641026,
          "draws": 156
        },
        {
          "brier": 0.09064352697413662,
          "log_loss": 0.3288766627642705,
          "ece": 0.023869350855206875,
          "avg_hits": 0.5256410256410257,
          "precision_at_k": 0.10512820512820513,
          "mean_winning_rank": 25.624358974358973,
          "draws": 156
        },
        {
          "brier": 0.09,
          "log_loss": 0.3250829733914482,
          "ece": 2.7755575615628914e-17,
          "avg_hits": 0.47435897435897434,
          "precision_at_k": 0.09487179487179487,
          "mean_winning_rank": 24.705128205128204,
          "draws": 156
        }
      ],
      "GradientBoosting": [
        {
          "brier": 0.09022650816055969,
          "log_loss": 0.32619652845368424,
          "ece": 0.00895020181725339,
          "avg_hits": 0.4423076923076923,
          "precision_at_k": 0.08846153846153845,
          "mean_winning_rank": 26.21153846153846,
          "draws": 156
        },
        {
          "brier": 0.08999698822972091,
          "log_loss": 0.32506736320478247,
          "ece": 0.00011573850432551129,
          "avg_hits": 0.5,
          "precision_at_k": 0.1,
          "mean_winning_rank": 25.52179487179487,
          "draws": 156
        },
        {
          "brier": 0.0900304887180776,
          "log_loss": 0.3251498215578256,
          "ece": 0.00247918492691586,
          "avg_hits": 0.5064102564102564,
          "precision_at_k": 0.10128205128205128,
          "mean_winning_rank": 24.94871794871795,
          "draws": 156
        }
      ],
      "RandomForest": [
        {
          "brier": 0.0902537124322448,
          "log_loss": 0.32656452056541724,
          "ece": 0.013555649918683466,
          "avg_hits": 0.5064102564102564,
          "precision_at_k": 0.10128205128205128,
          "mean_winning_rank": 26.317948717948717,
          "draws": 156
        },
        {
          "brier": 0.09010891150987589,
          "log_loss": 0.32564597470995016,
          "ece": 0.006865841898918796,
          "avg_hits": 0.5,
          "precision_at_k": 0.1,
          "mean_winning_rank": 25.73205128205128,
          "draws": 156
        },
        {
          "brier": 0.09002112909081537,
          "log_loss": 0.32518212703005783,
          "ece": 0.004160422498876573,
          "avg_hits": 0.5192307692307693,
          "precision_at_k": 0.10384615384615385,
          "mean_winning_rank": 25.07051282051282,
          "draws": 156
        }
      ],
      "ExtraTrees": [
        {
          "brier": 0.09022414573828978,
          "log_loss": 0.3263204691740008,
          "ece": 0.01519463151147038,
          "avg_hits": 0.4551282051282051,
          "precision_at_k": 0.09102564102564102,
          "mean_winning_rank": 26.21923076923077,
          "draws": 156
        },
        {
          "brier": 0.09015391450292681,
          "log_loss": 0.32593435711961566,
          "ece": 0.009144955858767893,
          "avg_hits": 0.4551282051282051,
          "precision_at_k": 0.09102564102564102,
          "mean_winning_rank": 25.923076923076923,
          "draws": 156
        },
        {
          "brier": 0.09003480564448209,
          "log_loss": 0.325256956780953,
          "ece": 0.0062195622189080415,
          "avg_hits": 0.5512820512820513,
          "precision_at_k": 0.11025641025641027,
          "mean_winning_rank": 25.485897435897435,
          "draws": 156
        }
      ],
      "HistGradientBoosting": [
        {
          "brier": 0.09020170898018114,
          "log_loss": 0.3261057079485546,
          "ece": 0.008925731001397399,
          "avg_hits": 0.4423076923076923,
          "precision_at_k": 0.08846153846153845,
          "mean_winning_rank": 26.03974358974359,
          "draws": 156
        },
        {
          "brier": 0.09004494158106924,
          "log_loss": 0.3253592819763364,
          "ece": 0.005982702168360563,
          "avg_hits": 0.5,
          "precision_at_k": 0.1,
          "mean_winning_rank": 25.407692307692308,
          "draws": 156
        },
        {
          "brier": 0.09000631524367478,
          "log_loss": 0.3251190136288756,
          "ece": 0.002581486374737817,
          "avg_hits": 0.48717948717948717,
          "precision_at_k": 0.09743589743589744,
          "mean_winning_rank": 25.55897435897436,
          "draws": 156
        }
      ],
      "Bayesian_GLM_Laplace": [
        {
          "brier": 0.09000145961054022,
          "log_loss": 0.32509108391980684,
          "ece": 0.0033539092781472942,
          "avg_hits": 0.5,
          "precision_at_k": 0.1,
          "mean_winning_rank": 25.95769230769231,
          "draws": 156
        },
        {
          "brier": 0.09000089716675214,
          "log_loss": 0.325087949702219,
          "ece": 0.0006989201679007881,
          "avg_hits": 0.3717948717948718,
          "precision_at_k": 0.07435897435897436,
          "mean_winning_rank": 25.77948717948718,
          "draws": 156
        },
        {
          "brier": 0.08999996835869764,
          "log_loss": 0.3250827983084355,
          "ece": 0.000633362870015122,
          "avg_hits": 0.4935897435897436,
          "precision_at_k": 0.09871794871794873,
          "mean_winning_rank": 25.382051282051282,
          "draws": 156
        }
      ]
    },
    "consensus_ml_hyperparameters": {
      "Logistic_L2": "C0.1",
      "ElasticNet": "a0.001_l0.5",
      "GradientBoosting": "d1_lr0.03",
      "RandomForest": "leaf100",
      "ExtraTrees": "leaf100",
      "HistGradientBoosting": "leaf80_l5",
      "Bayesian_GLM_Laplace": "ridge1"
    },
    "consensus_statistical_hyperparameters": {
      "FullFrequency": 80,
      "RollingFrequency": 200,
      "EWMA": 120,
      "BetaBinomial": 100,
      "HierarchicalBayes": 150,
      "DynamicState": 0.99
    },
    "calibrators": {
      "Uniform": {
        "coef": 1.0,
        "intercept": 0.0
      },
      "FullFrequency": {
        "coef": -0.24691813226370352,
        "intercept": -2.741117019825854
      },
      "RollingFrequency": {
        "coef": -0.01817566540378778,
        "intercept": -2.237361624080489
      },
      "EWMA": {
        "coef": -0.06667806260264951,
        "intercept": -2.344842039705754
      },
      "BetaBinomial": {
        "coef": -0.2532144199717325,
        "intercept": -2.754872912669734
      },
      "HierarchicalBayes": {
        "coef": -0.2327783408040301,
        "intercept": -2.710654542762443
      },
      "DynamicState": {
        "coef": 0.13564635794108773,
        "intercept": -1.8988701158051626
      },
      "Logistic_L2": {
        "coef": -0.2866316215758232,
        "intercept": -2.8273962128519874
      },
      "ElasticNet": {
        "coef": -0.0271961910355484,
        "intercept": -2.257276972537696
      },
      "GradientBoosting": {
        "coef": -0.10795325796451896,
        "intercept": -2.4347967297595496
      },
      "RandomForest": {
        "coef": -0.10729227497331817,
        "intercept": -2.433568531497605
      },
      "ExtraTrees": {
        "coef": -0.2348796881665958,
        "intercept": -2.714470728821012
      },
      "HistGradientBoosting": {
        "coef": -0.11816221709914487,
        "intercept": -2.457212106701266
      },
      "Bayesian_GLM_Laplace": {
        "coef": 0.8278781548799017,
        "intercept": -0.37744248675039316
      }
    },
    "calibration_diagnostics": {
      "FullFrequency": {
        "coef": -0.24691813226370352,
        "intercept": -2.741117019825854,
        "crossfit_brier": 0.09007937700484486,
        "crossfit_log_loss": 0.32552640132025257
      },
      "RollingFrequency": {
        "coef": -0.01817566540378778,
        "intercept": -2.237361624080489,
        "crossfit_brier": 0.09022072271627608,
        "crossfit_log_loss": 0.32632253309224396
      },
      "EWMA": {
        "coef": -0.06667806260264951,
        "intercept": -2.344842039705754,
        "crossfit_brier": 0.09017020173347202,
        "crossfit_log_loss": 0.32603760611172145
      },
      "BetaBinomial": {
        "coef": -0.2532144199717325,
        "intercept": -2.754872912669734,
        "crossfit_brier": 0.0900746543570789,
        "crossfit_log_loss": 0.3254995654728711
      },
      "HierarchicalBayes": {
        "coef": -0.2327783408040301,
        "intercept": -2.710654542762443,
        "crossfit_brier": 0.09010087635915201,
        "crossfit_log_loss": 0.3256496154551833
      },
      "DynamicState": {
        "coef": 0.13564635794108773,
        "intercept": -1.8988701158051626,
        "crossfit_brier": 0.09003258623884085,
        "crossfit_log_loss": 0.32526242020437895
      },
      "Logistic_L2": {
        "coef": -0.2866316215758232,
        "intercept": -2.8273962128519874,
        "crossfit_brier": 0.0900255316312282,
        "crossfit_log_loss": 0.3252225037746237
      },
      "ElasticNet": {
        "coef": -0.0271961910355484,
        "intercept": -2.257276972537696,
        "crossfit_brier": 0.09000291304432789,
        "crossfit_log_loss": 0.3250992479070353
      },
      "GradientBoosting": {
        "coef": -0.10795325796451896,
        "intercept": -2.4347967297595496,
        "crossfit_brier": 0.09008078656462304,
        "crossfit_log_loss": 0.32548289481847337
      },
      "RandomForest": {
        "coef": -0.10729227497331817,
        "intercept": -2.433568531497605,
        "crossfit_brier": 0.0900932529868964,
        "crossfit_log_loss": 0.3256235286296265
      },
      "ExtraTrees": {
        "coef": -0.2348796881665958,
        "intercept": -2.714470728821012,
        "crossfit_brier": 0.09007743612087633,
        "crossfit_log_loss": 0.32550932929409865
      },
      "HistGradientBoosting": {
        "coef": -0.11816221709914487,
        "intercept": -2.457212106701266,
        "crossfit_brier": 0.09007125280071755,
        "crossfit_log_loss": 0.3254469496530924
      },
      "Bayesian_GLM_Laplace": {
        "coef": 0.8278781548799017,
        "intercept": -0.37744248675039316,
        "crossfit_brier": 0.0900004817970566,
        "crossfit_log_loss": 0.3250856505680599
      }
    },
    "production_weights": {
      "Bayesian_GLM_Laplace": 0.0,
      "BetaBinomial": 0.0,
      "DynamicState": 0.0,
      "EWMA": 0.0,
      "ElasticNet": 0.0,
      "ExtraTrees": 0.0,
      "FullFrequency": 0.0,
      "GradientBoosting": 0.0,
      "HierarchicalBayes": 0.0,
      "HistGradientBoosting": 0.0,
      "Logistic_L2": 0.0,
      "RandomForest": 0.0,
      "RollingFrequency": 0.0,
      "Uniform": 1.0
    },
    "research_weights": {
      "Bayesian_GLM_Laplace": 0.09748808165735762,
      "BetaBinomial": 0.028855242712127874,
      "DynamicState": 0.05755728974307657,
      "EWMA": 0.006013552477701679,
      "ElasticNet": 0.09367437013607076,
      "ExtraTrees": 0.02756737346241967,
      "FullFrequency": 0.02670300396886526,
      "GradientBoosting": 0.026092296632763506,
      "HierarchicalBayes": 0.018763140849930682,
      "HistGradientBoosting": 0.030512104426337585,
      "Logistic_L2": 0.06462312211040279,
      "RandomForest": 0.021264123381673727,
      "RollingFrequency": 0.002624222519468009,
      "Uniform": 0.4982620759218043
    },
    "weight_diagnostics": {
      "development_brier": {
        "Bayesian_GLM_Laplace": 0.0900004817970566,
        "BetaBinomial": 0.0900746543570789,
        "DynamicState": 0.09003258623884085,
        "EWMA": 0.09017020173347202,
        "ElasticNet": 0.09000291304432789,
        "ExtraTrees": 0.09007743612087633,
        "FullFrequency": 0.09007937700484486,
        "GradientBoosting": 0.09008078656462304,
        "HierarchicalBayes": 0.09010087635915201,
        "HistGradientBoosting": 0.09007125280071755,
        "Logistic_L2": 0.0900255316312282,
        "RandomForest": 0.0900932529868964,
        "RollingFrequency": 0.09022072271627608,
        "Uniform": 0.09
      },
      "fold_brier": {
        "Bayesian_GLM_Laplace": [
          0.09000145961054024,
          0.08999998473187235,
          0.09000000104875726
        ],
        "BetaBinomial": [
          0.09021648630279235,
          0.08997868302264928,
          0.09002879374579509
        ],
        "DynamicState": [
          0.09008549932689736,
          0.0900074542596434,
          0.09000480512998184
        ],
        "EWMA": [
          0.09044071556957171,
          0.08998108351813806,
          0.09008880611270631
        ],
        "ElasticNet": [
          0.09000888717463688,
          0.08999985195834677,
          0.09
        ],
        "ExtraTrees": [
          0.09022414573828978,
          0.0899835646932834,
          0.09002459793105579
        ],
        "FullFrequency": [
          0.09023065901928617,
          0.08997839701486023,
          0.09002907498038819
        ],
        "GradientBoosting": [
          0.09022650816055969,
          0.09000215474666844,
          0.09001369678664103
        ],
        "HierarchicalBayes": [
          0.0902957614041524,
          0.08997757622082848,
          0.09002929145247525
        ],
        "HistGradientBoosting": [
          0.09020170898018114,
          0.09001029166368865,
          0.0900017577582828
        ],
        "Logistic_L2": [
          0.0900828021539019,
          0.08999655307561259,
          0.08999723966417016
        ],
        "RandomForest": [
          0.0902537124322448,
          0.09000268342627267,
          0.09002336310217171
        ],
        "RollingFrequency": [
          0.09059285423571138,
          0.09000901674004277,
          0.09006029717307405
        ],
        "Uniform": [
          0.09,
          0.09,
          0.09
        ]
      },
      "eligible_models": []
    },
    "frozen_holdout_metrics": {
      "Uniform": {
        "brier": 0.09,
        "log_loss": 0.3250829733914482,
        "ece": 0.0,
        "avg_hits": 0.5076923076923077,
        "precision_at_k": 0.10153846153846154,
        "mean_winning_rank": 25.18769230769231,
        "draws": 195
      },
      "FullFrequency": {
        "brier": 0.08999768930122551,
        "log_loss": 0.3250699236742418,
        "ece": 0.0027713818772761934,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "RollingFrequency": {
        "brier": 0.08999655109794015,
        "log_loss": 0.32506382452406146,
        "ece": 0.0027155490804294477,
        "avg_hits": 0.517948717948718,
        "precision_at_k": 0.1035897435897436,
        "mean_winning_rank": 24.93128205128205,
        "draws": 195
      },
      "EWMA": {
        "brier": 0.08999327366001844,
        "log_loss": 0.32504563569520506,
        "ece": 0.004865595496053197,
        "avg_hits": 0.5333333333333333,
        "precision_at_k": 0.10666666666666666,
        "mean_winning_rank": 25.013333333333332,
        "draws": 195
      },
      "BetaBinomial": {
        "brier": 0.08999769292767963,
        "log_loss": 0.3250699419641643,
        "ece": 0.0027780721628605743,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "HierarchicalBayes": {
        "brier": 0.08999774974400192,
        "log_loss": 0.32507024592022227,
        "ece": 0.0027683094152730855,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "DynamicState": {
        "brier": 0.09000405432355867,
        "log_loss": 0.32510530513398417,
        "ece": 0.00045566849350735033,
        "avg_hits": 0.4666666666666667,
        "precision_at_k": 0.09333333333333334,
        "mean_winning_rank": 25.747692307692308,
        "draws": 195
      },
      "Logistic_L2": {
        "brier": 0.09000510846577126,
        "log_loss": 0.3251115033807289,
        "ece": 0.0009332174455191979,
        "avg_hits": 0.48205128205128206,
        "precision_at_k": 0.09641025641025641,
        "mean_winning_rank": 25.851282051282052,
        "draws": 195
      },
      "ElasticNet": {
        "brier": 0.09,
        "log_loss": 0.3250829733914482,
        "ece": 2.7755575615628914e-17,
        "avg_hits": 0.5076923076923077,
        "precision_at_k": 0.10153846153846154,
        "mean_winning_rank": 25.18769230769231,
        "draws": 195
      },
      "GradientBoosting": {
        "brier": 0.0900006561141188,
        "log_loss": 0.32508784878993296,
        "ece": 0.0019168353255509395,
        "avg_hits": 0.47692307692307695,
        "precision_at_k": 0.09538461538461539,
        "mean_winning_rank": 25.620512820512822,
        "draws": 195
      },
      "RandomForest": {
        "brier": 0.08999844574706259,
        "log_loss": 0.325074309783135,
        "ece": 0.002790108560411536,
        "avg_hits": 0.5282051282051282,
        "precision_at_k": 0.10564102564102565,
        "mean_winning_rank": 25.54871794871795,
        "draws": 195
      },
      "ExtraTrees": {
        "brier": 0.09000045590036079,
        "log_loss": 0.32508543777428905,
        "ece": 0.00392132166191452,
        "avg_hits": 0.517948717948718,
        "precision_at_k": 0.1035897435897436,
        "mean_winning_rank": 25.491282051282052,
        "draws": 195
      },
      "HistGradientBoosting": {
        "brier": 0.08999843745148933,
        "log_loss": 0.3250741644389013,
        "ece": 0.0015354575534177511,
        "avg_hits": 0.5384615384615384,
        "precision_at_k": 0.10769230769230768,
        "mean_winning_rank": 25.617435897435897,
        "draws": 195
      },
      "Bayesian_GLM_Laplace": {
        "brier": 0.08999941370707587,
        "log_loss": 0.3250797184246306,
        "ece": 0.0007525712466899381,
        "avg_hits": 0.558974358974359,
        "precision_at_k": 0.1117948717948718,
        "mean_winning_rank": 25.134358974358975,
        "draws": 195
      },
      "ProductionEnsemble": {
        "brier": 0.09,
        "log_loss": 0.3250829733914482,
        "ece": 0.0,
        "avg_hits": 0.5076923076923077,
        "precision_at_k": 0.10153846153846154,
        "mean_winning_rank": 25.18769230769231,
        "draws": 195
      }
    },
    "prequential_holdout_metrics": {
      "Uniform": {
        "brier": 0.09,
        "log_loss": 0.3250829733914482,
        "ece": 0.0,
        "avg_hits": 0.5076923076923077,
        "precision_at_k": 0.10153846153846154,
        "mean_winning_rank": 25.18769230769231,
        "draws": 195
      },
      "FullFrequency": {
        "brier": 0.08999768930122551,
        "log_loss": 0.3250699236742418,
        "ece": 0.0027713818772761934,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "RollingFrequency": {
        "brier": 0.08999655109794015,
        "log_loss": 0.32506382452406146,
        "ece": 0.0027155490804294477,
        "avg_hits": 0.517948717948718,
        "precision_at_k": 0.1035897435897436,
        "mean_winning_rank": 24.93128205128205,
        "draws": 195
      },
      "EWMA": {
        "brier": 0.08999327366001844,
        "log_loss": 0.32504563569520506,
        "ece": 0.004865595496053197,
        "avg_hits": 0.5333333333333333,
        "precision_at_k": 0.10666666666666666,
        "mean_winning_rank": 25.013333333333332,
        "draws": 195
      },
      "BetaBinomial": {
        "brier": 0.08999769292767963,
        "log_loss": 0.3250699419641643,
        "ece": 0.0027780721628605743,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "HierarchicalBayes": {
        "brier": 0.08999774974400192,
        "log_loss": 0.32507024592022227,
        "ece": 0.0027683094152730855,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.40102564102564,
        "draws": 195
      },
      "DynamicState": {
        "brier": 0.09000405432355867,
        "log_loss": 0.32510530513398417,
        "ece": 0.00045566849350735033,
        "avg_hits": 0.4666666666666667,
        "precision_at_k": 0.09333333333333334,
        "mean_winning_rank": 25.747692307692308,
        "draws": 195
      },
      "Logistic_L2": {
        "brier": 0.09000221784220669,
        "log_loss": 0.32509541774214223,
        "ece": 0.0021534499214122243,
        "avg_hits": 0.5538461538461539,
        "precision_at_k": 0.11076923076923077,
        "mean_winning_rank": 25.603076923076923,
        "draws": 195
      },
      "ElasticNet": {
        "brier": 0.09000023901695556,
        "log_loss": 0.3250843011901575,
        "ece": 0.0014729192792138116,
        "avg_hits": 0.47692307692307695,
        "precision_at_k": 0.09538461538461539,
        "mean_winning_rank": 25.324102564102564,
        "draws": 195
      },
      "GradientBoosting": {
        "brier": 0.0899950931832066,
        "log_loss": 0.32505623685625457,
        "ece": 0.0046058468601928235,
        "avg_hits": 0.5128205128205128,
        "precision_at_k": 0.10256410256410256,
        "mean_winning_rank": 24.87794871794872,
        "draws": 195
      },
      "RandomForest": {
        "brier": 0.0899994818407156,
        "log_loss": 0.3250798432083551,
        "ece": 0.0002802661311959672,
        "avg_hits": 0.48717948717948717,
        "precision_at_k": 0.09743589743589744,
        "mean_winning_rank": 25.395897435897435,
        "draws": 195
      },
      "ExtraTrees": {
        "brier": 0.09000331772834126,
        "log_loss": 0.3251009055164493,
        "ece": 0.004052298689711336,
        "avg_hits": 0.4666666666666667,
        "precision_at_k": 0.09333333333333334,
        "mean_winning_rank": 25.483076923076922,
        "draws": 195
      },
      "HistGradientBoosting": {
        "brier": 0.08999556637430918,
        "log_loss": 0.32505823172534115,
        "ece": 0.00018053276921146748,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.26051282051282,
        "draws": 195
      },
      "Bayesian_GLM_Laplace": {
        "brier": 0.08999975987986962,
        "log_loss": 0.32508164114268695,
        "ece": 0.0012441952379535228,
        "avg_hits": 0.5230769230769231,
        "precision_at_k": 0.10461538461538462,
        "mean_winning_rank": 25.305641025641027,
        "draws": 195
      },
      "ProductionEnsemble": {
        "brier": 0.09,
        "log_loss": 0.3250829733914482,
        "ece": 0.0,
        "avg_hits": 0.5076923076923077,
        "precision_at_k": 0.10153846153846154,
        "mean_winning_rank": 25.18769230769231,
        "draws": 195
      }
    },
    "reality_check": {
      "observed_brier_improvement": {
        "FullFrequency": 2.3106987744880847e-06,
        "RollingFrequency": 3.4489020598466036e-06,
        "EWMA": 6.726339981555363e-06,
        "BetaBinomial": 2.307072320364978e-06,
        "HierarchicalBayes": 2.2502559980791537e-06,
        "DynamicState": -4.054323558669304e-06,
        "Logistic_L2": -2.2178422066920778e-06,
        "ElasticNet": -2.390169555610555e-07,
        "GradientBoosting": 4.906816793395774e-06,
        "RandomForest": 5.181592843961358e-07,
        "ExtraTrees": -3.3177283412649805e-06,
        "HistGradientBoosting": 4.433625690816734e-06,
        "Bayesian_GLM_Laplace": 2.401201303764422e-07,
        "ProductionEnsemble": 0.0
      },
      "maxT_adjusted_p": {
        "FullFrequency": 0.9460215913634547,
        "RollingFrequency": 0.9068372650939625,
        "EWMA": 0.719312275089964,
        "BetaBinomial": 0.9460215913634547,
        "HierarchicalBayes": 0.9464214314274291,
        "DynamicState": 1.0,
        "Logistic_L2": 1.0,
        "ElasticNet": 1.0,
        "GradientBoosting": 0.8344662135145942,
        "RandomForest": 0.9976009596161536,
        "ExtraTrees": 1.0,
        "HistGradientBoosting": 0.8612554978008796,
        "Bayesian_GLM_Laplace": 0.9996001599360256,
        "ProductionEnsemble": 1.0
      },
      "best_model": "EWMA",
      "best_improvement": 6.726339981555363e-06,
      "best_adjusted_p": 0.719312275089964
    },
    "block_bootstrap": {
      "mean": 0.0,
      "ci_low": 0.0,
      "ci_high": 0.0,
      "prob_positive": 0.0
    },
    "period_brier_improvements": [
      0.0,
      0.0,
      0.0
    ],
    "acceptance_criteria": {
      "frozen_brier_better": false,
      "prequential_brier_better": false,
      "frozen_log_loss_better": false,
      "prequential_log_loss_better": false,
      "positive_all_three_periods": false,
      "maxT_adjusted_p_below_0_05": false,
      "block_bootstrap_ci_positive": false,
      "nonuniform_weight_positive": false
    },
    "status": "Uniform mode"
  },
  "euro_pool": {
    "dev_draws": 780,
    "holdout_draws": 195,
    "selected_features": [
      "number_norm",
      "number_sin",
      "number_cos",
      "is_odd",
      "is_high",
      "decade_norm",
      "pair_prev_score",
      "triple_prev_score"
    ],
    "feature_screen": [
      {
        "group": "identity",
        "selection_votes": 3,
        "runs": 3,
        "mean_permutation_delta": 0.0,
        "median_permutation_p": 0.0,
        "keep": true
      },
      {
        "group": "frequency",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -8.883622861005989e-05,
        "median_permutation_p": 0.7,
        "keep": false
      },
      {
        "group": "ewma",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -0.0001525624044770086,
        "median_permutation_p": 0.825,
        "keep": false
      },
      {
        "group": "gap",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 0.0001492094873598017,
        "median_permutation_p": 0.25,
        "keep": false
      },
      {
        "group": "trend",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -6.226364026275896e-05,
        "median_permutation_p": 0.675,
        "keep": false
      },
      {
        "group": "repeat_transition",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": -6.0809967952055145e-05,
        "median_permutation_p": 0.65,
        "keep": false
      },
      {
        "group": "pair_triple",
        "selection_votes": 3,
        "runs": 3,
        "mean_permutation_delta": 0.0005962583096905589,
        "median_permutation_p": 0.05,
        "keep": true
      },
      {
        "group": "position",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 2.7328038536915842e-05,
        "median_permutation_p": 0.2,
        "keep": false
      },
      {
        "group": "draw_composition",
        "selection_votes": 1,
        "runs": 3,
        "mean_permutation_delta": 0.0002461728605005797,
        "median_permutation_p": 0.225,
        "keep": false
      },
      {
        "group": "rule_calendar",
        "selection_votes": 0,
        "runs": 3,
        "mean_permutation_delta": 0.0,
        "median_permutation_p": 1.0,
        "keep": false
      }
    ],
    "nested_fold_metrics": {
      "Uniform": [
        {
          "brier": 0.16000000000000006,
          "log_loss": 0.5004024235381879,
          "ece": 0.0,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 5.766025641025641,
          "draws": 156
        },
        {
          "brier": 0.1453514739229025,
          "log_loss": 0.46581872356177906,
          "ece": 8.496604780294566e-18,
          "avg_hits": 0.2692307692307692,
          "precision_at_k": 0.1346153846153846,
          "mean_winning_rank": 6.368589743589744,
          "draws": 156
        },
        {
          "brier": 0.1388888888888889,
          "log_loss": 0.4505612088663047,
          "ece": 2.7755575615628914e-17,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 6.298076923076923,
          "draws": 156
        }
      ],
      "FullFrequency": [
        {
          "brier": 0.1609457607256503,
          "log_loss": 0.5034314040134142,
          "ece": 0.030598756757162383,
          "avg_hits": 0.36538461538461536,
          "precision_at_k": 0.18269230769230768,
          "mean_winning_rank": 5.67948717948718,
          "draws": 156
        },
        {
          "brier": 0.14530730684739876,
          "log_loss": 0.4657948181464143,
          "ece": 0.0030589470987547355,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 6.019230769230769,
          "draws": 156
        },
        {
          "brier": 0.1392882043610829,
          "log_loss": 0.45203351094745203,
          "ece": 0.0,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 6.512820512820513,
          "draws": 156
        }
      ],
      "RollingFrequency": [
        {
          "brier": 0.1609963688377194,
          "log_loss": 0.503633196396663,
          "ece": 0.02195382896711024,
          "avg_hits": 0.3141025641025641,
          "precision_at_k": 0.15705128205128205,
          "mean_winning_rank": 5.708333333333333,
          "draws": 156
        },
        {
          "brier": 0.14655011217030292,
          "log_loss": 0.4702021651033921,
          "ece": 0.012874973456951985,
          "avg_hits": 0.34615384615384615,
          "precision_at_k": 0.17307692307692307,
          "mean_winning_rank": 6.198717948717949,
          "draws": 156
        },
        {
          "brier": 0.13949473916780916,
          "log_loss": 0.4528109770033645,
          "ece": 0.006432708129958408,
          "avg_hits": 0.36538461538461536,
          "precision_at_k": 0.18269230769230768,
          "mean_winning_rank": 6.461538461538462,
          "draws": 156
        }
      ],
      "EWMA": [
        {
          "brier": 0.16111289798559453,
          "log_loss": 0.5039806416183691,
          "ece": 0.027176073532305448,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 5.67948717948718,
          "draws": 156
        },
        {
          "brier": 0.14597262866632207,
          "log_loss": 0.46823911964070625,
          "ece": 0.002661723733548022,
          "avg_hits": 0.2948717948717949,
          "precision_at_k": 0.14743589743589744,
          "mean_winning_rank": 6.128205128205129,
          "draws": 156
        },
        {
          "brier": 0.13935162163333262,
          "log_loss": 0.4522934386347693,
          "ece": 0.00620204470922109,
          "avg_hits": 0.34615384615384615,
          "precision_at_k": 0.17307692307692307,
          "mean_winning_rank": 6.464743589743589,
          "draws": 156
        }
      ],
      "BetaBinomial": [
        {
          "brier": 0.1608901695817998,
          "log_loss": 0.5032458544468831,
          "ece": 0.028968350146832914,
          "avg_hits": 0.36538461538461536,
          "precision_at_k": 0.18269230769230768,
          "mean_winning_rank": 5.6826923076923075,
          "draws": 156
        },
        {
          "brier": 0.1452920824019863,
          "log_loss": 0.4657269660808058,
          "ece": 0.00319654595581023,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 6.0256410256410255,
          "draws": 156
        },
        {
          "brier": 0.1392672009866848,
          "log_loss": 0.451952934384139,
          "ece": 0.0,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 6.5256410256410255,
          "draws": 156
        }
      ],
      "HierarchicalBayes": [
        {
          "brier": 0.1613006242568201,
          "log_loss": 0.5045910298796565,
          "ece": 0.028890658725261698,
          "avg_hits": 0.34615384615384615,
          "precision_at_k": 0.17307692307692307,
          "mean_winning_rank": 5.753205128205129,
          "draws": 156
        },
        {
          "brier": 0.14547700389815632,
          "log_loss": 0.4663792829842373,
          "ece": 0.002140643581519924,
          "avg_hits": 0.41025641025641024,
          "precision_at_k": 0.20512820512820512,
          "mean_winning_rank": 5.951923076923077,
          "draws": 156
        },
        {
          "brier": 0.1392960439289351,
          "log_loss": 0.4521407909361989,
          "ece": 0.00220156236547484,
          "avg_hits": 0.4166666666666667,
          "precision_at_k": 0.20833333333333334,
          "mean_winning_rank": 6.451923076923077,
          "draws": 156
        }
      ],
      "DynamicState": [
        {
          "brier": 0.16027867193193265,
          "log_loss": 0.5012653695583563,
          "ece": 0.012009156023287833,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 5.621794871794871,
          "draws": 156
        },
        {
          "brier": 0.1454965108782696,
          "log_loss": 0.4662544732267061,
          "ece": 0.009465573204703018,
          "avg_hits": 0.2948717948717949,
          "precision_at_k": 0.14743589743589744,
          "mean_winning_rank": 6.230769230769231,
          "draws": 156
        },
        {
          "brier": 0.13890509959407688,
          "log_loss": 0.45063785602718537,
          "ece": 0.00041266808522267927,
          "avg_hits": 0.3717948717948718,
          "precision_at_k": 0.1858974358974359,
          "mean_winning_rank": 6.512820512820513,
          "draws": 156
        }
      ],
      "Logistic_L2": [
        {
          "brier": 0.1600302193204829,
          "log_loss": 0.5004379723054052,
          "ece": 0.004455413554946848,
          "avg_hits": 0.34615384615384615,
          "precision_at_k": 0.17307692307692307,
          "mean_winning_rank": 5.435897435897436,
          "draws": 156
        },
        {
          "brier": 0.1453535645400462,
          "log_loss": 0.465783424385503,
          "ece": 0.0019220695510940205,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 6.012820512820513,
          "draws": 156
        },
        {
          "brier": 0.1389290757476512,
          "log_loss": 0.45075572540212866,
          "ece": 0.00020712097844938814,
          "avg_hits": 0.391025641025641,
          "precision_at_k": 0.1955128205128205,
          "mean_winning_rank": 6.346153846153846,
          "draws": 156
        }
      ],
      "ElasticNet": [
        {
          "brier": 0.15969032887583168,
          "log_loss": 0.4994043683894627,
          "ece": 0.007703187656428894,
          "avg_hits": 0.46794871794871795,
          "precision_at_k": 0.23397435897435898,
          "mean_winning_rank": 5.237179487179487,
          "draws": 156
        },
        {
          "brier": 0.14532670503996828,
          "log_loss": 0.46572253500202065,
          "ece": 0.0009210584967404359,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 5.980769230769231,
          "draws": 156
        },
        {
          "brier": 0.13892961332532425,
          "log_loss": 0.4507674109741243,
          "ece": 0.0,
          "avg_hits": 0.3782051282051282,
          "precision_at_k": 0.1891025641025641,
          "mean_winning_rank": 6.336538461538462,
          "draws": 156
        }
      ],
      "GradientBoosting": [
        {
          "brier": 0.16083811026215297,
          "log_loss": 0.5031063474243138,
          "ece": 0.031173654385763104,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 5.55448717948718,
          "draws": 156
        },
        {
          "brier": 0.14564497047273395,
          "log_loss": 0.46672414506085663,
          "ece": 0.0018124986505862343,
          "avg_hits": 0.3782051282051282,
          "precision_at_k": 0.1891025641025641,
          "mean_winning_rank": 6.201923076923077,
          "draws": 156
        },
        {
          "brier": 0.1393904233279176,
          "log_loss": 0.45267719476773516,
          "ece": 0.0032552724380367987,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 6.42948717948718,
          "draws": 156
        }
      ],
      "RandomForest": [
        {
          "brier": 0.16252518758173526,
          "log_loss": 0.5088995587022546,
          "ece": 0.043405606395430604,
          "avg_hits": 0.38461538461538464,
          "precision_at_k": 0.19230769230769232,
          "mean_winning_rank": 5.544871794871795,
          "draws": 156
        },
        {
          "brier": 0.14600630725184258,
          "log_loss": 0.46814689755856725,
          "ece": 0.0005437453848016918,
          "avg_hits": 0.2948717948717949,
          "precision_at_k": 0.14743589743589744,
          "mean_winning_rank": 6.342948717948718,
          "draws": 156
        },
        {
          "brier": 0.13883562135511157,
          "log_loss": 0.4504454440456616,
          "ece": 0.0018393869999783164,
          "avg_hits": 0.4166666666666667,
          "precision_at_k": 0.20833333333333334,
          "mean_winning_rank": 6.262820512820513,
          "draws": 156
        }
      ],
      "ExtraTrees": [
        {
          "brier": 0.1610402488378293,
          "log_loss": 0.5036626066513252,
          "ece": 0.02966118677964763,
          "avg_hits": 0.358974358974359,
          "precision_at_k": 0.1794871794871795,
          "mean_winning_rank": 5.737179487179487,
          "draws": 156
        },
        {
          "brier": 0.1455606816886747,
          "log_loss": 0.4665587722808339,
          "ece": 0.004640321026974726,
          "avg_hits": 0.3141025641025641,
          "precision_at_k": 0.15705128205128205,
          "mean_winning_rank": 6.198717948717949,
          "draws": 156
        },
        {
          "brier": 0.13900905655607662,
          "log_loss": 0.4512192556263639,
          "ece": 0.0,
          "avg_hits": 0.4230769230769231,
          "precision_at_k": 0.21153846153846154,
          "mean_winning_rank": 6.233974358974359,
          "draws": 156
        }
      ],
      "HistGradientBoosting": [
        {
          "brier": 0.16236300549605784,
          "log_loss": 0.508008320149565,
          "ece": 0.029836463552248192,
          "avg_hits": 0.3333333333333333,
          "precision_at_k": 0.16666666666666666,
          "mean_winning_rank": 5.42948717948718,
          "draws": 156
        },
        {
          "brier": 0.1468290514065972,
          "log_loss": 0.4712230832321806,
          "ece": 0.018469283720417146,
          "avg_hits": 0.3525641025641026,
          "precision_at_k": 0.1762820512820513,
          "mean_winning_rank": 6.092948717948718,
          "draws": 156
        },
        {
          "brier": 0.13970804706992876,
          "log_loss": 0.4543347882965087,
          "ece": 0.013993791560327408,
          "avg_hits": 0.34615384615384615,
          "precision_at_k": 0.17307692307692307,
          "mean_winning_rank": 6.362179487179487,
          "draws": 156
        }
      ],
      "Bayesian_GLM_Laplace": [
        {
          "brier": 0.15999651875244467,
          "log_loss": 0.5003913775514995,
          "ece": 0.0010465515364696826,
          "avg_hits": 0.4166666666666667,
          "precision_at_k": 0.20833333333333334,
          "mean_winning_rank": 5.451923076923077,
          "draws": 156
        },
        {
          "brier": 0.1453402222827803,
          "log_loss": 0.4657830407939875,
          "ece": 0.0015826874844835472,
          "avg_hits": 0.3333333333333333,
          "precision_at_k": 0.16666666666666666,
          "mean_winning_rank": 6.112179487179487,
          "draws": 156
        },
        {
          "brier": 0.13887954332116564,
          "log_loss": 0.45052763141068053,
          "ece": 0.0,
          "avg_hits": 0.3525641025641026,
          "precision_at_k": 0.1762820512820513,
          "mean_winning_rank": 6.288461538461538,
          "draws": 156
        }
      ]
    },
    "consensus_ml_hyperparameters": {
      "Logistic_L2": "C0.1",
      "ElasticNet": "a0.001_l0.5",
      "GradientBoosting": "d2_lr0.03",
      "RandomForest": "leaf100",
      "ExtraTrees": "leaf50",
      "HistGradientBoosting": "leaf80_l5",
      "Bayesian_GLM_Laplace": "ridge1"
    },
    "consensus_statistical_hyperparameters": {
      "FullFrequency": 80,
      "RollingFrequency": 200,
      "EWMA": 120,
      "BetaBinomial": 100,
      "HierarchicalBayes": 150,
      "DynamicState": 0.99
    },
    "calibrators": {
      "Uniform": {
        "coef": 1.0,
        "intercept": 0.0
      },
      "FullFrequency": {
        "coef": 0.2873542420392208,
        "intercept": -1.0783367300091355
      },
      "RollingFrequency": {
        "coef": 0.10287498869192323,
        "intercept": -1.3582209096560987
      },
      "EWMA": {
        "coef": 0.12503775711387413,
        "intercept": -1.3248080737481054
      },
      "BetaBinomial": {
        "coef": 0.30299067377596944,
        "intercept": -1.0547850661193385
      },
      "HierarchicalBayes": {
        "coef": 0.21636558714309348,
        "intercept": -1.1857537041248005
      },
      "DynamicState": {
        "coef": 0.4917130474845221,
        "intercept": -0.7686866468917668
      },
      "Logistic_L2": {
        "coef": 0.5868779574249486,
        "intercept": -0.624356221751686
      },
      "ElasticNet": {
        "coef": 0.633786970770427,
        "intercept": -0.5528482418462521
      },
      "GradientBoosting": {
        "coef": 0.2476326336309513,
        "intercept": -1.138151186147632
      },
      "RandomForest": {
        "coef": 0.13356671494520544,
        "intercept": -1.3112702874365896
      },
      "ExtraTrees": {
        "coef": 0.27106745627609485,
        "intercept": -1.103508244352468
      },
      "HistGradientBoosting": {
        "coef": 0.14992135017419844,
        "intercept": -1.2844521938461804
      },
      "Bayesian_GLM_Laplace": {
        "coef": 0.6972771574814457,
        "intercept": -0.4576302306208956
      }
    },
    "calibration_diagnostics": {
      "FullFrequency": {
        "coef": 0.2873542420392208,
        "intercept": -1.0783367300091355,
        "crossfit_brier": 0.1477759092380332,
        "crossfit_log_loss": 0.4718569239230232
      },
      "RollingFrequency": {
        "coef": 0.10287498869192323,
        "intercept": -1.3582209096560987,
        "crossfit_brier": 0.147721283257301,
        "crossfit_log_loss": 0.4716667342134702
      },
      "EWMA": {
        "coef": 0.12503775711387413,
        "intercept": -1.3248080737481054,
        "crossfit_brier": 0.14777306624667025,
        "crossfit_log_loss": 0.4718331566859645
      },
      "BetaBinomial": {
        "coef": 0.30299067377596944,
        "intercept": -1.0547850661193385,
        "crossfit_brier": 0.14775764845627365,
        "crossfit_log_loss": 0.47179607022401154
      },
      "HierarchicalBayes": {
        "coef": 0.21636558714309348,
        "intercept": -1.1857537041248005,
        "crossfit_brier": 0.14789789677629223,
        "crossfit_log_loss": 0.4722530595928453
      },
      "DynamicState": {
        "coef": 0.4917130474845221,
        "intercept": -0.7686866468917668,
        "crossfit_brier": 0.14749757147298315,
        "crossfit_log_loss": 0.47094200592338425
      },
      "Logistic_L2": {
        "coef": 0.5868779574249486,
        "intercept": -0.624356221751686,
        "crossfit_brier": 0.1474160481843143,
        "crossfit_log_loss": 0.47067121062557327
      },
      "ElasticNet": {
        "coef": 0.633786970770427,
        "intercept": -0.5528482418462521,
        "crossfit_brier": 0.14727884525089852,
        "crossfit_log_loss": 0.4702472815944984
      },
      "GradientBoosting": {
        "coef": 0.2476326336309513,
        "intercept": -1.138151186147632,
        "crossfit_brier": 0.14769475068004984,
        "crossfit_log_loss": 0.4715994561614574
      },
      "RandomForest": {
        "coef": 0.13356671494520544,
        "intercept": -1.3112702874365896,
        "crossfit_brier": 0.1481712144692399,
        "crossfit_log_loss": 0.47322094505966367
      },
      "ExtraTrees": {
        "coef": 0.27106745627609485,
        "intercept": -1.103508244352468,
        "crossfit_brier": 0.14773273329869982,
        "crossfit_log_loss": 0.4716693019498337
      },
      "HistGradientBoosting": {
        "coef": 0.14992135017419844,
        "intercept": -1.2844521938461804,
        "crossfit_brier": 0.14812793976871969,
        "crossfit_log_loss": 0.47298227285860556
      },
      "Bayesian_GLM_Laplace": {
        "coef": 0.6972771574814457,
        "intercept": -0.4576302306208956,
        "crossfit_brier": 0.1474181723183441,
        "crossfit_log_loss": 0.47069482969391824
      }
    },
    "production_weights": {
      "Bayesian_GLM_Laplace": 0.18521522310416602,
      "BetaBinomial": 0.0,
      "DynamicState": 0.0,
      "EWMA": 0.0,
      "ElasticNet": 0.1563066031154922,
      "ExtraTrees": 0.0,
      "FullFrequency": 0.0,
      "GradientBoosting": 0.0,
      "HierarchicalBayes": 0.0,
      "HistGradientBoosting": 0.0,
      "Logistic_L2": 0.05847817378034179,
      "RandomForest": 0.0,
      "RollingFrequency": 0.0,
      "Uniform": 0.6
    },
    "research_weights": {
      "Bayesian_GLM_Laplace": 0.08084968642345203,
      "BetaBinomial": 0.02143657402098459,
      "DynamicState": 0.05927027543059414,
      "EWMA": 0.020182351688411638,
      "ElasticNet": 0.13940991284067583,
      "ExtraTrees": 0.023630238382598253,
      "FullFrequency": 0.01995922141133335,
      "GradientBoosting": 0.02741403333166876,
      "HierarchicalBayes": 0.01238726772958466,
      "HistGradientBoosting": 0.005038483666530129,
      "Logistic_L2": 0.0815240408757206,
      "RandomForest": 0.004254099315959037,
      "RollingFrequency": 0.0247123127917326,
      "Uniform": 0.47993150209075436
    },
    "weight_diagnostics": {
      "development_brier": {
        "Bayesian_GLM_Laplace": 0.1474181723183441,
        "BetaBinomial": 0.14775764845627365,
        "DynamicState": 0.14749757147298315,
        "EWMA": 0.14777306624667025,
        "ElasticNet": 0.14727884525089852,
        "ExtraTrees": 0.14773273329869982,
        "FullFrequency": 0.1477759092380332,
        "GradientBoosting": 0.14769475068004984,
        "HierarchicalBayes": 0.14789789677629223,
        "HistGradientBoosting": 0.14812793976871969,
        "Logistic_L2": 0.1474160481843143,
        "RandomForest": 0.1481712144692399,
        "RollingFrequency": 0.147721283257301,
        "Uniform": 0.14742109314857585
      },
      "fold_brier": {
        "Bayesian_GLM_Laplace": [
          0.15999651875244467,
          0.1453514416811146,
          0.13888371313398293
        ],
        "BetaBinomial": [
          0.16089016959289926,
          0.14550675029289545,
          0.13893491949637152
        ],
        "DynamicState": [
          0.16027867193540307,
          0.1453403141236609,
          0.13887945461552018
        ],
        "EWMA": [
          0.16111289799932546,
          0.14540116160686845,
          0.13889160377362972
        ],
        "ElasticNet": [
          0.15969032887583168,
          0.14523058818921575,
          0.1388660306151681
        ],
        "ExtraTrees": [
          0.1610402488378293,
          0.14536329550204988,
          0.13887587647831975
        ],
        "FullFrequency": [
          0.16094576073750527,
          0.14551302511984635,
          0.13893336609984147
        ],
        "GradientBoosting": [
          0.16083811026215297,
          0.14535325181766465,
          0.1389483634178525
        ],
        "HierarchicalBayes": [
          0.1613006242732411,
          0.14559943397783628,
          0.13889481637096968
        ],
        "HistGradientBoosting": [
          0.16236300549605784,
          0.14535345959016926,
          0.13887979901034114
        ],
        "Logistic_L2": [
          0.1600302193204829,
          0.14533385568577933,
          0.1388663049124087
        ],
        "RandomForest": [
          0.16252518758173523,
          0.14532992177595136,
          0.1388869421698105
        ],
        "RollingFrequency": [
          0.16099636885103558,
          0.14535459763047026,
          0.1388888580006255
        ],
        "Uniform": [
          0.16000000000000006,
          0.1453514739229025,
          0.1388888888888889
        ]
      },
      "eligible_models": [
        "Bayesian_GLM_Laplace",
        "ElasticNet",
        "Logistic_L2"
      ]
    },
    "frozen_holdout_metrics": {
      "Uniform": {
        "brier": 0.1388888888888889,
        "log_loss": 0.45056120886630463,
        "ece": 0.0,
        "avg_hits": 0.3230769230769231,
        "precision_at_k": 0.16153846153846155,
        "mean_winning_rank": 6.469230769230769,
        "draws": 195
      },
      "FullFrequency": {
        "brier": 0.13888112102409858,
        "log_loss": 0.4505318998559891,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.448717948717949,
        "draws": 195
      },
      "RollingFrequency": {
        "brier": 0.13894192470383657,
        "log_loss": 0.45075335873903727,
        "ece": 0.0,
        "avg_hits": 0.31794871794871793,
        "precision_at_k": 0.15897435897435896,
        "mean_winning_rank": 6.615384615384615,
        "draws": 195
      },
      "EWMA": {
        "brier": 0.13891000383190213,
        "log_loss": 0.45063763639738086,
        "ece": 0.0,
        "avg_hits": 0.30256410256410254,
        "precision_at_k": 0.15128205128205127,
        "mean_winning_rank": 6.484615384615385,
        "draws": 195
      },
      "BetaBinomial": {
        "brier": 0.13888178106727514,
        "log_loss": 0.45053426596456564,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.443589743589744,
        "draws": 195
      },
      "HierarchicalBayes": {
        "brier": 0.13890001845894617,
        "log_loss": 0.4506013821489368,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.4743589743589745,
        "draws": 195
      },
      "DynamicState": {
        "brier": 0.13891417774038214,
        "log_loss": 0.4506535192813756,
        "ece": 0.0,
        "avg_hits": 0.35384615384615387,
        "precision_at_k": 0.17692307692307693,
        "mean_winning_rank": 6.538461538461538,
        "draws": 195
      },
      "Logistic_L2": {
        "brier": 0.13891846898723928,
        "log_loss": 0.45067831309904033,
        "ece": 0.0,
        "avg_hits": 0.35384615384615387,
        "precision_at_k": 0.17692307692307693,
        "mean_winning_rank": 6.464102564102564,
        "draws": 195
      },
      "ElasticNet": {
        "brier": 0.1389896568357438,
        "log_loss": 0.45095525429214434,
        "ece": 0.0,
        "avg_hits": 0.3435897435897436,
        "precision_at_k": 0.1717948717948718,
        "mean_winning_rank": 6.456410256410257,
        "draws": 195
      },
      "GradientBoosting": {
        "brier": 0.13892445904809841,
        "log_loss": 0.45068901108830556,
        "ece": 0.0,
        "avg_hits": 0.3384615384615385,
        "precision_at_k": 0.16923076923076924,
        "mean_winning_rank": 6.546153846153846,
        "draws": 195
      },
      "RandomForest": {
        "brier": 0.13889823631954018,
        "log_loss": 0.4505945772505296,
        "ece": 0.0,
        "avg_hits": 0.358974358974359,
        "precision_at_k": 0.1794871794871795,
        "mean_winning_rank": 6.433333333333334,
        "draws": 195
      },
      "ExtraTrees": {
        "brier": 0.13883627828454848,
        "log_loss": 0.450369481600093,
        "ece": 0.0,
        "avg_hits": 0.3435897435897436,
        "precision_at_k": 0.1717948717948718,
        "mean_winning_rank": 6.28974358974359,
        "draws": 195
      },
      "HistGradientBoosting": {
        "brier": 0.13886008721940307,
        "log_loss": 0.4504577737586663,
        "ece": 0.0,
        "avg_hits": 0.3435897435897436,
        "precision_at_k": 0.1717948717948718,
        "mean_winning_rank": 6.4051282051282055,
        "draws": 195
      },
      "Bayesian_GLM_Laplace": {
        "brier": 0.13889003954469034,
        "log_loss": 0.4505654163788208,
        "ece": 0.0,
        "avg_hits": 0.3282051282051282,
        "precision_at_k": 0.1641025641025641,
        "mean_winning_rank": 6.482051282051282,
        "draws": 195
      },
      "ProductionEnsemble": {
        "brier": 0.1388920361011362,
        "log_loss": 0.4505735381029349,
        "ece": 0.0,
        "avg_hits": 0.3487179487179487,
        "precision_at_k": 0.17435897435897435,
        "mean_winning_rank": 6.48974358974359,
        "draws": 195
      }
    },
    "prequential_holdout_metrics": {
      "Uniform": {
        "brier": 0.1388888888888889,
        "log_loss": 0.45056120886630463,
        "ece": 0.0,
        "avg_hits": 0.3230769230769231,
        "precision_at_k": 0.16153846153846155,
        "mean_winning_rank": 6.469230769230769,
        "draws": 195
      },
      "FullFrequency": {
        "brier": 0.13888112102409858,
        "log_loss": 0.4505318998559891,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.448717948717949,
        "draws": 195
      },
      "RollingFrequency": {
        "brier": 0.13894192470383657,
        "log_loss": 0.45075335873903727,
        "ece": 0.0,
        "avg_hits": 0.31794871794871793,
        "precision_at_k": 0.15897435897435896,
        "mean_winning_rank": 6.615384615384615,
        "draws": 195
      },
      "EWMA": {
        "brier": 0.13891000383190213,
        "log_loss": 0.45063763639738086,
        "ece": 0.0,
        "avg_hits": 0.30256410256410254,
        "precision_at_k": 0.15128205128205127,
        "mean_winning_rank": 6.484615384615385,
        "draws": 195
      },
      "BetaBinomial": {
        "brier": 0.13888178106727514,
        "log_loss": 0.45053426596456564,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.443589743589744,
        "draws": 195
      },
      "HierarchicalBayes": {
        "brier": 0.13890001845894617,
        "log_loss": 0.4506013821489368,
        "ece": 0.0,
        "avg_hits": 0.3641025641025641,
        "precision_at_k": 0.18205128205128204,
        "mean_winning_rank": 6.4743589743589745,
        "draws": 195
      },
      "DynamicState": {
        "brier": 0.13891417774038214,
        "log_loss": 0.4506535192813756,
        "ece": 0.0,
        "avg_hits": 0.35384615384615387,
        "precision_at_k": 0.17692307692307693,
        "mean_winning_rank": 6.538461538461538,
        "draws": 195
      },
      "Logistic_L2": {
        "brier": 0.13896574609216938,
        "log_loss": 0.450849304421337,
        "ece": 0.0,
        "avg_hits": 0.358974358974359,
        "precision_at_k": 0.1794871794871795,
        "mean_winning_rank": 6.507692307692308,
        "draws": 195
      },
      "ElasticNet": {
        "brier": 0.13880869704778753,
        "log_loss": 0.4503045378777253,
        "ece": 0.00017106328188712912,
        "avg_hits": 0.4153846153846154,
        "precision_at_k": 0.2076923076923077,
        "mean_winning_rank": 6.317948717948718,
        "draws": 195
      },
      "GradientBoosting": {
        "brier": 0.13894305758089082,
        "log_loss": 0.4507552519469678,
        "ece": 0.0,
        "avg_hits": 0.3076923076923077,
        "precision_at_k": 0.15384615384615385,
        "mean_winning_rank": 6.746153846153846,
        "draws": 195
      },
      "RandomForest": {
        "brier": 0.13891165129799368,
        "log_loss": 0.4506418239818719,
        "ece": 0.0,
        "avg_hits": 0.3128205128205128,
        "precision_at_k": 0.1564102564102564,
        "mean_winning_rank": 6.517948717948718,
        "draws": 195
      },
      "ExtraTrees": {
        "brier": 0.13889887357959135,
        "log_loss": 0.4505958503323116,
        "ece": 0.0,
        "avg_hits": 0.3230769230769231,
        "precision_at_k": 0.16153846153846155,
        "mean_winning_rank": 6.448717948717949,
        "draws": 195
      },
      "HistGradientBoosting": {
        "brier": 0.13889802520977526,
        "log_loss": 0.4505944637684992,
        "ece": 0.0,
        "avg_hits": 0.35384615384615387,
        "precision_at_k": 0.17692307692307693,
        "mean_winning_rank": 6.469230769230769,
        "draws": 195
      },
      "Bayesian_GLM_Laplace": {
        "brier": 0.13889438236502372,
        "log_loss": 0.4505810596165597,
        "ece": 0.0,
        "avg_hits": 0.38461538461538464,
        "precision_at_k": 0.19230769230769232,
        "mean_winning_rank": 6.530769230769231,
        "draws": 195
      },
      "ProductionEnsemble": {
        "brier": 0.1388632519854934,
        "log_loss": 0.45046972725956863,
        "ece": 0.0,
        "avg_hits": 0.37948717948717947,
        "precision_at_k": 0.18974358974358974,
        "mean_winning_rank": 6.3538461538461535,
        "draws": 195
      }
    },
    "reality_check": {
      "observed_brier_improvement": {
        "FullFrequency": 7.76786479031455e-06,
        "RollingFrequency": -5.303581494767173e-05,
        "EWMA": -2.1114943013239573e-05,
        "BetaBinomial": 7.1078216137554495e-06,
        "HierarchicalBayes": -1.1129570057277771e-05,
        "DynamicState": -2.528885149324922e-05,
        "Logistic_L2": -7.685720328048928e-05,
        "ElasticNet": 8.019184110136246e-05,
        "GradientBoosting": -5.4168692001921315e-05,
        "RandomForest": -2.276240910478733e-05,
        "ExtraTrees": -9.98469070245811e-06,
        "HistGradientBoosting": -9.136320886365956e-06,
        "Bayesian_GLM_Laplace": -5.493476134821318e-06,
        "ProductionEnsemble": 2.563690339549285e-05
      },
      "maxT_adjusted_p": {
        "FullFrequency": 1.0,
        "RollingFrequency": 1.0,
        "EWMA": 1.0,
        "BetaBinomial": 1.0,
        "HierarchicalBayes": 1.0,
        "DynamicState": 1.0,
        "Logistic_L2": 1.0,
        "ElasticNet": 0.5237904838064774,
        "GradientBoosting": 1.0,
        "RandomForest": 1.0,
        "ExtraTrees": 1.0,
        "HistGradientBoosting": 1.0,
        "Bayesian_GLM_Laplace": 1.0,
        "ProductionEnsemble": 0.998000799680128
      },
      "best_model": "ElasticNet",
      "best_improvement": 8.019184110136246e-05,
      "best_adjusted_p": 0.5237904838064774
    },
    "block_bootstrap": {
      "mean": 2.5636903395483027e-05,
      "ci_low": -3.530236185524323e-05,
      "ci_high": 8.734377855967239e-05,
      "prob_positive": 0.7953333333333333
    },
    "period_brier_improvements": [
      7.773776212296938e-05,
      -1.7853950597795077e-05,
      1.7026898661274782e-05
    ],
    "acceptance_criteria": {
      "frozen_brier_better": false,
      "prequential_brier_better": true,
      "frozen_log_loss_better": false,
      "prequential_log_loss_better": true,
      "positive_all_three_periods": false,
      "maxT_adjusted_p_below_0_05": false,
      "block_bootstrap_ci_positive": false,
      "nonuniform_weight_positive": true
    },
    "status": "Uniform mode"
  },
  "randomness_audit": {
    "main": {
      "draws_tested": 975,
      "max_marginal_z": 2.081665999466133,
      "familywise_frequency_p": 0.8780609695152424,
      "mean_consecutive_overlap": 0.5010266940451745,
      "expected_overlap": 0.5,
      "overlap_p": 0.9795102448775612,
      "tuesday_friday_max_stat": 2.046580088489482,
      "tuesday_friday_familywise_p": 0.8830584707646177,
      "march_2024_sensitivity_max_stat": 2.4920090405167676,
      "march_2024_familywise_p": 0.4617691154422789,
      "anomaly_detected_5pct": false
    },
    "euro": {
      "draws_tested": 453,
      "max_marginal_z": 2.080180837783291,
      "familywise_frequency_p": 0.4312843578210895,
      "mean_consecutive_overlap": 0.3407079646017699,
      "expected_overlap": 0.3333333333333333,
      "overlap_p": 0.792103948025987,
      "tuesday_friday_max_stat": 3.101747410498038,
      "tuesday_friday_familywise_p": 0.026986506746626688,
      "march_2024_sensitivity_max_stat": 2.2294356687327186,
      "march_2024_familywise_p": 0.2478760619690155,
      "anomaly_detected_5pct": true
    }
  },
  "overall_status": "Uniform mode",
  "research_next_probabilities": {
    "main": {
      "1": 0.09987678976149147,
      "2": 0.1001495319395483,
      "3": 0.10015154311951638,
      "4": 0.09968174730503979,
      "5": 0.10025384424694125,
      "6": 0.09961815292492085,
      "7": 0.09987406395526058,
      "8": 0.0994093874403769,
      "9": 0.09992771416701675,
      "10": 0.10013134603873602,
      "11": 0.09966156914686326,
      "12": 0.09998885615953719,
      "13": 0.09986061916218658,
      "14": 0.09993273737582714,
      "15": 0.09985948641527317,
      "16": 0.09977994815559194,
      "17": 0.09939353447381845,
      "18": 0.09974751055103448,
      "19": 0.09985190143758807,
      "20": 0.09963826691331765,
      "21": 0.09968763118608891,
      "22": 0.09957835647145549,
      "23": 0.09974441831929293,
      "24": 0.10018133599019044,
      "25": 0.1003729741093097,
      "26": 0.10026515412719167,
      "27": 0.10030226585461251,
      "28": 0.10047492781414348,
      "29": 0.10005390527327881,
      "30": 0.10000114676649094,
      "31": 0.10012584001421021,
      "32": 0.10017612840034419,
      "33": 0.10019539335650926,
      "34": 0.09994635119309754,
      "35": 0.09976739480531059,
      "36": 0.10048828487402145,
      "37": 0.10005224527374809,
      "38": 0.10003353130248406,
      "39": 0.09991756078064833,
      "40": 0.10012080949746457,
      "41": 0.09987749390052224,
      "42": 0.10034352320504869,
      "43": 0.10010048201427241,
      "44": 0.10020582628233678,
      "45": 0.10006293001495176,
      "46": 0.10007155392477922,
      "47": 0.10012484275260847,
      "48": 0.10068598460313188,
      "49": 0.09984820184655188,
      "50": 0.10040495535601776
    },
    "euro": {
      "1": 0.16441687714829242,
      "2": 0.1649471333416093,
      "3": 0.1687776783750218,
      "4": 0.1667843923962404,
      "5": 0.17150680151168632,
      "6": 0.1665141144704443,
      "7": 0.1664286771190058,
      "8": 0.16850694682152564,
      "9": 0.16850975970959128,
      "10": 0.16655839597658395,
      "11": 0.16200630891693188,
      "12": 0.16504291421306702
    }
  },
  "primary_experimental_line": {
    "line": 1,
    "main": [
      4,
      32,
      36,
      41,
      47
    ],
    "euro": [
      5,
      9
    ],
    "portfolio_score": -1.2714025391503996,
    "anti_crowd_score": 0.8
  },
  "portfolio": [
    {
      "line": 1,
      "main": [
        4,
        32,
        36,
        41,
        47
      ],
      "euro": [
        5,
        9
      ],
      "portfolio_score": -1.2714025391503996,
      "anti_crowd_score": 0.8
    },
    {
      "line": 2,
      "main": [
        4,
        32,
        37,
        41,
        45
      ],
      "euro": [
        2,
        3
      ],
      "portfolio_score": -4.273987711446938,
      "anti_crowd_score": 0.8
    },
    {
      "line": 3,
      "main": [
        1,
        32,
        37,
        44,
        48
      ],
      "euro": [
        3,
        7
      ],
      "portfolio_score": -4.979041408852963,
      "anti_crowd_score": 0.8
    },
    {
      "line": 4,
      "main": [
        6,
        32,
        39,
        41,
        43
      ],
      "euro": [
        1,
        8
      ],
      "portfolio_score": -5.679759942038884,
      "anti_crowd_score": 0.8
    },
    {
      "line": 5,
      "main": [
        2,
        35,
        37,
        44,
        46
      ],
      "euro": [
        4,
        10
      ],
      "portfolio_score": -3.8862714734415316,
      "anti_crowd_score": 0.8
    },
    {
      "line": 6,
      "main": [
        2,
        34,
        36,
        43,
        49
      ],
      "euro": [
        7,
        12
      ],
      "portfolio_score": -4.7872819912539475,
      "anti_crowd_score": 0.8
    },
    {
      "line": 7,
      "main": [
        8,
        33,
        39,
        42,
        45
      ],
      "euro": [
        8,
        9
      ],
      "portfolio_score": -5.091524392494627,
      "anti_crowd_score": 0.8
    },
    {
      "line": 8,
      "main": [
        1,
        35,
        38,
        42,
        50
      ],
      "euro": [
        10,
        12
      ],
      "portfolio_score": -5.892316820102814,
      "anti_crowd_score": 0.8
    },
    {
      "line": 9,
      "main": [
        4,
        6,
        35,
        40,
        47
      ],
      "euro": [
        6,
        11
      ],
      "portfolio_score": -6.330912935459112,
      "anti_crowd_score": 0.6000000000000001
    },
    {
      "line": 10,
      "main": [
        3,
        17,
        34,
        40,
        49
      ],
      "euro": [
        5,
        6
      ],
      "portfolio_score": -6.151398030920604,
      "anti_crowd_score": 0.6000000000000001
    }
  ],
  "audit_findings": [
    [
      "CALENDAR_COMPLETENESS",
      "PASS",
      "975 of 975 expected draw dates; no duplicates or off-schedule dates"
    ],
    [
      "UPLOADED_2024_2026_CROSSCHECK",
      "PASS",
      "235 of 235 uploaded draws matched canonical numbers exactly"
    ],
    [
      "V2_CALIBRATION_CLAIM",
      "CORRECTED",
      "CalibratedClassifierCV was imported but no calibration was applied; v3 uses cross-fitted Platt calibration"
    ],
    [
      "V2_NEXT_DATE",
      "CORRECTED",
      "Hard-coded date replaced by calendar-derived next Tuesday/Friday"
    ],
    [
      "V2_HOLDOUT_REFIT",
      "CORRECTED",
      "Added frozen and block-prequential expanding-history holdout evaluations"
    ],
    [
      "V2_ENSEMBLE_OPTIMIZER",
      "CORRECTED",
      "Previous weights remained at the initial equal allocation; v3 uses fold-consistent robust weighting and can revert to 100% uniform"
    ],
    [
      "SOURCE_STATUS",
      "CORRECTED",
      "Older rows no longer labeled cross-source unless independently checked"
    ],
    [
      "DRAW_PROBABILITY_EDGE",
      "Uniform mode",
      "Acceptance requires frozen+prequential gains, three-period consistency, maxT correction and positive block-bootstrap CI"
    ],
    [
      "VALUE_EDGE",
      "PORTFOLIO_ONLY",
      "Anti-crowd proxies may reduce prize sharing but do not increase draw probability"
    ],
    [
      "V2_DRAW_LEVEL_PERMUTATION",
      "CORRECTED",
      "Within-draw permutation cannot test features that are constant for every candidate number in a draw; v3.1 adds a separate weekday-number interaction audit."
    ],
    [
      "EURO_WEEKDAY_EFFECT",
      "REJECTED_AS_EDGE",
      "Nested-development-selected model holdout improvement 0.000002890228; permutation p=0.594; bootstrap CI crosses zero."
    ],
    [
      "GLOBAL_RANDOMNESS_CORRECTION",
      "PASS",
      "Minimum raw audit p=0.026987; Bonferroni across 8 families=0.215892."
    ],
    [
      "DEPLOYMENT_GATE",
      "CORRECTED",
      "Uniform-mode pools now deploy exactly uniform probabilities; non-uniform scores remain research-only."
    ]
  ],
  "interpretation": "A reliable draw-probability edge is established only if all prespecified tests pass. Otherwise production probabilities revert toward or fully to uniform; research ranks remain explicitly experimental.",
  "global_randomness_multiple_testing": {
    "tests": 8,
    "minimum_raw_p": 0.026986506746626688,
    "bonferroni_min_p": 0.2158920539730135,
    "conclusion": "No anomaly remains significant after correction across the eight prespecified audit families."
  },
  "weekday_effect_targeted_audit": {
    "audit_version": "3.1",
    "protocol": "C selected using three expanding development folds; untouched final 20% evaluated once",
    "candidate_C": [
      0.0003,
      0.001,
      0.003,
      0.01,
      0.03,
      0.1,
      0.3
    ],
    "development_cv": {
      "0.0003": {
        "mean_brier": 0.13888885610453197,
        "fold_brier": [
          0.138887283685392,
          0.13888999532153462,
          0.1388892893066693
        ]
      },
      "0.001": {
        "mean_brier": 0.1388891414205732,
        "fold_brier": [
          0.13888382058809676,
          0.13889300650406933,
          0.1388905971695535
        ]
      },
      "0.003": {
        "mean_brier": 0.13889241202443042,
        "fold_brier": [
          0.13887608749553687,
          0.1389043169733828,
          0.1388968316043716
        ]
      },
      "0.01": {
        "mean_brier": 0.13892195167876775,
        "fold_brier": [
          0.13886744583966545,
          0.13896498737472254,
          0.13893342182191526
        ]
      },
      "0.03": {
        "mean_brier": 0.13904499162237688,
        "fold_brier": [
          0.13891535773804436,
          0.1391684733233318,
          0.1390511438057545
        ]
      },
      "0.1": {
        "mean_brier": 0.1393498926200891,
        "fold_brier": [
          0.1391130214951065,
          0.13963423727361343,
          0.1393024190915473
        ]
      },
      "0.3": {
        "mean_brier": 0.13969194009481986,
        "fold_brier": [
          0.1393245587683653,
          0.14018691642091624,
          0.13956434509517804
        ]
      }
    },
    "selected_C": 0.0003,
    "holdout": {
      "draws": 195,
      "model_brier": 0.1388859986606943,
      "uniform_brier": 0.1388888888888889,
      "brier_improvement": 2.8902281946074915e-06,
      "model_log_loss": 0.45055080152406907,
      "uniform_log_loss": 0.45056120886630463,
      "average_top2_hits": 0.3641025641025641,
      "permutation_p": 0.593940605939406,
      "block_bootstrap_ci_low": -9.030543757266813e-06,
      "block_bootstrap_ci_high": 1.4994799414908725e-05,
      "block_bootstrap_probability_positive": 0.6867
    },
    "descriptive_number_4": {
      "tuesday_draws": 226,
      "friday_draws": 227,
      "tuesday_occurrences": 44,
      "friday_occurrences": 21,
      "tuesday_rate": 0.19469026548672566,
      "friday_rate": 0.09251101321585903
    },
    "conclusion": "Not a reliable predictive edge: holdout improvement is negligible, permutation p is not significant, and the block-bootstrap interval crosses zero."
  },
  "candidate_next_probabilities": {
    "main": {
      "1": 0.10000000000000003,
      "2": 0.10000000000000003,
      "3": 0.10000000000000003,
      "4": 0.10000000000000003,
      "5": 0.10000000000000003,
      "6": 0.10000000000000003,
      "7": 0.10000000000000003,
      "8": 0.10000000000000003,
      "9": 0.10000000000000003,
      "10": 0.10000000000000003,
      "11": 0.10000000000000003,
      "12": 0.10000000000000003,
      "13": 0.10000000000000003,
      "14": 0.10000000000000003,
      "15": 0.10000000000000003,
      "16": 0.10000000000000003,
      "17": 0.10000000000000003,
      "18": 0.10000000000000003,
      "19": 0.10000000000000003,
      "20": 0.10000000000000003,
      "21": 0.10000000000000003,
      "22": 0.10000000000000003,
      "23": 0.10000000000000003,
      "24": 0.10000000000000003,
      "25": 0.10000000000000003,
      "26": 0.10000000000000003,
      "27": 0.10000000000000003,
      "28": 0.10000000000000003,
      "29": 0.10000000000000003,
      "30": 0.10000000000000003,
      "31": 0.10000000000000003,
      "32": 0.10000000000000003,
      "33": 0.10000000000000003,
      "34": 0.10000000000000003,
      "35": 0.10000000000000003,
      "36": 0.10000000000000003,
      "37": 0.10000000000000003,
      "38": 0.10000000000000003,
      "39": 0.10000000000000003,
      "40": 0.10000000000000003,
      "41": 0.10000000000000003,
      "42": 0.10000000000000003,
      "43": 0.10000000000000003,
      "44": 0.10000000000000003,
      "45": 0.10000000000000003,
      "46": 0.10000000000000003,
      "47": 0.10000000000000003,
      "48": 0.10000000000000003,
      "49": 0.10000000000000003,
      "50": 0.10000000000000003
    },
    "euro": {
      "1": 0.16446565392170698,
      "2": 0.16530422750677273,
      "3": 0.16812519034666354,
      "4": 0.16748555236264115,
      "5": 0.17022422668986928,
      "6": 0.166728569487839,
      "7": 0.16582658947638204,
      "8": 0.16897243099569884,
      "9": 0.16853357205498534,
      "10": 0.1669513780468105,
      "11": 0.16261029587887685,
      "12": 0.1647723132317539
    }
  },
  "deployed_next_probabilities": {
    "main": {
      "1": 0.1,
      "2": 0.1,
      "3": 0.1,
      "4": 0.1,
      "5": 0.1,
      "6": 0.1,
      "7": 0.1,
      "8": 0.1,
      "9": 0.1,
      "10": 0.1,
      "11": 0.1,
      "12": 0.1,
      "13": 0.1,
      "14": 0.1,
      "15": 0.1,
      "16": 0.1,
      "17": 0.1,
      "18": 0.1,
      "19": 0.1,
      "20": 0.1,
      "21": 0.1,
      "22": 0.1,
      "23": 0.1,
      "24": 0.1,
      "25": 0.1,
      "26": 0.1,
      "27": 0.1,
      "28": 0.1,
      "29": 0.1,
      "30": 0.1,
      "31": 0.1,
      "32": 0.1,
      "33": 0.1,
      "34": 0.1,
      "35": 0.1,
      "36": 0.1,
      "37": 0.1,
      "38": 0.1,
      "39": 0.1,
      "40": 0.1,
      "41": 0.1,
      "42": 0.1,
      "43": 0.1,
      "44": 0.1,
      "45": 0.1,
      "46": 0.1,
      "47": 0.1,
      "48": 0.1,
      "49": 0.1,
      "50": 0.1
    },
    "euro": {
      "1": 0.16666666666666666,
      "2": 0.16666666666666666,
      "3": 0.16666666666666666,
      "4": 0.16666666666666666,
      "5": 0.16666666666666666,
      "6": 0.16666666666666666,
      "7": 0.16666666666666666,
      "8": 0.16666666666666666,
      "9": 0.16666666666666666,
      "10": 0.16666666666666666,
      "11": 0.16666666666666666,
      "12": 0.16666666666666666
    }
  },
  "deployment_rule": "Non-uniform probabilities are deployed only after all prespecified validation criteria pass; otherwise the deployed model is uniform."
}