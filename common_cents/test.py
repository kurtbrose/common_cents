import copy

from common_cents import closest_round_division


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


def _col_sum(matrix):
    """given a list-of-list-of-numbers, return the column-oriented sum"""
    sums = [0] * len(matrix[0])
    for row in matrix:
        for idx in range(len(row)):
            sums[idx] += row[idx]
    return sums


def _exact_division_error(data, result, fractions):
    # how close did each column scale to the target fraction?
    cols = _col_sum(result)
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
assert closest_round_division([-1], [1/3, 1/3, 1/3])[0] == [0, 0, -1]
assert closest_round_division([-2], [1/3, 1/3, 1/3])[0] == [0, -1, -1]
assert closest_round_division([-3], [1/3, 1/3, 1/3])[0] == [-1, -1, -1]
assert closest_round_division([-4], [1/3, 1/3, 1/3])[0] == [-1, -1, -2]
# nothing blows up with 0
assert closest_round_division([1], [1, -1])[0] == [1, -1]
assert closest_round_division([1], [1, 0])[0] == [1, 0]