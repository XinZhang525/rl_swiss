# Imports ---------------------------------------------------------------------
# Python
import argparse
import joblib
import yaml
import os.path as osp
from collections import defaultdict
import joblib

# PyTorch
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch import autograd
from torch.optim import Adam

# NumPy
import numpy as np
from numpy import array
from numpy.random import choice, randint

# Model Building
from gen_models.vrnn import VRNN
from gen_models.vrnn_flat_latent import VRNN as FlatLatentVRNN
from gen_models.flat_vrnn import VRNN as FlatVRNN
from gen_models.flat_net import VRNN as AE
from gen_models.convgru import ConvGRUCell
import rlkit.torch.pytorch_util as ptu

# Data
from gen_models.data_loaders import BasicDataLoader, RandomDataLoader

# Logging
from rlkit.core import logger
from rlkit.launchers.launcher_util import setup_logger, set_seed
from rlkit.core.vistools import generate_gif, save_pytorch_tensor_as_img

import sys

from numpy import pi
from numpy import log as np_log
log_2pi = np_log(2*pi)

LOG_COV_MAX = 2
LOG_COV_MIN = -20


def compute_diag_log_prob(recon_mean, recon_log_cov, obs):
    bs = recon_mean.size(0)
    recon_mean = recon_mean.view(bs, -1)
    recon_log_cov = recon_log_cov.view(bs, -1)
    obs = obs.view(bs, -1)

    recon_cov = torch.exp(recon_log_cov)
    log_prob = -0.5 * torch.sum(
        (recon_mean - obs)**2 / recon_cov
    )
    log_det_temp = torch.sum(recon_log_cov, 1) + log_2pi
    log_prob = log_prob - 0.5 * torch.sum(log_det_temp)

    return log_prob


