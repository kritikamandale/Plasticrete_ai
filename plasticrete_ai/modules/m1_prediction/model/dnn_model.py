"""
DNN with MaskedMSELoss, transfer learning (pretrain â†’ finetune), and MC Dropout.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from loguru import logger

from modules.m1_prediction.utils.schema import TARGET_COLUMNS

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


class MaskedMSELoss(nn.Module if _TORCH_AVAILABLE else object):
    """MSE loss that ignores NaN targets -- each element masked independently."""

    def forward(self, y_pred: "torch.Tensor", y_true: "torch.Tensor") -> "torch.Tensor":
        mask = ~torch.isnan(y_true)
        if mask.sum() == 0:
            return torch.tensor(0.0, requires_grad=True, device=y_pred.device)
        return ((y_pred[mask] - y_true[mask]) ** 2).mean()


class PlastiCreteDNN(nn.Module if _TORCH_AVAILABLE else object):
    """4-block BN+ReLU+Dropout network with a 7-output head."""

    def __init__(
        self,
        n_features: int,
        hidden: List[int] = None,
        dropout: float = 0.25,
        n_outputs: int = 7,
    ) -> None:
        super().__init__()
        hidden = hidden or [256, 128, 64, 32]
        self.n_features = n_features

        layers: List[nn.Module] = []
        in_dim = n_features
        for h in hidden:
            layers += [
                nn.Linear(in_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ]
            in_dim = h
        layers.append(nn.Linear(in_dim, n_outputs))
        self.net = nn.Sequential(*layers)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)

    def enable_dropout(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Dropout):
                m.train()


def _to_tensor(arr: np.ndarray, device: "torch.device") -> "torch.Tensor":
    """Replace NaN with 0 for tensor, but MaskedMSELoss still sees NaN via mask."""
    safe = np.where(np.isnan(arr), 0.0, arr)
    return torch.tensor(safe, dtype=torch.float32, device=device)


def _nan_tensor(arr: np.ndarray, device: "torch.device") -> "torch.Tensor":
    """Tensor preserving NaN for loss masking."""
    return torch.tensor(arr, dtype=torch.float32, device=device)


class DNNModel:
    """Wrapper with pretrain/finetune/fit methods and MC Dropout inference."""

    def __init__(self, config: Optional[dict] = None) -> None:
        if not _TORCH_AVAILABLE:
            raise ImportError("torch is not installed.")
        cfg = (config or {}).get("dnn", {})
        arch = cfg.get("architecture", {})
        train_cfg = cfg.get("training", {})
        mc_cfg = cfg.get("mc_dropout", {})

        self.hidden    = arch.get("hidden_layers", [256, 128, 64, 32])
        self.dropout   = arch.get("dropout_rate", 0.25)
        self.epochs    = train_cfg.get("epochs", 300)
        self.batch_sz  = train_cfg.get("batch_size", 32)
        self.lr        = train_cfg.get("learning_rate", 0.001)
        self.wd        = train_cfg.get("weight_decay", 1e-4)
        self.patience  = train_cfg.get("early_stopping_patience", 30)
        self.grad_clip = train_cfg.get("gradient_clip", 1.0)
        self.mc_passes = mc_cfg.get("n_forward_passes", 50)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[PlastiCreteDNN] = None
        self._n_features: int = 0
        self._config = config

    def _build_model(self, n_features: int) -> "PlastiCreteDNN":
        self._n_features = n_features
        return PlastiCreteDNN(n_features, self.hidden, self.dropout, len(TARGET_COLUMNS)).to(self.device)

    def _run_epoch(
        self,
        loader: "DataLoader",
        optimizer: "torch.optim.Optimizer",
        criterion: "MaskedMSELoss",
        is_train: bool,
    ) -> float:
        self.model.train(is_train)
        total = 0.0
        for X_b, y_b in loader:
            X_b = X_b.to(self.device)
            y_b = y_b.to(self.device)
            pred = self.model(X_b)
            loss = criterion(pred, y_b)
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                optimizer.step()
            total += loss.item() * len(X_b)
        return total

    def _train_loop(
        self,
        X_tr: np.ndarray, y_tr: np.ndarray,
        X_vl: np.ndarray, y_vl: np.ndarray,
        epochs: int, lr: float,
        freeze_blocks: int = 0,
    ) -> None:
        criterion = MaskedMSELoss()
        if freeze_blocks > 0:
            # Each block = Linear, BN, ReLU, Dropout = 4 submodules
            frozen_params: set = set()
            block_idx = 0
            for name, m in self.model.net.named_children():
                if block_idx >= freeze_blocks * 4:
                    break
                for p in m.parameters():
                    p.requires_grad_(False)
                    frozen_params.add(id(p))
                block_idx += 1

        trainable = [p for p in self.model.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(trainable, lr=lr, weight_decay=self.wd)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        X_tr_t = _to_tensor(X_tr, self.device)
        y_tr_t = _nan_tensor(y_tr, self.device)
        X_vl_t = _to_tensor(X_vl, self.device)
        y_vl_t = _nan_tensor(y_vl, self.device)

        train_ds = TensorDataset(X_tr_t, y_tr_t)
        train_dl = DataLoader(train_ds, batch_size=self.batch_sz, shuffle=True)

        best_val  = float("inf")
        best_sd   = None
        no_improve = 0

        for epoch in range(1, epochs + 1):
            self._run_epoch(train_dl, optimizer, criterion, is_train=True)
            scheduler.step()

            self.model.eval()
            with torch.no_grad():
                val_loss = criterion(self.model(X_vl_t), y_vl_t).item()

            if val_loss < best_val - 1e-6:
                best_val   = val_loss
                best_sd    = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= self.patience:
                    logger.info(f"Early stop at epoch {epoch} (best val_loss={best_val:.4f})")
                    break

            if epoch % 20 == 0:
                logger.debug(f"  Epoch {epoch}/{epochs}  val_loss={val_loss:.4f}")

        if best_sd:
            self.model.load_state_dict(best_sd)

        # Unfreeze all for subsequent stages
        for p in self.model.parameters():
            p.requires_grad_(True)

    def pretrain(
        self,
        X_tr: np.ndarray, y_tr: np.ndarray,
        X_vl: np.ndarray, y_vl: np.ndarray,
    ) -> None:
        cfg = (self._config or {}).get("transfer_learning", {})
        pretrain_epochs = cfg.get("pretrain_epochs", 100)
        pretrain_lr     = cfg.get("pretrain_lr", 0.001)
        self.model = self._build_model(X_tr.shape[1])
        logger.info(f"DNN pretrain: {pretrain_epochs} epochs, lr={pretrain_lr}")
        self._train_loop(X_tr, y_tr, X_vl, y_vl, pretrain_epochs, pretrain_lr, freeze_blocks=0)

    def finetune(
        self,
        X_tr: np.ndarray, y_tr: np.ndarray,
        X_vl: np.ndarray, y_vl: np.ndarray,
    ) -> None:
        cfg = (self._config or {}).get("transfer_learning", {})
        finetune_epochs = cfg.get("finetune_epochs", 200)
        finetune_lr     = cfg.get("finetune_lr", 0.0003)
        freeze_until    = cfg.get("freeze_layers_until", 2)
        if self.model is None:
            self.model = self._build_model(X_tr.shape[1])
        logger.info(f"DNN finetune: {finetune_epochs} epochs, lr={finetune_lr}, freeze_blocks={freeze_until}")
        self._train_loop(X_tr, y_tr, X_vl, y_vl, finetune_epochs, finetune_lr, freeze_blocks=freeze_until)

    def fit(
        self,
        X_tr: np.ndarray, y_tr: np.ndarray,
        X_vl: np.ndarray, y_vl: np.ndarray,
    ) -> None:
        self.model = self._build_model(X_tr.shape[1])
        logger.info(f"DNN single-stage fit: {self.epochs} epochs")
        self._train_loop(X_tr, y_tr, X_vl, y_vl, self.epochs, self.lr, freeze_blocks=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            X_t = _to_tensor(X, self.device)
            return self.model(X_t).cpu().numpy()

    def predict_mc_dropout(self, X: np.ndarray, n_passes: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """MC Dropout: keep Dropout layers active, run n_passes forward passes."""
        n = n_passes or self.mc_passes
        self.model.eval()
        self.model.enable_dropout()
        X_t = _to_tensor(X, self.device)
        results = []
        with torch.no_grad():
            for _ in range(n):
                results.append(self.model(X_t).cpu().numpy())
        stacked = np.stack(results)  # (n_passes, n_samples, 7)
        return stacked.mean(axis=0), stacked.std(axis=0)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "n_features": self._n_features,
                "hidden":     self.hidden,
                "dropout":    self.dropout,
                "config":     self._config,
            },
            path,
        )
        logger.info(f"DNN saved â†’ {path}")

    @classmethod
    def load(cls, path: str | Path, config: Optional[dict] = None) -> "DNNModel":
        path = Path(path)
        ck = torch.load(path, map_location="cpu", weights_only=True)
        obj = cls(config or ck.get("config"))
        obj._n_features = ck["n_features"]
        obj.model = PlastiCreteDNN(
            n_features=ck["n_features"],
            hidden=ck.get("hidden", [256, 128, 64, 32]),
            dropout=ck.get("dropout", 0.25),
        ).to(obj.device)
        obj.model.load_state_dict(ck["state_dict"])
        return obj

