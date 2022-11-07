"""
This package contains helpers for managing inexact multiplications of monetary amounts
which can not be divided.

closest_round_division() is the core algorithm, surrounded by various helpers.
"""
import typing


def col_sum(distribution: list[list[int]]) -> list[int]:
    """
    Helper function for creating a column-wise sum of a list-of-lists-of-ints.
    """
    sums = [0] * len(distribution[0])
    for row in distribution:
        for idx in range(len(row)):
            sums[idx] += row[idx]
    return sums


def refund(refunds: list[int], charge: list[int]) -> list[list[int]]:
    """
    Given a charge that was divided into multiple sub-amounts (e.g. cost and tax
    for each item, or which account is responsible for how much of the charge),
    calculate refunds which return money as close as possible to proportional
    to how it was charged.

    >>> refund([100, 4], [75])
    [75, 3]

    This is good in particular for a refund, because calculating a refund using
    this function ensures that when the full amount is refunded, each allocation
    will go down to 0.  If the original distribution is not know (for example,
    because the allocation percentages or tax rate at the time of the original
    transaction was not stored), this allows a refund to be calculated regardless.
    """
    total = sum(charge)
    fractions = [allocation / total for allocation in charge]
    return closest_round_division(refunds, fractions)


def split(amounts: typing.Union[int, list[int]], shares) -> typing.Union[int, list[int]]:
    """
    Divide up amounts as closely as possible to the shares.

    >>> split(2, [50, 50])
    [1, 1]

    The scale of shares doesn't matter, only their relative proportions.
    """
    total = sum(shares)
    fractions = [share / total for share in shares]
    if type(amounts) is int:
        return closest_round_division([amounts], fractions)[0]
    return closest_round_division(amounts, fractions)


def _round_to_int_if_close(val):
    """
    If a value is really, really close to an int, nudge it in.  Make 1/6 + 5/6 == 1.
    """
    # if the scale factor is really, really close to an integer, nudge it in
    if abs(val - int(val)) < 2 ** -40:
        return int(val)
    if abs(val - int(val) - 1) < 2 ** -40:
        return int(val) + 1
    if abs(val - int(val) + 1) < 2 ** -40:
        return int(val) - 1
    return val


def closest_round_division(numbers: list[int], fractions: list[float]) -> list[list[int]]:
    '''
    Given a list of numbers and a list of fractions, this function performs a more
    sophisticated version of:
    [[round(n * f) for f in fractions] for n in numbers]
    Rather than rounding each number individually, the algorithm rounds in order that
    the sum of each row and the sum of each column both remain within 1 of their exact
    result.
    When dealing with monetary amounts, it is common to need to make a fractional multiplication
    to a discrete monetary amount which cannot be done precisely.  For example, adding a 3% tax
    to a $1.50 amount. Or, 3 friends splitting a $10 bill.

    >>> closest_round_division([150], [1, 0.03])
    [[150, 4]]

    >>> closest_round_division([1000], [1/3, 1/3, 1/3])
    [[333, 333, 334]]

    Not only does this ensure that the $10.00 is completely accounted for, but if there
    were multiple amounts being split among parties, the later roundings take into account
    earlier ones to try and keep the columns as even as possible.

    For example, if the 3 friends are splitting 3 bills of $10 each, the algorithm will round
    such that each bill is completely paid for, but also each individual will end up paying
    exactly $10 in the end, even though on each individual bill they are paying different amounts.

    >>> closest_round_division([1000, 1000, 1000], [1/1, 1/3, 1/3])
    [[333, 333, 334],
     [333, 334, 333],
     [334, 333, 333]]

    This is often handled in an ad-hoc manner, with code that mixes the pure numerical problem
    of rounding the multiplication to the nearest discrete amount with the business logic of
    what the quantities represent.
    Then, there's another dimension of complexity when many monetary amounts are combined
    into one total.  For example, a 3% tax on $1.50 would be 4.5 cents which may be
    rounded up (school rounding) or down (banker's rounding).  But what if we were calculating
    the 3% tax on an order of two $1.50 items?  The tax on the total $3.00 is _exactly_
    9 cents.  So, sum(tax(items)) != tax(sum(items)).
    This function handles this complexity for you, allowing the business logic to remain
    simple.

    >>> closest_round_division([150, 150], [1, 0.3])
    [[150, 4], [150, 5]]
    '''
    # the factor the total will grow / shrink by in the end
    scale_factor = _round_to_int_if_close(sum(fractions))
    remainder_error = 0  # accumulated error in row sums if the fractions leave "left over"
    # these lists are [error, col-num] mini data structures
    # col_errors can be sorted to find the col-num with the largest or smallest error
    col_errors = [[0, col] for col in range(len(fractions))]
    # indexed_col_errors allows access by col-num to update the error
    indexed_col_errors = {error[1]: error for error in col_errors}
    result = []
    # each number is will be one row in the final result
    for number in numbers:
        # initialize the row with integer-truncated fractions, but keep track of the difference
        # between the integer truncated values and the exact fractions in our errors data structure
        row = []
        for idx, frac in enumerate(fractions):
            # compute the exact fraction (or as close as 64 bit float can represent)
            exact = frac * number
            truncated = int(exact)  # truncate the amount to an integer
            row.append(truncated)  # put the truncated amount in the row
            indexed_col_errors[idx][0] += exact - \
                truncated  # accumulate the column error
        # if there is "extra" left over, distribute it among the columns to minimize the overall error
        exact_sum = number * scale_factor
        remainder = int(exact_sum) - sum(row)
        # there may also be "extra" that has accumulated if sum(fractions) scales rows by an amount
        # that doesn't divide evenly; check if there's >= 1 of running error accumulated, and if so consume it
        remainder_error += exact_sum - int(exact_sum)
        if remainder_error >= 1:
            remainder += 1
            remainder_error -= 1
        elif remainder_error <= -1:
            remainder -= 1
            remainder_error += 1
        if remainder:
            if remainder > 0:  # grab the remainder most positive errors and "use up" the remainder
                col_errors.sort()
                for col_error in col_errors[-remainder:]:
                    col_error[0] -= 1
                    row[col_error[1]] += 1
            elif remainder < 0:  # grab the -remainder most negative errors and "use up" the remainder
                # for symmetrical behavior of positive and negative numbers, flip the indices negative since
                # those are the tie-breakers for sorting
                col_errors.sort(key=lambda err_col: (err_col[0], -err_col[1]))
                for col_error in col_errors[:-remainder]:
                    col_error[0] += 1
                    row[col_error[1]] -= 1
        # magnitude of col_errors < 1
        assert col_errors[0][0] > -1 and col_errors[-1][0] < 1
        # magnitude of row error < 1
        assert -1 < sum(row) - (number * scale_factor) < 1
        result.append(row)
    assert -1 < remainder_error < 1
    return result
