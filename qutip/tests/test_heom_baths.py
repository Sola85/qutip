"""
Tests for qutip.nonmarkov.heom_baths.
"""

import numpy as np
import pytest

from qutip import isequal, spre, spost, sigmax, sigmaz
from qutip.nonmarkov.heom_baths import (
    BathExponent,
    Bath,
    BosonicBath,
    DrudeLorentzBath,
    DrudeLorentzPadeBath,
    FermionicBath,
)


def check_exponent(
    exp, type, dim, Q, ck, vk, ck2=None, sigma_bar_k_offset=None, tag=None,
):
    """ Check the attributes of a BathExponent. """
    assert exp.type is BathExponent.types[type]
    assert exp.dim == dim
    assert exp.Q == Q
    assert exp.ck == ck
    assert exp.vk == vk
    assert exp.ck2 == ck2
    assert exp.sigma_bar_k_offset == sigma_bar_k_offset
    assert exp.tag == tag


class TestBathExponent:
    def test_create(self):
        exp_r = BathExponent("R", None, Q=None, ck=1.0, vk=2.0)
        check_exponent(exp_r, "R", None, Q=None, ck=1.0, vk=2.0)

        exp_i = BathExponent("I", None, Q=None, ck=1.0, vk=2.0)
        check_exponent(exp_i, "I", None, Q=None, ck=1.0, vk=2.0)

        exp_ri = BathExponent("RI", None, Q=None, ck=1.0, vk=2.0, ck2=3.0)
        check_exponent(exp_ri, "RI", None, Q=None, ck=1.0, vk=2.0, ck2=3.0)

        exp_p = BathExponent(
            "+", 2, Q=None, ck=1.0, vk=2.0, sigma_bar_k_offset=-1,
        )
        check_exponent(
            exp_p, "+", 2, Q=None, ck=1.0, vk=2.0, sigma_bar_k_offset=-1,
        )

        exp_m = BathExponent(
            "-", 2, Q=None, ck=1.0, vk=2.0, sigma_bar_k_offset=+1,
        )
        check_exponent(
            exp_m, "-", 2, Q=None, ck=1.0, vk=2.0, sigma_bar_k_offset=+1,
        )

        exp_tag = BathExponent("R", None, Q=None, ck=1.0, vk=2.0, tag="tag1")
        check_exponent(exp_tag, "R", None, Q=None, ck=1.0, vk=2.0, tag="tag1")

        for exp_type, kw in [
            ("R", {}),
            ("I", {}),
            ("+", {"sigma_bar_k_offset": 1}),
            ("-", {"sigma_bar_k_offset": -1}),
        ]:
            with pytest.raises(ValueError) as err:
                BathExponent(
                    exp_type, None, Q=None, ck=1.0, vk=2.0, ck2=3.0, **kw,
                )
            assert str(err.value) == (
                "Second co-efficient (ck2) should only be specified for RI"
                " bath exponents"
            )

        for exp_type, kw in [("R", {}), ("I", {}), ("RI", {"ck2": 3.0})]:
            with pytest.raises(ValueError) as err:
                BathExponent(
                    exp_type, None, Q=None, ck=1.0, vk=2.0,
                    sigma_bar_k_offset=1, **kw,
                )
            assert str(err.value) == (
                "Offset of sigma bar (sigma_bar_k_offset) should only be"
                " specified for + and - bath exponents"
            )

    def test_repr(self):
        exp1 = BathExponent("R", None, Q=sigmax(), ck=1.0, vk=2.0)
        assert repr(exp1) == (
            "<BathExponent type=R dim=None Q.dims=[[2], [2]]"
            " ck=1.0 vk=2.0 ck2=None"
            " sigma_bar_k_offset=None tag=None>"
        )
        exp2 = BathExponent(
            "+", None, Q=None, ck=1.0, vk=2.0, sigma_bar_k_offset=-1,
            tag="bath1",
        )
        assert repr(exp2) == (
            "<BathExponent type=+ dim=None Q.dims=None"
            " ck=1.0 vk=2.0 ck2=None"
            " sigma_bar_k_offset=-1 tag='bath1'>"
        )


class TestBath:
    def test_create(self):
        exp_r = BathExponent("R", None, Q=None, ck=1.0, vk=2.0)
        exp_i = BathExponent("I", None, Q=None, ck=1.0, vk=2.0)
        bath = Bath([exp_r, exp_i])
        assert bath.exponents == [exp_r, exp_i]


