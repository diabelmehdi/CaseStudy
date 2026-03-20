import math
from typing import List


def generate_primes(start: int, end: int) -> List[int]:
    if end < 2:
        return []

    sieve_start = max(start, 2)

    sieve = [True] * (end + 1)
    sieve[0] = False
    sieve[1] = False

    for i in range(2, int(math.sqrt(end)) + 1):
        if sieve[i]:
            for multiple in range(i * i, end + 1, i):
                sieve[multiple] = False

    primes = [num for num in range(sieve_start, end + 1) if sieve[num]]

    return primes
