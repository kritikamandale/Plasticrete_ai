"""
M1Trainer: orchestrates data loading â†’ CTGAN augmentation â†’ model training â†’ evaluation â†’ save.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from modules.m1_prediction.utils.data_loader import (
    PRETRAIN_SOURCES, load_all_sources, print_coverage_report, save_master,
)
from modules.m1_prediction.utils.preprocessor import Preprocessor
from modules.m1_prediction.utils.schema import (
    MIN_COVERAGE_ROWS, SOURCE_DOI, STUDY_TYPE, TARGET_COLUMNS,
    TARGET_RANGES, INPUT_RANGES, PLASTIC_TYPE,
)
from modules.m1_prediction.model.xgboost_model import XGBoostMultiOutput
from modules.m1_prediction.model.random_forest_model import RandomForestMultiOutput
from modules.m1_prediction.model.dnn_model import DNNModel
from modules.m1_prediction.model.ensemble import PlastiCreteEnsemble
from modules.m1_prediction.model import evaluator as _evaluator


class M1Trainer:
    def __init__(self, config: dict, raw_dir: str = "data/raw",
                 processed_dir: str = "data/processed",
                 save_dir: str = "models/m1/") -> None:
        self.config       = config
        self.raw_dir      = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.save_dir     = Path(save_dir)

    def run(
        self,
        tune_xgb: bool = False,
        use_transfer: bool = True,
        use_ctgan: bool = True,
    ) -> PlastiCreteEnsemble:
        wall_start = time.time()

        # â”€â”€ Stage 0: Load raw data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 0: Loading raw sources â€¦")
        master_df = load_all_sources(self.raw_dir)
        save_master(master_df, self.processed_dir)
        print_coverage_report(master_df)
        logger.info(f"Stage 0 done in {time.time()-t0:.1f}s  |  total rows: {len(master_df)}")

        # â”€â”€ Stage 0b: Split pretrain vs plastic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        pretrain_dois = set()
        for fname in PRETRAIN_SOURCES:
            # Match DOIs injected in _load_uci_yeh and _load_mendeley_rubberized
            if "uci" in fname:
                pretrain_dois.add("10.1061/(ASCE)0899-1561(1998)10:1(52)")
            elif "mendeley" in fname:
                pretrain_dois.add("mendeley_rubberized_concrete")

        pretrain_df = master_df[master_df[SOURCE_DOI].isin(pretrain_dois)].copy()
        plastic_df  = master_df[~master_df[SOURCE_DOI].isin(pretrain_dois)].copy()
        logger.info(f"Stage 0b: pretrain={len(pretrain_df)}, plastic={len(plastic_df)}")

        # â”€â”€ Stage 0c: CTGAN augmentation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if use_ctgan:
            t0 = time.time()
            low_targets = [
                t for t in TARGET_COLUMNS
                if plastic_df[t].notna().sum() < 100 if t in plastic_df.columns
            ]
            if low_targets:
                logger.info(f"Stage 0c: CTGAN augmenting for low-coverage targets: {low_targets}")
                synth = self._ctgan_augment(plastic_df)
                if synth is not None and len(synth) > 0:
                    plastic_df = pd.concat([plastic_df, synth], ignore_index=True)
                    master_df  = pd.concat([master_df, synth], ignore_index=True)
                    logger.info(f"  +{len(synth)} synthetic rows added")
            else:
                logger.info("Stage 0c: All targets have â‰¥100 rows â€” CTGAN skipped")
            logger.info(f"Stage 0c done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 1-2: Preprocess splits â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 1-3: Preprocessing â€¦")
        cfg_pre = self.config.get("preprocessing", {})
        test_size = cfg_pre.get("test_size", 0.15)
        val_size  = cfg_pre.get("validation_size", 0.15)
        seed      = cfg_pre.get("random_seed", 42)

        preprocessor = Preprocessor()

        # Master split (used by XGB, RF, and overall eval)
        train_df, val_df, test_df = preprocessor.split(
            master_df, test_size=test_size, val_size=val_size, random_seed=seed
        )
        X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.fit_transform(
            train_df, val_df, test_df
        )
        feature_names = preprocessor.feature_names
        logger.info(f"Feature matrix shape: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")

        # Pretrain split (DNN pretraining) — transform using already-fitted preprocessor
        n_feat = X_train.shape[1]
        X_ptr  = np.empty((0, n_feat));  X_pval = np.empty((0, n_feat))
        y_ptr  = np.empty((0, 7));       y_pval = np.empty((0, 7))
        if use_transfer and len(pretrain_df) > 20:
            ptr_tr, ptr_val_df, _ = preprocessor.split(
                pretrain_df, test_size=0.10, val_size=0.10, random_seed=seed
            )
            X_ptr,  y_ptr  = preprocessor.transform_df(ptr_tr)
            X_pval, y_pval = preprocessor.transform_df(ptr_val_df)

        # Plastic-specific split (DNN finetuning) — same: use fitted preprocessor
        X_ftr  = np.empty((0, n_feat));  X_fval = np.empty((0, n_feat))
        y_ftr  = np.empty((0, 7));       y_fval = np.empty((0, 7))
        if use_transfer and len(plastic_df) > 20:
            ftr_tr, ftr_val_df, _ = preprocessor.split(
                plastic_df, test_size=0.10, val_size=0.10, random_seed=seed
            )
            X_ftr,  y_ftr  = preprocessor.transform_df(ftr_tr)
            X_fval, y_fval = preprocessor.transform_df(ftr_val_df)

        logger.info(f"Stage 1-3 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 4-5: DNN transfer learning â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        dnn = DNNModel(self.config)
        if use_transfer and X_ptr.shape[0] > 0:
            logger.info("Stage 4: DNN pretrain â€¦")
            dnn.pretrain(X_ptr, y_ptr, X_pval, y_pval)
            logger.info(f"Stage 4 done in {time.time()-t0:.1f}s")

            t0 = time.time()
            if X_ftr.shape[0] > 0:
                logger.info("Stage 5: DNN finetune â€¦")
                dnn.finetune(X_ftr, y_ftr, X_fval, y_fval)
            else:
                logger.info("Stage 5: No plastic-specific rows â€” finetuning on master train")
                dnn.finetune(X_train, y_train, X_val, y_val)
            logger.info(f"Stage 5 done in {time.time()-t0:.1f}s")
        else:
            logger.info("Stage 4-5: Single-stage DNN training (no transfer)")
            dnn.fit(X_train, y_train, X_val, y_val)
            logger.info(f"Stage 4-5 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 6: XGBoost â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info(f"Stage 6: XGBoost {'+ Optuna HPO' if tune_xgb else 'fit'} â€¦")
        xgb = XGBoostMultiOutput(self.config)
        xgb.fit(X_train, y_train, X_val, y_val, feature_names=feature_names, tune=tune_xgb)
        logger.info(f"Stage 6 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 7: Random Forest â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 7: Random Forest fit â€¦")
        rf = RandomForestMultiOutput(self.config)
        rf.fit(X_train, y_train, feature_names=feature_names)
        logger.info(f"Stage 7 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 8: Ensemble weights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 8: Computing ensemble weights â€¦")
        ensemble = PlastiCreteEnsemble(xgb, rf, dnn, preprocessor, self.config)
        ensemble.compute_weights(X_val, y_val)
        logger.info(f"Stage 8 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 9: Evaluate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 9: Evaluation on test set â€¦")
        _evaluator.evaluate(ensemble, X_test, y_test, preprocessor, save_dir=self.save_dir)
        logger.info(f"Stage 9 done in {time.time()-t0:.1f}s")

        # â”€â”€ Stage 10: Save â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        t0 = time.time()
        logger.info("Stage 10: Saving ensemble â€¦")
        ensemble.save(self.save_dir)
        logger.info(f"Stage 10 done in {time.time()-t0:.1f}s")

        total = time.time() - wall_start
        logger.info(f"âœ… M1 training complete  |  total wall time: {total/60:.1f} min")
        return ensemble

    def _ctgan_augment(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        try:
            from sdv.single_table import CTGANSynthesizer
            from sdv.metadata import SingleTableMetadata
        except ImportError:
            logger.warning("sdv/ctgan not installed â€” skipping augmentation")
            return None

        cfg = self.config.get("augmentation", {}).get("ctgan", {})
        n_synthetic = cfg.get("n_synthetic_rows", 500)
        epochs      = cfg.get("epochs", 300)

        cols_to_use = [
            c for c in df.columns
            if c in (
                list(INPUT_RANGES.keys()) +
                [PLASTIC_TYPE, "additive_type"] +
                TARGET_COLUMNS
            )
        ]
        train_data = df[cols_to_use].dropna(subset=[TARGET_COLUMNS[0]], how="all")
        if len(train_data) < 20:
            logger.warning("Not enough rows for CTGAN â€” skipping")
            return None

        try:
            metadata = SingleTableMetadata()
            metadata.detect_from_dataframe(train_data)

            synth = CTGANSynthesizer(metadata, epochs=epochs, batch_size=500, verbose=False)
            synth.fit(train_data)
            syn_df = synth.sample(num_rows=n_synthetic)

            # Rejection sampling: clip to valid ranges
            for col, (lo, hi) in INPUT_RANGES.items():
                if col in syn_df.columns:
                    syn_df[col] = syn_df[col].clip(lo, hi)
            for col, (lo, hi) in TARGET_RANGES.items():
                if col in syn_df.columns:
                    syn_df[col] = syn_df[col].clip(lo, hi)

            syn_df[SOURCE_DOI] = "ctgan_synthetic"
            syn_df[STUDY_TYPE] = "synthetic"
            return syn_df
        except Exception as exc:
            logger.warning(f"CTGAN failed: {exc}")
            return None