class TestBosonicBath:
    def test_create(self):
        Q = sigmaz()
        bath = BosonicBath(Q, [1.], [0.5], [2.], [0.6])
        exp_r, exp_i = bath.exponents
        check_exponent(exp_r, "R", dim=None, Q=Q, ck=1.0, vk=0.5)
        check_exponent(exp_i, "I", dim=None, Q=Q, ck=2.0, vk=0.6)

        bath = BosonicBath(Q, [1.], [0.5], [2.], [0.5])
        [exp_ri] = bath.exponents
        check_exponent(exp_ri, "RI", dim=None, Q=Q, ck=1.0, vk=0.5, ck2=2.0)

        bath = BosonicBath(Q, [1.], [0.5], [2.], [0.6], tag="bath1")
        exp_r, exp_i = bath.exponents
        check_exponent(exp_r, "R", dim=None, Q=Q, ck=1.0, vk=0.5, tag="bath1")
        check_exponent(exp_i, "I", dim=None, Q=Q, ck=2.0, vk=0.6, tag="bath1")

        with pytest.raises(ValueError) as err:
            BosonicBath("not-a-qobj", [1.], [0.5], [2.], [0.6])
        assert str(err.value) == "The coupling operator Q must be a Qobj."

        with pytest.raises(ValueError) as err:
            BosonicBath(Q, [1.], [], [2.], [0.6])
        assert str(err.value) == (
            "The bath exponent lists ck_real and vk_real, and ck_imag and"
            " vk_imag must be the same length."
        )

        with pytest.raises(ValueError) as err:
            BosonicBath(Q, [1.], [0.5], [2.], [])
        assert str(err.value) == (
            "The bath exponent lists ck_real and vk_real, and ck_imag and"
            " vk_imag must be the same length."
        )

    def test_combine(self):
        exp_ix = BathExponent("I", None, Q=sigmax(), ck=2.0, vk=0.5)
        exp_rx = BathExponent("R", None, Q=sigmax(), ck=1.0, vk=0.5)
        exp_rix = BathExponent("RI", None, Q=sigmax(), ck=0.1, vk=0.5, ck2=0.2)
        exp_rz = BathExponent("R", None, Q=sigmaz(), ck=1.0, vk=0.5)

        [exp] = BosonicBath.combine([exp_rx, exp_rx])
        check_exponent(exp, "R", dim=None, Q=sigmax(), ck=2.0, vk=0.5)

        [exp] = BosonicBath.combine([exp_ix, exp_ix])
        check_exponent(exp, "I", dim=None, Q=sigmax(), ck=4.0, vk=0.5)

        [exp] = BosonicBath.combine([exp_rix, exp_rix])
        check_exponent(
            exp, "RI", dim=None, Q=sigmax(), ck=0.2, vk=0.5, ck2=0.4,
        )

        [exp1, exp2] = BosonicBath.combine([exp_rx, exp_rz])
        check_exponent(exp1, "R", dim=None, Q=sigmax(), ck=1.0, vk=0.5)
        check_exponent(exp2, "R", dim=None, Q=sigmaz(), ck=1.0, vk=0.5)

        [exp] = BosonicBath.combine([exp_rx, exp_ix])
        check_exponent(
            exp, "RI", dim=None, Q=sigmax(), ck=1.0, vk=0.5, ck2=2.0,
        )

        [exp] = BosonicBath.combine([exp_rx, exp_ix, exp_rix])
        check_exponent(
            exp, "RI", dim=None, Q=sigmax(), ck=1.1, vk=0.5, ck2=2.2,
        )


