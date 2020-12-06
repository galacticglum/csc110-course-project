"""Helper functions."""

import random
from typing import Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from tqdm import tqdm


def parallel_map(iterables: Union[list, iter], function: callable, n_jobs: Optional[int] = 16,
                 use_kwargs: Optional[bool] = False, front_num: Optional[int] = 3,
                 show_progress_bar: Optional[bool] = True, initial_value: Optional[list] = None,
                 raise_errors: Optional[bool] = False, include_errors: Optional[bool] = True,
                 extend_result: Optional[bool] = False, return_output: Optional[bool] = True,
                 add_func: Optional[callable] = None) -> Union[list, None]:
    """A parallel version of the map function with a progress bar.
    Return a list of the form [function(iterables[0]), function(iterables[1]), ...].

    Args:
        iterables: A sequence, collection, or iterator object.
        function: A function to apply to the elements of `iterables`.
        n_jobs: The number of jobs to run.
        use_kwargs: Whether to consider the elements of iterables as dictionaries of
            keyword arguments to function.
        front_num: The number of iterations to run serially before dispatching the
            parallel jobs. Useful for catching exceptions.
        show_progress_bar: Whether to show a progress bar while the jobs run.
        initial_value: The initial value of the output list.
            This should be an iterables-like object.
        raise_errors: Whether to raise errors.
        include_errors: Whether to include the errors in the output list.
        extend_result: Whether the resultant list should be extended rather than appended to.
        return_output: Whether to return a list containing the output values of the function.
            If False, this function does not return None.
        add_func: A custom function for adding the output values of the function to the result list.
            This function has two parameters, the value to add and the list to add it to, and it
            should mutate the list.

    Preconditions:
        - n_jobs >= 1
        - front_num >= 0
    """
    if isinstance(iterables, list):
        front = [function(**a) if use_kwargs else function(a) for a in iterables[:front_num]]
        iterables = iterables[front_num:]
    else:
        front = []
        for _ in range(front_num):
            a = next(iterables)
            front.append(function(**a) if use_kwargs else function(a))

    def _add_func(x: object, output: list) -> None:
        """Add a value to the output list."""
        # No reason to add if we aren't returning the output.
        if not return_output:
            return

        if add_func is not None:
            add_func(x, output)
        else:
            if extend_result:
                output.extend(x)
            else:
                output.append(x)

    output = initial_value or list()
    for x in front:
        _add_func(x, output)

    # If n_jobs == 1, then we are not parallelising, run all elements serially.
    if n_jobs == 1:
        for a in tqdm(iterables):
            x = function(**a) if use_kwargs else function(a)
            _add_func(x, output)

        return output if return_output else None

    with ThreadPoolExecutor(max_workers=n_jobs) as pool:
        futures = [
            pool.submit(function, **a) if use_kwargs else
            pool.submit(function, a) for a in iterables
        ]

        for _ in tqdm(as_completed(futures), total=len(futures), unit='it',
                      unit_scale=True, disable=not show_progress_bar):
            # Do nothing...This for loop is just here to iterate through the futures
            pass

    # Don't bother retrieving the results from the future...If we don't return anything.
    if not return_output:
        return None

    for _, future in tqdm(enumerate(futures)):
        try:
            _add_func(future.result(), output)
        except Exception as exception:
            if raise_errors:
                raise exception
            if include_errors:
                _add_func(exception, output)

    return output


def set_seed(seed: int) -> None:
    """Sets the seed in random, numpy, and tensorflow.

    Args:
        seed: The seed of the random engine.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Set TensorFlow seed
    import tensorflow as tf
    tf.random.set_seed(seed)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'extra-imports': [
            'random',
            'typing',
            'concurrent.futures',
            'tqdm',
            'numpy'
            'tensorflow',
        ],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['R1705', 'C0200']
    })
