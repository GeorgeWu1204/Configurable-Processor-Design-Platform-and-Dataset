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


- An interface that allows easy access to the dataset via scripts or Python. It supports various combinations and numbers of parameters as input to query the dataset.
- The dataset can automatically detect whether the parameters meet the specified constraints, both inherent constraints and conditional constraints among the parameters.
- The dataset can consider the target fpga device and therefore is able to tell whether the customised processor can be implemented on the target device.
- The dataset supports brute force methods to explore all combinations of parameters and will automatically retrieve the benchmark performance and resource utilisation if the customised processor is not yet stored in the dataset.


## Supported Benchmark

- RISC-V Benchmark Library

## Contribution

- The platform supports the aforementioned functionality and can be easily extended to support more processors, benchmarks, and constraints.
- The dataset is able to accelerate the synthesis process of the processor by recording the results of the previous synthesis.


## Future Work

- The design space for RocketChip and BOOM is still not fully explored by this platform. Several challenges could arise in addressing this issue; for example, as the number of cores increases, the platform may be unable to collect benchmark results due to RAM limitations.

