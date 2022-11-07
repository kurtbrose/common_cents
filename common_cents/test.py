import copy
import random

from common_cents import closest_round_division, split, refund, col_sum


def _l2_norm_diff(vec1, vec2):
    assert len(vec1) == len(vec2)
    acc = 0
    for num1, num2 in zip(vec1, vec2):
        acc += (num1 - num2) ** 2
    return (acc / len(vec1)) ** 0.5


def _l1_norm_diff(vec1, vec2):
    acc = 0
    for num1, num2 in zip(vec1, vec2):
        acc += abs(num1 - num2)
    return acc / len(vec1)


def _exact_division_error(data, result, fractions):
    # how close did each column scale to the target fraction?
    cols = col_sum(result)
    scale = sum(data)
    return _l2_norm_diff([1.0 * col / scale for col in cols], fractions)


def _check_division(data, fractions):
    '''
    helper function for testing performance of the functions
    over various inputs -- this checks that there isn't a
    rounding with lower error rates within one step of the
    given rounding
    '''
    result = closest_round_division(data, fractions)
    base = copy.deepcopy(result)
    error = _exact_division_error(data, result, fractions)
    # try a bunch of "nudging" permutations to rows
    # and check that none of them improve the overall error
    for row in result:
        for i in range(len(row)):
            for j in range(len(row)):
                if i == j or row[i] == 0:
                    continue
                row[i] -= 1
                row[j] += 1
                nudged_error = _exact_division_error(data, result, fractions)
                if nudged_error < error:
                    raise ValueError(f"smaller error {nudged_error:.4f} < {error:.4f} with rounding\n {result} vs\n {base}")
                row[i] += 1
                row[j] -= 1


_check_division([10, 10, 10, 10, 10], [2.0 / 3, 1.0 / 3])
# [[7, 3], [6, 4], [7, 3], [7, 3], [6, 4]]
_check_division([1000, 1], [2.0 / 3, 1.0 / 3])
# [[667, 333], [0, 1]]
_check_division([10, -10, 10, -10, 10], [2.0 / 3, 1.0 / 3])
# [[7, 3], [-7, -3], [7, 3], [-7, -3], [7, 3]]
_check_division([2, 3, 5, 7, 11, 13, 17, 23], [1, -0.1]) # 10% discount
# always favors more positive values to the right
assert closest_round_division([1], [1/3, 1/3, 1/3])[0] == [0, 0, 1]
assert closest_round_division([2], [1/3, 1/3, 1/3])[0] == [0, 1, 1]
assert closest_round_division([3], [1/3, 1/3, 1/3])[0] == [1, 1, 1]
assert closest_round_division([4], [1/3, 1/3, 1/3])[0] == [1, 1, 2]
# negative numbers are rounded away-from-0 the same as positive
assert closest_round_division([-1], [1/3, 1/3, 1/3])[0] == [0, 0, -1]
assert closest_round_division([-2], [1/3, 1/3, 1/3])[0] == [0, -1, -1]
assert closest_round_division([-3], [1/3, 1/3, 1/3])[0] == [-1, -1, -1]
assert closest_round_division([-4], [1/3, 1/3, 1/3])[0] == [-1, -1, -2]
# nothing blows up with 0
assert closest_round_division([1], [1, -1])[0] == [1, -1]
assert closest_round_division([1], [1, 0])[0] == [1, 0]


def test_money_conserved():
    """
    Simulate a charge followed by two refunds, in different hard-to-divvy-up amounts.
    """
    shares = 19, 27, 61

    def check(charge, refund_factor):
        # pylint: disable=too-many-locals
        refund1 = int(refund_factor * charge)
        refund2 = int((charge - refund1) * random.random())
        refund3 = charge - refund1 - refund2
        house, lot, host = split(charge, shares)
        # subsequent refunds are divided up according to how the funds so far have been allocated
        r1_house, r1_lot, r1_host = refund([refund1], (house, lot, host))[0]
        rows = refund([refund2, refund3], [house - r1_house, lot - r1_lot, host - r1_host])
        r2_house, r2_lot, r2_host = rows[0]
        r3_house, r3_lot, r3_host = rows[1]
        # check that we didn't leak any pennies from any of the three parties
        assert charge == refund1 + refund2 + refund3
        assert house == r1_house + r2_house + r3_house
        assert lot == r1_lot + r2_lot + r3_lot
        assert host == r1_host + r2_host + r3_host

    base_charge = 100003  # prime number
    random.seed(123)
    for factor in (1, 3, 7, 11, 13, 17, 23):
        charge = base_charge * factor
        # try some random cases
        for _ in range(100):
            check(charge, random.random())
            # try some cases very close to 1 / 0
            for refund_magnitude in (0.0001, 0.001, 0.01, 0.1):
                for refund_digit in (1, 2, 5):
                    refund_factor = refund_magnitude * refund_digit
                    check(charge, refund_factor)
                    check(charge, 1 - refund_factor)

test_money_conserved()
