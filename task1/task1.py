import math
import os
import platform
import random
import time
from array import array


STUDENT_ID = 230103108
ELEMENT_COUNT = 20_000_000


def main() -> None:
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    cpu_model = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "Unknown")
    print(f"CPU model: {cpu_model}")
    print(f"Logical cores: {os.cpu_count()}")
    print(f"Array elements: {ELEMENT_COUNT}")
    print("Execution mode: serial, single thread")

    start_ns = time.perf_counter_ns()

    generator = random.Random(STUDENT_ID)
    values = array("d", (generator.random() for _ in range(ELEMENT_COUNT)))

    total = 0.0
    for value in values:
        total += value

    mean = total / ELEMENT_COUNT
    squared_deviation = 0.0
    for value in values:
        difference = value - mean
        squared_deviation += difference * difference
    standard_deviation = math.sqrt(squared_deviation / ELEMENT_COUNT)

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

    print(f"Mathematical sum: {total:.12f}")
    print(f"Standard deviation: {standard_deviation:.12f}")
    print(f"Wall-clock execution time (ms): {elapsed_ms:.3f}")


if __name__ == "__main__":
    main()
