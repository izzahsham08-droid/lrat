def risk_component(N, P, L, *extras):

    if L is None:
        return 0

    result = N * P * L

    for extra in extras:

        result *= extra

    return result