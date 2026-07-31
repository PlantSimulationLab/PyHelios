"""
W4 -- Action-conditioned latent dynamics model (DreamerV3 / RSSM family).

Runs in the `gsplat` conda env (torch 2.7.0+cu128). **This file must never import
pyhelios** -- the two-env split means data on disk is the only interface.

## Architecture

    encoder            RGB-D (4,H,W) -> embed
    RSSM
      recurrent        h_t   = GRU(h_{t-1}, MLP([z_{t-1}, a_{t-1}]))
      prior            p(z_t | h_t)          32 categoricals x 32 classes
      posterior        q(z_t | h_t, e_t)     same shape
    decoder heads      [h_t, z_t] ->
                         rgb        (3,H,W)   MSE on [-0.5, 0.5]
                         depth      (1,H,W)   MSE on symlog metres
                         semantic   (7,H,W)   cross-entropy over 7 classes
                         fruit_vis  ()        MSE on symlog(fruit pixel fraction * 1e3)

## DreamerV3 details that are actually implemented (not just named)

- **Discrete latents with straight-through gradients** and **unimix**: the
  categorical is mixed with 1% uniform, which stops the posterior collapsing to a
  deterministic one-hot early in training and keeps the KL finite.
- **KL balancing**: the dynamics loss (train prior toward posterior) and the
  representation loss (train posterior toward prior) are computed separately with
  stop-gradients, weighted 0.5 / 0.1.
- **Free bits**: each of the two KL terms is clipped below at 1.0 nat, so the
  model is not penalised for the last scraps of KL and does not posterior-collapse.
- **symlog** targets for depth and the fruit-visibility scalar. RGB is already
  bounded so it is left in linear [-0.5, 0.5].

## Deliberate omissions, and why

- **No actor/critic, no reward head, no imagination-trained policy.** The plan's
  goal is the *world model* and its multi-step imagination quality (W6), not
  control. There is no reward function defined for this orchard, so a critic would
  be fitting noise.
- **No RSSM "observe with mixed prior/posterior" schedule** beyond standard
  teacher forcing; open-loop rollout is done explicitly at evaluation time by
  feeding the prior forward.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

N_SEMANTIC_CLASSES = 7   # 0 other, 1 fruit, 2 leaf, 3 shoot, 4 petiole, 5 peduncle, 6 sky


# ---------------------------------------------------------------------------
def symlog(x):
    return torch.sign(x) * torch.log1p(torch.abs(x))


def symexp(x):
    return torch.sign(x) * torch.expm1(torch.abs(x))


class Encoder(nn.Module):
    """Strided conv stack over RGB-D. `depth` (levels) chosen so H,W -> 4x4."""

    def __init__(self, in_channels=4, base=32, image_size=64):
        super().__init__()
        n_levels = int(np.log2(image_size)) - 2   # 64 -> 4 levels, 128 -> 5
        chans = [base * (2 ** i) for i in range(n_levels)]
        layers, c_in = [], in_channels
        for c in chans:
            layers += [nn.Conv2d(c_in, c, 4, stride=2, padding=1),
                       nn.GroupNorm(min(8, c), c), nn.SiLU()]
            c_in = c
        self.net = nn.Sequential(*layers)
        self.out_channels = c_in
        self.out_hw = image_size // (2 ** n_levels)
        self.embed_dim = self.out_channels * self.out_hw * self.out_hw

    def forward(self, x):
        return self.net(x).flatten(1)


class Decoder(nn.Module):
    """Transposed-conv stack producing all image heads from one trunk."""

    def __init__(self, feat_dim, base=32, image_size=64, out_channels=3 + 1 + N_SEMANTIC_CLASSES):
        super().__init__()
        n_levels = int(np.log2(image_size)) - 2
        chans = [base * (2 ** i) for i in range(n_levels)][::-1]
        self.start_hw = image_size // (2 ** n_levels)
        self.start_c = chans[0]
        self.fc = nn.Linear(feat_dim, self.start_c * self.start_hw * self.start_hw)
        layers, c_in = [], self.start_c
        for c in chans[1:]:
            layers += [nn.ConvTranspose2d(c_in, c, 4, stride=2, padding=1),
                       nn.GroupNorm(min(8, c), c), nn.SiLU()]
            c_in = c
        layers += [nn.ConvTranspose2d(c_in, out_channels, 4, stride=2, padding=1)]
        self.net = nn.Sequential(*layers)

    def forward(self, f):
        x = self.fc(f).view(-1, self.start_c, self.start_hw, self.start_hw)
        return self.net(x)


class RSSM(nn.Module):
    def __init__(self, action_dim, deter=512, stoch=32, classes=32, hidden=512, unimix=0.01):
        super().__init__()
        self.deter, self.stoch, self.classes = deter, stoch, classes
        self.stoch_dim = stoch * classes
        self.unimix = unimix

        self.in_proj = nn.Sequential(nn.Linear(self.stoch_dim + action_dim, hidden), nn.SiLU())
        self.gru = nn.GRUCell(hidden, deter)
        self.prior_net = nn.Sequential(nn.Linear(deter, hidden), nn.SiLU(),
                                       nn.Linear(hidden, self.stoch_dim))
        self.post_net = None  # built lazily once embed_dim is known
        self._hidden = hidden

    def build_posterior(self, embed_dim):
        self.post_net = nn.Sequential(nn.Linear(self.deter + embed_dim, self._hidden), nn.SiLU(),
                                      nn.Linear(self._hidden, self.stoch_dim))

    # -- distributions -------------------------------------------------------
    def _dist(self, logits):
        logits = logits.view(*logits.shape[:-1], self.stoch, self.classes)
        probs = F.softmax(logits, dim=-1)
        probs = (1.0 - self.unimix) * probs + self.unimix / self.classes
        return torch.distributions.Independent(
            torch.distributions.OneHotCategoricalStraightThrough(probs=probs), 1)

    def initial(self, batch, device):
        return (torch.zeros(batch, self.deter, device=device),
                torch.zeros(batch, self.stoch_dim, device=device))

    # -- one step ------------------------------------------------------------
    def img_step(self, h, z, a):
        """Prior step: no observation. Returns (h_next, prior_logits)."""
        x = self.in_proj(torch.cat([z, a], dim=-1))
        h = self.gru(x, h)
        return h, self.prior_net(h)

    def obs_step(self, h, z, a, embed):
        """Posterior step. Returns (h_next, prior_logits, post_logits)."""
        h, prior_logits = self.img_step(h, z, a)
        post_logits = self.post_net(torch.cat([h, embed], dim=-1))
        return h, prior_logits, post_logits

    def sample(self, logits):
        d = self._dist(logits)
        return d.rsample().flatten(-2)

    def kl_terms(self, post_logits, prior_logits, free_bits=1.0):
        """Returns (dyn_loss, rep_loss) with DreamerV3's stop-gradient split."""
        post = self._dist(post_logits)
        prior = self._dist(prior_logits)
        post_sg = self._dist(post_logits.detach())
        prior_sg = self._dist(prior_logits.detach())
        dyn = torch.distributions.kl_divergence(post_sg, prior)
        rep = torch.distributions.kl_divergence(post, prior_sg)
        dyn = torch.clamp(dyn, min=free_bits)
        rep = torch.clamp(rep, min=free_bits)
        return dyn.mean(), rep.mean()