def experiment(exp_specs):
    ptu.set_gpu_mode(exp_specs['use_gpu'])
    # Set up logging ----------------------------------------------------------
    exp_id = exp_specs['exp_id']
    exp_prefix = exp_specs['exp_name']
    seed = exp_specs['seed']
    set_seed(seed)
    setup_logger(exp_prefix=exp_prefix, exp_id=exp_id, variant=exp_specs)

    # Prep the data -----------------------------------------------------------
    replay_dict = joblib.load(exp_specs['replay_dict_path'])
    next_obs_array = replay_dict['next_observations']
    acts_array = replay_dict['actions']
    data_loader = BasicDataLoader(
        next_obs_array[:40000], acts_array[:40000], exp_specs['episode_length'], exp_specs['batch_size'], use_gpu=ptu.gpu_enabled())
    val_data_loader = BasicDataLoader(
        next_obs_array[40000:], acts_array[40000:], exp_specs['episode_length'], exp_specs['batch_size'], use_gpu=ptu.gpu_enabled())

    # Model Definition --------------------------------------------------------
    conv_channels = 32
    conv_encoder = nn.Sequential(
        nn.Conv2d(3, conv_channels, 4, stride=2, padding=1, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU(),
        nn.Conv2d(conv_channels, conv_channels, 4, stride=2, padding=1, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU()
    )
    gru_channels = 128
    inter_h = 5
    act_channels = 4
    act_proc = nn.Linear(4, act_channels * inter_h * inter_h, bias=True)
    pre_gru_conv = nn.Sequential(
        nn.Conv2d(act_channels + conv_channels, conv_channels, 3, stride=1, padding=1, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU(),
    )
    gru = ConvGRUCell(conv_channels, gru_channels, 3)
    post_gru_conv = nn.Sequential(
        nn.Conv2d(act_channels + gru_channels, conv_channels, 3, stride=1, padding=1, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU(),
    )
    conv_decoder = nn.Sequential(
        nn.ConvTranspose2d(conv_channels, conv_channels, 4, stride=2, padding=1, output_padding=0, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU(),
        # nn.Conv2d(conv_channels, conv_channels, 3, stride=1, padding=1, bias=False),
        # nn.BatchNorm2d(conv_channels),
        # nn.ReLU(),
        nn.ConvTranspose2d(conv_channels, conv_channels, 4, stride=2, padding=1, output_padding=0, bias=False),
        nn.BatchNorm2d(conv_channels),
        nn.ReLU(),
        # nn.Conv2d(conv_channels, conv_channels, 3, stride=1, padding=1, bias=False),
        # nn.BatchNorm2d(conv_channels),
        # nn.ReLU(),
    )
    mean_decoder = nn.Sequential(
        nn.Conv2d(conv_channels, 3, 1, stride=1, padding=0, bias=True),
        nn.Sigmoid()
    )
    log_cov_decoder = nn.Sequential(
        nn.Conv2d(conv_channels, 3, 1, stride=1, padding=0, bias=True),
    )
    if ptu.gpu_enabled():
        conv_encoder.cuda()
        pre_gru_conv.cuda()
        gru.cuda()
        post_gru_conv.cuda()
        conv_decoder.cuda()
        mean_decoder.cuda()
        log_cov_decoder.cuda()
        act_proc.cuda()

    # Optimizer ---------------------------------------------------------------
    model_optim = Adam(
        [
            item for sublist in
            map(
                lambda x: list(x.parameters()),
                [conv_encoder, pre_gru_conv, gru, post_gru_conv, conv_decoder, mean_decoder, log_cov_decoder]
            )
            for item in sublist
        ],
        lr=float(exp_specs['model_lr']),
        weight_decay=float(exp_specs['model_wd'])
    )

    # -------------------------------------------------------------------------
    freq_bptt = exp_specs['freq_bptt']
    episode_length = exp_specs['episode_length']
    losses = []
    for iter_num in range(int(float(exp_specs['max_iters']))):
        if iter_num % freq_bptt == 0:
            if iter_num > 0:
                # loss = loss / freq_bptt
                loss.backward()
                model_optim.step()
                prev_h_batch = prev_h_batch.detach()
            loss = 0
        if iter_num % episode_length == 0:
            prev_h_batch = Variable(torch.zeros(exp_specs['batch_size'], gru_channels, inter_h, inter_h))
            if ptu.gpu_enabled():
                prev_h_batch = prev_h_batch.cuda()
            
            train_loss_print = '\t'.join(losses)
            losses = []

        obs_batch, act_batch = data_loader.get_next_batch()
        act_batch = act_proc(act_batch).view(act_batch.size(0), act_channels, inter_h, inter_h)
        
        hidden = post_gru_conv(torch.cat([prev_h_batch, act_batch], 1))
        hidden = conv_decoder(hidden)
        recon = mean_decoder(hidden)
        log_cov = log_cov_decoder(hidden)
        log_cov = torch.clamp(log_cov, LOG_COV_MIN, LOG_COV_MAX)

        enc = conv_encoder(obs_batch)
        enc = pre_gru_conv(torch.cat([enc, act_batch], 1))
        prev_h_batch = gru(enc, prev_h_batch)

        losses.append('%.4f' % ((obs_batch - recon)**2).mean())
        if iter_num % episode_length != 0:
            loss = loss + ((obs_batch - recon)**2).sum()/float(exp_specs['batch_size'])
            # loss = loss + compute_diag_log_prob(recon, log_cov, obs_batch)/float(exp_specs['batch_size'])

        if iter_num % (500*episode_length) in range(2*episode_length):
            save_pytorch_tensor_as_img(recon[0].data.cpu(), 'junk_vis/conv_gru_pogrid_len_8_scale_4/rnn_recon_%d.png' % iter_num)
            save_pytorch_tensor_as_img(obs_batch[0].data.cpu(), 'junk_vis/conv_gru_pogrid_len_8_scale_4/rnn_obs_%d.png' % iter_num)

        if iter_num % exp_specs['freq_val'] == 0:
            print('\nValidating Iter %d...' % iter_num)
            list(map(lambda x: x.eval(), [conv_encoder, pre_gru_conv, gru, post_gru_conv, conv_decoder, mean_decoder, log_cov_decoder, act_proc]))

            val_prev_h_batch = Variable(torch.zeros(exp_specs['batch_size'], gru_channels, inter_h, inter_h))
            if ptu.gpu_enabled():
                val_prev_h_batch = val_prev_h_batch.cuda()

            losses = []            
            for i in range(episode_length):
                obs_batch, act_batch = val_data_loader.get_next_batch()
                act_batch = act_proc(act_batch).view(act_batch.size(0), act_channels, inter_h, inter_h)
                
                hidden = post_gru_conv(torch.cat([val_prev_h_batch, act_batch], 1))
                hidden = conv_decoder(hidden)
                recon = mean_decoder(hidden)
                log_cov = log_cov_decoder(hidden)
                log_cov = torch.clamp(log_cov, LOG_COV_MIN, LOG_COV_MAX)

                enc = conv_encoder(obs_batch)
                enc = pre_gru_conv(torch.cat([enc, act_batch], 1))
                val_prev_h_batch = gru(enc, val_prev_h_batch)

                # val_loss = compute_diag_log_prob(recon, log_cov, obs_batch)/float(exp_specs['batch_size'])
                losses.append('%.4f' % ((obs_batch - recon)**2).mean())

            loss_print = '\t'.join(losses)
            print('Val MSE:\t' + loss_print)
            print('Train MSE:\t' + train_loss_print)

            list(map(lambda x: x.train(), [conv_encoder, pre_gru_conv, gru, post_gru_conv, conv_decoder, mean_decoder, log_cov_decoder, act_proc]))


if __name__ == '__main__':
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--experiment', help='experiment specification file')
    args = parser.parse_args()
    with open(args.experiment, 'r') as spec_file:
        spec_string = spec_file.read()
        exp_specs = yaml.load(spec_string)
    
    experiment(exp_specs)
