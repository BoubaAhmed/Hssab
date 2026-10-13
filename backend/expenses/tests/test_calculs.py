from expenses.calculs import repartir


def test_repartition_avec_reste():
    assert repartir(1000, 3) == [334, 333, 333]


def test_repartition_exacte():
    assert repartir(900, 3) == [300, 300, 300]


def test_le_total_est_toujours_exact():
    for total in [1, 7, 100, 999, 12345]:
        for n in [1, 2, 3, 7]:
            assert sum(repartir(total, n)) == total


import pytest

from expenses.calculs import (
    calculer_soldes,
    parts_egales,
    repartir,
    simplifier,
)


def test_parts_egales_attribue_le_reste():
    assert parts_egales(1000, ['ali', 'sara', 'karim']) == {
        'ali': 334, 'sara': 333, 'karim': 333,
    }


def test_soldes_apres_une_depense():
    depenses = [{
        'payeur': 'ali',
        'montant': 1000,
        'parts': {'ali': 334, 'sara': 333, 'karim': 333},
    }]
    soldes = calculer_soldes(['ali', 'sara', 'karim'], depenses, [])
    assert soldes == {'ali': 666, 'sara': -333, 'karim': -333}


def test_la_somme_des_soldes_est_toujours_zero():
    depenses = [
        {'payeur': 'ali', 'montant': 1000,
         'parts': {'ali': 334, 'sara': 333, 'karim': 333}},
        {'payeur': 'sara', 'montant': 2500,
         'parts': {'ali': 1250, 'sara': 1250}},
    ]
    soldes = calculer_soldes(['ali', 'sara', 'karim'], depenses, [])
    assert sum(soldes.values()) == 0


def test_un_remboursement_reduit_la_dette():
    depenses = [{
        'payeur': 'ali',
        'montant': 1000,
        'parts': {'ali': 334, 'sara': 333, 'karim': 333},
    }]
    remboursements = [{'de': 'sara', 'a': 'ali', 'montant': 333}]
    soldes = calculer_soldes(['ali', 'sara', 'karim'], depenses, remboursements)
    assert soldes['sara'] == 0
    assert soldes['ali'] == 333


def test_depense_dont_les_parts_ne_font_pas_le_total():
    depenses = [{'payeur': 'ali', 'montant': 1000, 'parts': {'ali': 500}}]
    with pytest.raises(ValueError):
        calculer_soldes(['ali'], depenses, [])


def test_simplifier_evite_les_intermediaires():
    # Ali doit 50 à Sara, Sara doit 50 à Karim -> un seul virement
    soldes = {'ali': -5000, 'sara': 0, 'karim': 5000}
    assert simplifier(soldes) == [('ali', 'karim', 5000)]


def test_simplifier_solde_tout():
    soldes = {'ali': -700, 'sara': -300, 'karim': 1000}
    virements = simplifier(soldes)
    recu = sum(m for _, a, m in virements if a == 'karim')
    assert recu == 1000