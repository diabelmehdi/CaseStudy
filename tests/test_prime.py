import pytest
from app.core.prime import generate_primes


class TestGeneratePrimes:
    def test_basic_range(self):
        assert generate_primes(1, 10) == [2, 3, 5, 7]

    def test_single_prime(self):
        assert generate_primes(7, 7) == [7]

    def test_single_non_prime(self):
        assert generate_primes(4, 4) == []

    def test_range_below_two(self):
        assert generate_primes(0, 1) == []

    def test_start_equals_end_prime(self):
        assert generate_primes(13, 13) == [13]

    def test_large_range(self):
        primes = generate_primes(1, 100)
        assert len(primes) == 25
        assert primes[0] == 2
        assert primes[-1] == 97

    def test_range_with_no_primes(self):
        assert generate_primes(14, 16) == []

    def test_start_at_two(self):
        assert generate_primes(2, 2) == [2]

    def test_consecutive_primes(self):
        assert generate_primes(2, 3) == [2, 3]

    def test_high_range(self):
        primes = generate_primes(990, 1000)
        assert primes == [991, 997]
