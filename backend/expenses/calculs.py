def repartir(total_centimes: int, nb_personnes: int) -> list[int]:
    """Partage un montant en centimes sans perdre un centime."""
    if nb_personnes <= 0:
        raise ValueError('Il faut au moins une personne')
    base, reste = divmod(total_centimes, nb_personnes)
    return [base + 1 if i < reste else base for i in range(nb_personnes)]


def parts_egales(total_centimes: int, membres: list) -> dict:
    """Retourne {membre: part} pour un partage à parts égales."""
    parts = repartir(total_centimes, len(membres))
    return dict(zip(membres, parts))


def calculer_soldes(membres: list, depenses: list, remboursements: list) -> dict:
    """Solde en centimes : positif = on lui doit de l'argent."""
    soldes = {m: 0 for m in membres}
    for d in depenses:
        if sum(d['parts'].values()) != d['montant']:
            raise ValueError('La somme des parts doit égaler le montant')
        soldes[d['payeur']] += d['montant']
        for membre, part in d['parts'].items():
            soldes[membre] -= part
    for r in remboursements:
        soldes[r['de']] += r['montant']
        soldes[r['a']] -= r['montant']
    return soldes


def simplifier(soldes: dict) -> list[tuple]:
    """Retourne des virements (qui, à qui, combien) pour tout équilibrer."""
    crediteurs = sorted(
        [[m, s] for m, s in soldes.items() if s > 0], key=lambda x: -x[1]
    )
    debiteurs = sorted(
        [[m, -s] for m, s in soldes.items() if s < 0], key=lambda x: -x[1]
    )
    virements = []
    i = j = 0
    while i < len(debiteurs) and j < len(crediteurs):
        montant = min(debiteurs[i][1], crediteurs[j][1])
        virements.append((debiteurs[i][0], crediteurs[j][0], montant))
        debiteurs[i][1] -= montant
        crediteurs[j][1] -= montant
        if debiteurs[i][1] == 0:
            i += 1
        if crediteurs[j][1] == 0:
            j += 1
    return virements