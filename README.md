# Configurable-Processor-Design-Platform-and-Dataset

This repositry contains the platform and dataset for configurable RISC-V processors.

- The platform is able to automatically collect the benchmark performance, power and resource utilisation for the selected combinations of the RISC-V processors.
- The dataset records the results obtained by the platform.

## Supported RISC-V processors

- Berkley Out of Order Machine (BOOM)
- RocketChip
- Ibex
- Scarv

## Supported Functionality

- The dataset supports brute force methods to explore all combinations of parameters and will automatically retrieve the benchmark performance and resource utilisation if the customised processor is not yet stored in the dataset.
- An interface that allows easy access to the dataset via scripts or Python. It supports various combinations and numbers of parameters as input to query the dataset.
- The dataset can automatically detect whether the parameters meet the specified constraints, both inherent constraints and conditional constraints among the parameters.

## Supported Benchmark

- RISC-V Benchmark Library
