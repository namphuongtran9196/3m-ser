import logging
import os
import sys

lib_path = os.path.abspath("").replace("scripts", "src")
sys.path.append(lib_path)

import argparse
import datetime
import random

import numpy as np
import torch
from torch import nn, optim

import trainer as Trainer
from configs.base import Config
from data.dataloader import build_train_test_dataset
from models import losses, networks
from utils.configs import get_options
from utils.torch.callbacks import CheckpointsCallback

SEED = 0
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main(cfg: Config):
    logging.info("Initializing model...")
    # Model
    try:
        network = getattr(networks, cfg.model_type)(cfg)
        network.to(device)
    except AttributeError:
        raise NotImplementedError("Model {} is not implemented".format(cfg.model_type))

    logging.info("Initializing checkpoint directory and dataset...")
    # Preapre the checkpoint directory
    cfg.checkpoint_dir = checkpoint_dir = os.path.join(
        os.path.abspath(cfg.checkpoint_dir),
        cfg.name,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
    )
    log_dir = os.path.join(checkpoint_dir, "logs")
    weight_dir = os.path.join(checkpoint_dir, "weights")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(weight_dir, exist_ok=True)
    cfg.save(cfg)

    # Build dataset
    encoder_model = None
    if cfg.encode_data:
        network.embed_input = True
        encoder_model = network
    train_ds, test_ds = build_train_test_dataset(cfg, encoder_model)

    logging.info("Initializing trainer...")
    try:
        criterion = getattr(losses, cfg.loss_type)(cfg)
        criterion.to(device)
    except AttributeError:
        raise NotImplementedError("Loss {} is not implemented".format(cfg.loss_type))
    try:
        trainer = getattr(Trainer, cfg.trainer)(
            cfg=cfg,
            network=network,
            criterion=criterion,
            log_dir=cfg.checkpoint_dir,
        )
    except AttributeError:
        raise NotImplementedError("Trainer {} is not implemented".format(cfg.trainer))

    logging.info("Start training...")

    # Build optimizer and criterion
    optimizer = optim.Adam(
        params=trainer.network.parameters(),
        lr=cfg.learning_rate,
        betas=(cfg.adam_beta_1, cfg.adam_beta_2),
        eps=cfg.adam_eps,
        weight_decay=cfg.adam_weight_decay,
    )

    lr_scheduler = None
    if cfg.learning_rate_step_size is not None:
        lr_scheduler = optim.lr_scheduler.StepLR(
            optimizer,
            step_size=cfg.learning_rate_step_size,
            gamma=cfg.learning_rate_gamma,
        )

    ckpt_callback = CheckpointsCallback(
        checkpoint_dir=weight_dir,
        save_freq=cfg.save_freq,
        max_to_keep=cfg.max_to_keep,
        save_best_val=cfg.save_best_val,
        save_all_states=cfg.save_all_states,
    )
    trainer.compile(optimizer=optimizer, scheduler=lr_scheduler)
    if cfg.resume:
        trainer.load_all_states(cfg.resume_path)
    trainer.fit(train_ds, cfg.num_epochs, test_ds, callbacks=[ckpt_callback])


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", "--config", type=str, default="../src/configs/base.py")
    return parser.parse_args()


if __name__ == "__main__":
    args = arg_parser()
    cfg: Config = get_options(args.config)
    if cfg.resume and cfg.cfg_path is not None:
        resume = cfg.resume
        resume_path = cfg.resume_path
        cfg.load(cfg.cfg_path)
        cfg.resume = resume
        cfg.resume_path = resume_path

    main(cfg)
