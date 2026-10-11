def repartir(total_centimes: int, nb_personnes: int) -> list[int]:
    """Partage un montant en centimes entre des personnes, sans perdre un centime."""
    if nb_personnes <= 0:
        raise ValueError('Il faut au moins une personne')
    base, reste = divmod(total_centimes, nb_personnes)
    return [base + 1 if i < reste else base for i in range(nb_personnes)]