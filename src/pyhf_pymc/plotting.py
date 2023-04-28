import numpy as np
from random import randint
import matplotlib.pyplot as plt
import corner
import json

import pytensor
from pytensor import tensor as pt
from pytensor.graph.basic import Apply
from pytensor.graph import Apply, Op
from pytensor.tensor.type import TensorType

import jax
from jax import grad, jit, vmap, value_and_grad, random
import jax.numpy as jnp

import pyhf
pyhf.set_backend('jax')
# pyhf.set_backend('numpy')

import pymc as pm
import arviz as az

from pyhf_pymc import prepare_inference
from pyhf_pymc import make_op

blue = '#1F449C'
orange = '#E57A77'

def prior_posterior_predictives(model, observed, post_pred, prior_pred):

    nBins = len(model.expected_actualdata(model.config.suggested_init()))

    # Build means
    prior_means = []
    post_means = []
    for i in range(nBins):
        prior_means.append(prior_pred.prior_predictive.Expected_Data[0].T[i].mean())
        post_means.append(post_pred.posterior_predictive.Expected_Data[0].T[i].mean())

    # Plot means
    plt.scatter(np.linspace(0,nBins-1,nBins), prior_means, color=orange, label='Prior Predictive')
    plt.scatter(np.linspace(0,nBins-1,nBins), prior_means, color=orange, label='Prior Predictive')

    # Plot samples
    for i in range(nBins):
        plt.scatter(np.full(len(prior_pred.prior_predictive.Expected_Data[0].T[i]), i), prior_pred.prior_predictive.Expected_Data[0].T[i], alpha=0.1, color=orange, linewidths=0)
        plt.scatter(np.full(len(post_pred.posterior_predictive.Expected_Data[0].T[i]), i), post_pred.posterior_predictive.Expected_Data[0].T[i], alpha=0.1, color=blue, linewidths=0)

    # Plot data
    plt.scatter(np.arange(nBins), observed, marker='3', c = 'k',s=200, zorder = 999, label = "Data")

    plt.legend(loc='upper left')
    plt.xticks(np.arange(nBins))
    plt.xlabel('Bins')
    plt.ylabel('Events')

def calibration(prepared_model, prior_pred):

    # Sampling
    model = prepared_model['model']
    expData_op = make_op.make_op(model)
    prior_Normals, prior_Unconstrained, prior_data = np.concatenate(prior_pred.prior.Normals[0]), np.concatenate(prior_pred.prior.Unconstrained[0]), np.array(prior_pred.prior_predictive.Expected_Data[0])

    def posterior_from_prior(prior_data):
            with pm.Model() as m:
                    pars = prepare_inference.priors2pymc(prepared_model)
                    Expected_Data = pm.Poisson("Expected_Data", mu=expData_op(pars), observed=prior_data)
                    
                    step1 = pm.Metropolis()
                    post_data = pm.sample(1, chains=1, step=step1)
                    post_pred = pm.sample_posterior_predictive(post_data)

            return np.concatenate(post_data.posterior.Normals[0]), np.concatenate(post_data.posterior.Unconstrained[0]), np.array(post_pred.posterior_predictive.Expected_Data[0][0])
                
    post_Normals, post_Unconstrained, post_data = [], [], []
    for p_d in prior_data:
        a, b, c = posterior_from_prior(p_d)
        post_Normals.append(a[0])
        post_Unconstrained.append(b[0])
        post_data.append(c[0])

    # Plot Normals
    plt.hist(prior_Normals, 40, alpha = 0.5, color=orange, linewidth=2, label='Prior', edgecolor=orange)
    _, bins, _ = plt.hist(prior_Normals, bins=40, histtype='step', color=orange, alpha=0.000001)
    plt.hist(post_Normals, bins=bins, alpha = 0.5, color=blue, linewidth=2, label='Posterior', edgecolor=blue)
    plt.xlabel('Background')

    plt.legend()

    plt.show()
        
    # Plot Unconstrained 
    plt.hist(prior_Unconstrained, 40, alpha = 0.5, color=orange, linewidth=2, label='Prior', edgecolor=orange)
    _, bins, _ = plt.hist(prior_Unconstrained, bins=40, histtype='step', color=orange, alpha=0.000001)
    plt.hist(post_Unconstrained, bins=bins, alpha = 0.5, color=blue, linewidth=2, label='Posterior', edgecolor=blue)
    plt.xlabel('Signal Strenth')

    plt.legend()

    plt.show()

    return post_Normals, post_Unconstrained, post_data
