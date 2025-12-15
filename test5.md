### 1. Architectural Summary

The goal is to create a robust and Pythonic function for sorting a list of numbers. Instead of re-implementing a sorting algorithm (e.g., bubble sort, quicksort), which is inefficient and error-prone for production code, the optimal approach is to leverage Python's built-in `sorted()` function.

**Design Choices:**

* **Use `sorted()`:** This function is a highly optimized C implementation of the Timsort algorithm, providing excellent performance for real-world data.
* **Immutability:** The `sorted()` function returns a *new* sorted list, leaving the original input list unmodified. This is a best practice as it prevents unexpected side effects in the calling code. The alternative, `list.sort()`, modifies the list in-place and would be less suitable for a general-purpose utility function that returns a result.
* **Type Hinting:** The function signature uses strict type hints (`list[Union[int, float]]`) to clearly define its contract—it accepts a list of integers or floats and returns a list of the same.
* **Configurable Order:** A boolean `reverse` parameter is included to allow for sorting in both ascending (default) and descending order, mirroring the interface of the standard `sorted()` function.
* **Error Propagation:** The function does not catch the `TypeError` that `sorted()` raises for lists with incompatible types (e.g., `[1, 'a', 3]`). This is intentional. Propagating the exception allows the calling code to handle the invalid input as it sees fit, which is a more flexible and standard design.

### 2. Dependencies

No external dependencies are required. This solution uses only Python's standard library.

### 3. Implementation

```python
# Complete, runnable code block here
from typing import List, Union

def sort_numbers(
    numbers: List[Union[int, float]],
    reverse: bool = False
) -> List[Union[int, float]]:
    """Sorts a list of numbers.

    This function takes a list containing integers and/or floats and
    returns a new list with the elements sorted in either ascending or
    descending order. It does not modify the original list.

    Args:
        numbers: A list of numbers (integers or floats) to be sorted.
        reverse: If True, the list is sorted in descending order.
                 Defaults to False (ascending order).

    Returns:
        A new list containing the sorted numbers.

    Raises:
        TypeError: If the input list contains elements that cannot be
                   compared with each other (e.g., numbers and strings).
    """
    # The built-in sorted() function is highly optimized (Timsort)
    # and is the idiomatic way to sort an iterable in Python.
    # It returns a new sorted list, which is a best practice to avoid
    # side effects on the original input data.
    return sorted(numbers, reverse=reverse)

```

### 4. Usage Example

```python
# Brief snippet demonstrating how to run the code
if __name__ == "__main__":
    # --- Basic Usage ---
    original_data = [3.14, 1, -10, 50, 2, 2.0]
    print(f"Original list: {original_data}")

    # Sort in ascending order (default behavior)
    ascending_sorted = sort_numbers(original_data)
    print(f"Sorted (ascending): {ascending_sorted}")

    # Sort in descending order
    descending_sorted = sort_numbers(original_data, reverse=True)
    print(f"Sorted (descending): {descending_sorted}")

    # --- Verification ---
    # Verify that the original list remains unchanged
    print(f"Original list after sorting operations: {original_data}")

    # --- Edge Cases ---
    empty_list = []
    sorted_empty = sort_numbers(empty_list)
    print(f"\nSorting an empty list: {sorted_empty}")

    single_item_list = [100]
    sorted_single = sort_numbers(single_item_list)
    print(f"Sorting a single-item list: {sorted_single}")

    # --- Error Handling Example ---
    # The function will propagate a TypeError for invalid input
    mixed_data = [1, "apple", 3]
    try:
        sort_numbers(mixed_data)
    except TypeError as e:
        print(f"\nCaught expected error for mixed types: {e}")

```
