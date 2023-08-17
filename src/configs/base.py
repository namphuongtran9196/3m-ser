import logging
import os
from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def save(self):
        pass


class BaseConfig(Base):
    def __init__(self, **kwargs):
        super(BaseConfig, self).__init__(**kwargs)

    def show(self):
        for key, value in self.__dict__.items():
            logging.info(f"{key}: {value}")

    def save(self, opt):
        message = "\n"
        for k, v in sorted(vars(opt).items()):
            message += f"{str(k):>30}: {str(v):<40}\n"

        os.makedirs(os.path.join(opt.checkpoint_dir), exist_ok=True)
        out_opt = os.path.join(opt.checkpoint_dir, "opt.log")
        with open(out_opt, "w") as opt_file:
            opt_file.write(message)
            opt_file.write("\n")

        logging.info(message)


class Config(BaseConfig):
    # Base
    def __init__(self, **kwargs):
        super(Config, self).__init__(**kwargs)
        self.name = "default"
        self.set_args()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_args(self, **kwargs):
        self.num_epochs = 250
        self.checkpoint_dir = "checkpoints"
        self.save_all_states = True
        self.save_best_val = True
        self.max_to_keep = 1
        self.save_freq = 4000
        self.batch_size = 2

        self.loss_type = (
            "CrossEntropyLoss"  # [CrossEntropyLoss, CrossEntropyLoss_ContrastiveCenterLoss, CrossEntropyLoss_CenterLoss]
        )
        self.lambda_c = 1.0  # For CrossEntropyLoss_ContrastiveCenterLoss
        self.feat_dim = 2048  # For CrossEntropyLoss_ContrastiveCenterLoss

        # For combined margin loss
        self.margin_loss_m1 = 1.0
        self.margin_loss_m2 = 0.5
        self.margin_loss_m3 = 0.0
        self.margin_loss_scale = 64.0

        # For focal loss
        self.focal_loss_gamma = 0.5
        self.focal_loss_alpha = None

        # Learning rate
        self.learning_rate = 0.0001
        self.learning_rate_step_size = 30
        self.learning_rate_gamma = 0.1

        # Dataset
        self.data_root = "data/IEMOCAP"
        self.text_max_length = 297
        self.audio_max_length = 546220

        # Model
        self.num_classes = 4
        self.num_attention_head = 8
        self.dropout = 0.5
        self.model_type = "MMSERA"  # [MMSERA, AudioOnly, TextOnly, SERVER]
        self.text_encoder_type = "bert"  # [bert, roberta]
        self.text_encoder_dim = 768
        self.text_unfreeze = False
        self.audio_encoder_type = "panns"  # [vggish, panns, hubert_base, wav2vec2_base, wavlm_base]
        self.audio_encoder_dim = 2048  # 2048 - panns, 128 - vggish, 768 - hubert_base,wav2vec2_base,wavlm_base
        self.audio_norm_type = "layer_norm"  # [layer_norm, min_max, None]
        self.audio_unfreeze = True

        self.fusion_head_output_type = "cls"  # [cls, mean, max]

        self.optim_attributes = None  # For hyperparameter search

        for key, value in kwargs.items():
            setattr(self, key, value)