class TestDrudeLorentzBath:
    def test_create(self):
        Q = sigmaz()
        ck_real = [0.05262168274189053, 0.0007958201977617107]
        vk_real = [0.05, 6.613879270715354]
        ck_imag = [-0.0012500000000000002]
        vk_imag = [0.05]

        bath = DrudeLorentzBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, tag="bath1",
        )
        [exp1, exp2] = bath.exponents
        check_exponent(
            exp1, "RI", dim=None, Q=Q,
            ck=ck_real[0], vk=vk_real[0], ck2=ck_imag[0],
            tag="bath1",
        )
        check_exponent(
            exp2, "R", dim=None, Q=Q,
            ck=ck_real[1], vk=vk_real[1],
            tag="bath1",
        )
        assert bath.delta is None
        assert bath.terminator is None

        bath = DrudeLorentzBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, combine=False,
        )
        [exp1, exp2, exp3] = bath.exponents
        check_exponent(exp1, "R", dim=None, Q=Q, ck=ck_real[0], vk=vk_real[0])
        check_exponent(exp2, "R", dim=None, Q=Q, ck=ck_real[1], vk=vk_real[1])
        check_exponent(exp3, "I", dim=None, Q=Q, ck=ck_imag[0], vk=vk_imag[0])

        bath = DrudeLorentzBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, terminator=True,
        )
        bath2 = DrudeLorentzBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, terminator=True,
            combine=False,
        )
        op = -2*spre(Q)*spost(Q.dag()) + spre(Q.dag()*Q) + spost(Q.dag()*Q)

        assert np.abs(bath.delta - (0.00031039 / 4.0)) < 1e-8
        assert np.abs(bath2.delta - (0.00031039 / 4.0)) < 1e-8

        assert isequal(bath.terminator, - (0.00031039 / 4.0) * op, tol=1e-8)
        assert isequal(bath2.terminator, - (0.00031039 / 4.0) * op, tol=1e-8)


class TestDrudeLorentzPadeBath:
    def test_create(self):
        Q = sigmaz()
        ck_real = [0.05262168274189053, 0.0016138037466648136]
        vk_real = [0.05, 8.153649149910352]
        ck_imag = [-0.0012500000000000002]
        vk_imag = [0.05]

        bath = DrudeLorentzPadeBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, tag="bath1",
        )
        [exp1, exp2] = bath.exponents
        check_exponent(
            exp1, "RI", dim=None, Q=Q,
            ck=ck_real[0], vk=vk_real[0], ck2=ck_imag[0],
            tag="bath1",
        )
        check_exponent(
            exp2, "R", dim=None, Q=Q,
            ck=ck_real[1], vk=vk_real[1],
            tag="bath1",
        )

        bath = DrudeLorentzPadeBath(
            Q=Q, lam=0.025, T=1 / 0.95, Nk=1, gamma=0.05, combine=False,
        )
        [exp1, exp2, exp3] = bath.exponents
        check_exponent(exp1, "R", dim=None, Q=Q, ck=ck_real[0], vk=vk_real[0])
        check_exponent(exp2, "R", dim=None, Q=Q, ck=ck_real[1], vk=vk_real[1])
        check_exponent(exp3, "I", dim=None, Q=Q, ck=ck_imag[0], vk=vk_imag[0])


class TestFermionicBath:
    def test_create(self):
        Q = sigmaz()
        bath = FermionicBath(Q, [1.], [0.5], [2.], [0.6])
        exp_p, exp_m = bath.exponents
        check_exponent(
            exp_p, "+", dim=2, Q=Q, ck=1.0, vk=0.5, sigma_bar_k_offset=1,
        )
        check_exponent(
            exp_m, "-", dim=2, Q=Q, ck=2.0, vk=0.6, sigma_bar_k_offset=-1,
        )

        bath = FermionicBath(Q, [1.], [0.5], [2.], [0.6], tag="bath1")
        exp_p, exp_m = bath.exponents
        check_exponent(
            exp_p, "+", dim=2, Q=Q, ck=1.0, vk=0.5, sigma_bar_k_offset=1,
            tag="bath1",
        )
        check_exponent(
            exp_m, "-", dim=2, Q=Q, ck=2.0, vk=0.6, sigma_bar_k_offset=-1,
            tag="bath1",
        )

        with pytest.raises(ValueError) as err:
            FermionicBath("not-a-qobj", [1.], [0.5], [2.], [0.6])
        assert str(err.value) == "The coupling operator Q must be a Qobj."

        with pytest.raises(ValueError) as err:
            FermionicBath(Q, [1.], [], [2.], [0.6])
        assert str(err.value) == (
            "The bath exponent lists ck_plus and vk_plus, and ck_minus and"
            " vk_minus must be the same length."
        )

        with pytest.raises(ValueError) as err:
            FermionicBath(Q, [1.], [0.5], [2.], [])
        assert str(err.value) == (
            "The bath exponent lists ck_plus and vk_plus, and ck_minus and"
            " vk_minus must be the same length."
        )
