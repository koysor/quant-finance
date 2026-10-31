"""Unit tests for stochastic process path simulation."""

import numpy as np
import pytest

from quant_finance.stochastic.paths import (
    gbm_paths,
    random_walk_paths,
    wiener_paths,
)

N_PATHS = 200_000


def _rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


def _standard_errors(sample: np.ndarray, expected: float) -> float:
    """Return how many standard errors the sample mean is from the expected value."""
    return abs(sample.mean() - expected) / (sample.std() / np.sqrt(sample.size))


GENERATORS = {
    "gbm": lambda rng: gbm_paths(100.0, 0.05, 0.2, 1.0, 10, 5, rng),
    "wiener": lambda rng: wiener_paths(1.0, 10, 5, rng),
    "random_walk": lambda rng: random_walk_paths(100.0, 0.5, 10, 5, rng),
}


@pytest.mark.parametrize("generate", GENERATORS.values(), ids=GENERATORS.keys())
class TestAllProcesses:
    """Properties shared by every path generator."""

    def test_shape(self, generate):
        assert generate(_rng()).shape == (5, 11)

    def test_same_seed_gives_the_same_paths(self, generate):
        np.testing.assert_array_equal(generate(_rng()), generate(_rng()))

    def test_different_seeds_give_different_paths(self, generate):
        assert not np.array_equal(generate(_rng(1)), generate(_rng(2)))


class TestGbm:
    """Tests for geometric Brownian motion."""

    def test_starts_at_the_initial_price(self):
        assert (gbm_paths(100.0, 0.05, 0.2, 1.0, 10, 5, _rng())[:, 0] == 100.0).all()

    def test_prices_stay_positive(self):
        assert (gbm_paths(100.0, 0.05, 0.8, 1.0, 50, 100, _rng()) > 0).all()

    def test_mean_matches_theory(self):
        final = gbm_paths(100.0, 0.05, 0.2, 1.0, 10, N_PATHS, _rng())[:, -1]
        assert _standard_errors(final, 100.0 * np.exp(0.05)) < 4

    def test_log_return_distribution_matches_theory(self):
        final = gbm_paths(100.0, 0.05, 0.2, 2.0, 10, N_PATHS, _rng())[:, -1]
        log_returns = np.log(final / 100.0)
        assert _standard_errors(log_returns, (0.05 - 0.5 * 0.2**2) * 2.0) < 4
        assert log_returns.var() == pytest.approx(0.2**2 * 2.0, rel=0.02)

    def test_zero_volatility_grows_at_the_drift(self):
        paths = gbm_paths(100.0, 0.05, 0.0, 1.0, 4, 2, _rng())
        np.testing.assert_allclose(paths[:, -1], 100.0 * np.exp(0.05))


class TestWiener:
    """Tests for the Wiener process."""

    def test_starts_at_zero(self):
        assert (wiener_paths(1.0, 10, 5, _rng())[:, 0] == 0.0).all()

    def test_terminal_distribution_matches_theory(self):
        final = wiener_paths(2.0, 10, N_PATHS, _rng())[:, -1]
        assert _standard_errors(final, 0.0) < 4
        assert final.var() == pytest.approx(2.0, rel=0.02)

    def test_variance_grows_linearly_with_time(self):
        paths = wiener_paths(1.0, 10, N_PATHS, _rng())
        assert paths[:, 5].var() == pytest.approx(0.5, rel=0.02)

    def test_increments_are_uncorrelated(self):
        increments = np.diff(wiener_paths(1.0, 10, N_PATHS, _rng()), axis=1)
        correlation = np.corrcoef(increments[:, 0], increments[:, 1])[0, 1]
        assert correlation == pytest.approx(0.0, abs=0.02)


class TestRandomWalk:
    """Tests for the discrete random walk."""

    def test_starts_at_the_initial_value(self):
        assert (random_walk_paths(50.0, 0.5, 10, 5, _rng())[:, 0] == 50.0).all()

    def test_every_step_is_plus_or_minus_one(self):
        steps = np.diff(random_walk_paths(50.0, 0.5, 20, 100, _rng()), axis=1)
        assert set(np.unique(steps)) == {-1.0, 1.0}

    @pytest.mark.parametrize("p", [0.5, 0.6, 0.4])
    def test_mean_drift_matches_theory(self, p):
        final = random_walk_paths(50.0, p, 20, N_PATHS, _rng())[:, -1]
        assert _standard_errors(final, 50.0 + 20 * (2 * p - 1)) < 4

    @pytest.mark.parametrize("p, expected", [(1.0, 60.0), (0.0, 40.0)])
    def test_certain_steps_are_deterministic(self, p, expected):
        assert (random_walk_paths(50.0, p, 10, 3, _rng())[:, -1] == expected).all()
