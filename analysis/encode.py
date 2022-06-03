import torch, math, einops, numpy as np
from torch.distributions import MultivariateNormal
from torch.autograd.functional import jacobian

class VoxelEncodeBase():
    '''
    Base class for Voxel Encoding Models
    '''

    @staticmethod
    def tuning(stim, pref):
        '''
        Orientation (basis) tuning function
        '''
        stim = einops.repeat(stim, 'n -> n k', k = pref.shape[0])
        nonlinr = torch.cos(math.pi * (stim - pref) / 90.0)
        rectify = torch.maximum(torch.zeros_like(nonlinr), nonlinr)
        resp = torch.pow(rectify, 5)

        return resp

    def __init__(self, n_func=8):
        '''
        n_func: number of basis functions
        '''
        self.pref = torch.arange(0, 180.0, 180.0 / n_func, dtype=torch.float32)
        self.beta = None

    def forward(self, stim):
        '''
        Predict voxel responses given stimulus value
        '''
        if self.beta is None:
            raise Exception("Model weights are not yet estimated")

        stim = torch.tensor(stim, dtype=torch.float32)
        resp = self.tuning(stim, self.pref)
        return (resp @ self.beta).t()

    def ols(self, stim, voxel):
        '''
        Estimate model weights given stimulus and response
        Stage 1: estimate beta weights using least-square

        stim: stimulus value (n_trial)
        voxel: voxel responses of shape (n_voxel, n_trial)
        '''
        stim = torch.tensor(stim, dtype=torch.float32)
        voxel = torch.tensor(voxel, dtype=torch.float32)

        rgs = self.tuning(stim, self.pref)
        self.beta = torch.linalg.solve(rgs.t() @ rgs, rgs.t() @ voxel.t())

        return self.beta

class VoxelEncodeNoise(VoxelEncodeBase):

    def __init__(self, n_func=8):
        '''
        n_func: number of basis functions
        rho: global noise correlation between voxels
        sigma: vector of noise standard deviations
        '''
        super().__init__(n_func)
        self.rho = 0.0
        self.sigma = None
        self.cov = None

    # multivariate normal distribution negative log-likelihood
    def log_llhd(self, x, mu, cov):
        return torch.logdet(cov) + (x - mu).t() @ torch.inverse(cov) @ (x - mu)

    # objective function
    def objective(self, stim, voxel, cov):
        voxel = torch.tensor(voxel, dtype=torch.float32)
        mean_resp = super().forward(stim)

        vals = torch.zeros(voxel.shape[1])
        for idx in range(voxel.shape[1]):
            vals[idx] = self.log_llhd(voxel[:, idx], mean_resp[:, idx], cov)

        return torch.sum(vals) / voxel.shape[1]

    # define the covariance matrix (noise model)
    def cov_mtx(self, rho, sigma):
        return (1 - rho) * torch.diag((sigma ** 2).flatten()) + rho * (sigma @ sigma.t())

    def forward(self, stim):
        # mean response through tuning function
        mean_resp = super().forward(stim)
        sample = torch.zeros_like(mean_resp)

        # sample from multivariate normal distribution
        for idx in range(mean_resp.shape[1]):
            dist = MultivariateNormal(mean_resp[:, idx], self.cov)
            sample[:, idx] = dist.sample()

        return sample

    # estimate noise model
    def mle(self, stim, voxel):
        '''
        Estimate model weights given stimulus and response
        Stage 2: estimate noise covariance matrix using maximum likelihood

        stim: stimulus value (n_trial)
        voxel: voxel responses of shape (n_voxel, n_trial)
        '''
        pass

class VoxelEncode(VoxelEncodeNoise):

    def __init__(self, n_func=8):
        super().__init__(n_func)

# some simple testing routines for model fitting
def ols_test(n_func=8, n_voxel=20, n_trial=50):
    '''
    Test OLS estimation part of VoxelEncode
    '''
    simulate = VoxelEncodeBase()
    simulate.beta = torch.rand(n_func, n_voxel)

    stim_val = np.random.rand(n_trial) * 180.0
    resp = simulate.forward(stim_val)

    estimate = VoxelEncodeBase()
    estimate.ols(stim_val, resp.numpy())

    return simulate, estimate