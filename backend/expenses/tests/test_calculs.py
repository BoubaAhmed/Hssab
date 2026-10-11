from expenses.calculs import repartir


def test_repartition_avec_reste():
    assert repartir(1000, 3) == [334, 333, 333]


def test_repartition_exacte():
    assert repartir(900, 3) == [300, 300, 300]


def test_le_total_est_toujours_exact():
    for total in [1, 7, 100, 999, 12345]:
        for n in [1, 2, 3, 7]:
            assert sum(repartir(total, n)) == total