class WorldModel(nn.Module):
    def __init__(self, action_dim=5, image_size=64, base=32, deter=512, stoch=32,
                 classes=32, hidden=512, free_bits=1.0, kl_dyn=0.5, kl_rep=0.1,
                 w_rgb=1.0, w_depth=1.0, w_semantic=1.0, w_fruit=1.0):
        super().__init__()
        self.image_size = image_size
        self.action_dim = action_dim
        self.free_bits, self.kl_dyn, self.kl_rep = free_bits, kl_dyn, kl_rep
        self.w = {"rgb": w_rgb, "depth": w_depth, "semantic": w_semantic, "fruit": w_fruit}

        self.encoder = Encoder(4, base, image_size)
        self.rssm = RSSM(action_dim, deter, stoch, classes, hidden)
        self.rssm.build_posterior(self.encoder.embed_dim)
        feat_dim = deter + stoch * classes
        self.decoder = Decoder(feat_dim, base, image_size)
        self.fruit_head = nn.Sequential(nn.Linear(feat_dim, hidden), nn.SiLU(),
                                        nn.Linear(hidden, 1))

    # -- observation preprocessing ------------------------------------------
    @staticmethod
    def preprocess(batch, device):
        """dict of numpy/torch -> model inputs on `device`.

        rgb   uint8   (B,T,H,W,3) -> float (B,T,3,H,W) in [-0.5, 0.5]
        depth float   (B,T,H,W)   -> symlog metres, sky (-1) mapped to 0 and
                                      flagged by the semantic sky class instead
        """
        def t(x, dtype=torch.float32):
            return (x if torch.is_tensor(x) else torch.from_numpy(np.asarray(x))).to(device, dtype)

        rgb = t(batch["rgb"]).permute(0, 1, 4, 2, 3) / 255.0 - 0.5
        depth = t(batch["depth"])
        sky = depth < 0
        depth = torch.where(sky, torch.zeros_like(depth), depth)
        depth_sl = symlog(depth).unsqueeze(2)
        obs = torch.cat([rgb, depth_sl], dim=2)
        out = {"obs": obs, "rgb": rgb, "depth_symlog": depth_sl.squeeze(2),
               "sky": sky}
        if "semantic" in batch:
            sem = t(batch["semantic"], torch.long)
            out["semantic"] = sem
        if "action" in batch:
            out["action"] = t(batch["action"])
        if "fruit_vis" in batch:
            # x100 puts a realistic fruit pixel fraction (~0.04) at symlog(4)=1.6
            # instead of symlog(40)=3.7, so this head starts on the same loss
            # scale as the image heads rather than dominating them.
            out["fruit_vis"] = symlog(t(batch["fruit_vis"]) * 100.0)
        return out

    # -- rollout -------------------------------------------------------------
    def observe(self, obs, actions):
        """Teacher-forced posterior rollout.

        obs      (B,T,4,H,W)
        actions  (B,T,A)  -- actions[t] is the action taken AT step t leading to t+1;
                             the RSSM at step t consumes actions[t-1] (zeros at t=0).
        Returns dict of (B,T,...) tensors.
        """
        B, T = obs.shape[:2]
        embed = self.encoder(obs.reshape(B * T, *obs.shape[2:])).view(B, T, -1)
        h, z = self.rssm.initial(B, obs.device)
        hs, zs, priors, posts = [], [], [], []
        zero_a = torch.zeros(B, self.action_dim, device=obs.device)
        for t in range(T):
            a = zero_a if t == 0 else actions[:, t - 1]
            h, prior_l, post_l = self.rssm.obs_step(h, z, a, embed[:, t])
            z = self.rssm.sample(post_l)
            hs.append(h); zs.append(z); priors.append(prior_l); posts.append(post_l)
        return {"h": torch.stack(hs, 1), "z": torch.stack(zs, 1),
                "prior_logits": torch.stack(priors, 1),
                "post_logits": torch.stack(posts, 1)}

    def imagine(self, h, z, actions):
        """Open-loop prior rollout from a starting (h, z). actions (B,K,A).
        Returns h,z of shape (B,K,...) -- the states AFTER each action."""
        hs, zs = [], []
        for k in range(actions.shape[1]):
            h, prior_l = self.rssm.img_step(h, z, actions[:, k])
            z = self.rssm.sample(prior_l)
            hs.append(h); zs.append(z)
        return torch.stack(hs, 1), torch.stack(zs, 1)

    def decode(self, h, z):
        """(B,T,·) -> per-head predictions, same leading dims."""
        B, T = h.shape[:2]
        feat = torch.cat([h, z], dim=-1)
        flat = feat.reshape(B * T, -1)
        img = self.decoder(flat)
        S = self.image_size
        rgb = img[:, 0:3].view(B, T, 3, S, S)
        depth = img[:, 3:4].view(B, T, S, S)
        sem = img[:, 4:4 + N_SEMANTIC_CLASSES].view(B, T, N_SEMANTIC_CLASSES, S, S)
        fruit = self.fruit_head(flat).view(B, T)
        return {"rgb": rgb, "depth_symlog": depth, "semantic_logits": sem, "fruit_vis": fruit}

    # -- loss ----------------------------------------------------------------
    def loss(self, data):
        """`data` is the output of `preprocess` (with semantic, action, fruit_vis)."""
        state = self.observe(data["obs"], data["action"])
        pred = self.decode(state["h"], state["z"])

        l_rgb = F.mse_loss(pred["rgb"], data["rgb"])
        l_depth = F.mse_loss(pred["depth_symlog"], data["depth_symlog"])
        B, T = data["semantic"].shape[:2]
        l_sem = F.cross_entropy(
            pred["semantic_logits"].reshape(B * T, N_SEMANTIC_CLASSES, self.image_size, self.image_size),
            data["semantic"].reshape(B * T, self.image_size, self.image_size))
        l_fruit = F.mse_loss(pred["fruit_vis"], data["fruit_vis"])

        dyn, rep = self.rssm.kl_terms(state["post_logits"], state["prior_logits"], self.free_bits)

        total = (self.w["rgb"] * l_rgb + self.w["depth"] * l_depth
                 + self.w["semantic"] * l_sem + self.w["fruit"] * l_fruit
                 + self.kl_dyn * dyn + self.kl_rep * rep)
        metrics = {"loss": total.detach(), "rgb": l_rgb.detach(), "depth": l_depth.detach(),
                   "semantic": l_sem.detach(), "fruit": l_fruit.detach(),
                   "kl_dyn": dyn.detach(), "kl_rep": rep.detach()}
        return total, metrics, state, pred


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
