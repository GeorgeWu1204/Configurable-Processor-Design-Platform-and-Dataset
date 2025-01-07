# The environment and steps to generate customised processors

## FPGA Board Name

xczu19eg-ffvc1760-2-i (active)

## Environment Requirement

Ubuntu 22.04

## NutShell Core

### Prerequisites

run ```sudo vmhgfs-fuse .host:/Year4 /mnt/hgfs -o allow_other``` to mount the shared folder

java

```sudo apt install openjdk-11-jre-headless```\
```sudo apt install openjdk-11-jdk-headless```

mill

```sudo sh -c "curl -L https://github.com/com-lihaoyi/mill/releases/download/0.6.3/0.6.3 > /usr/local/bin/mill && chmod +x /usr/local/bin/mill"```

Clone Project

```git clone https://github.com/OSCPU/NutShell.git```\
```git checkout -q release-211228```

### Steps

``` make bitstream BOARD=PXIe ```

## VeeR EL2 RISC-V Core

### Prerequisites

- Vivado 2023.2
- Verilator (4.106 or later)
- RISC-V GNU Compiler Toolchain ```sudo apt install gcc-riscv64-unknown-elf```
- ```export RV_ROOT=/home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/Cores-VeeR-EL2```
- TODO: Have not came up with a better method to handle this. The current method is to modify the ```configs/veer.config``` line 373 to ```$build_path = "/home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/Cores-VeeR-EL2/snapshots/$snapshot" ;```
- TODO2: To run the dhry benchmark, need to modify the ```tb_top.sv``` to delete the selection of ```verilator```

### Modifications
- add ```#include <limits>``` to the ```/usr/local/share/verilator/include/verilated.cpp```

### Steps

```make -f $RV_ROOT/tools/Makefile```


## [Rocket Chip](https://github.com/chipsalliance/rocket-chip.git)

### Setup
```git clone https://github.com/chipsalliance/rocket-chip.git``` \
```cd rocket-chip```    \
```git checkout v1.6``` \
```git submodule update --init --recursive``` \
```export RISCV=/home/hw1020/Documents/Installations``` \
```git submodule update --init``` \
```export RISCV=/home/hw1020/Documents/Installations``` \

During the Synthesis Stage,
include all the ```*.v``` files in the ```chipyard/sims/verilator/generated-src``` directory
remove the ```ClockSourceAtFreqMHz.v``` file

Then need to modify according to the issue proposed [GitHub Issue](https://github.com/chipsalliance/rocket-chip/pull/3226)

## [BOOM](https://github.com/riscv-boom/riscv-boom)

### Setup
```git clone https://github.com/ucb-bar/chipyard.git``` \
```git checkout 1.12.3``` \
```cd chipyard``` \
```./build-setup.sh riscv-tools``` \
```source env.sh``` \
Benchmark Execution \
```cd sims/verilator``` \
```make run-binary CONFIG=MediumBoomV3Config BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/dhrystone.riscv```


|Benchmark | Minstret |
|----------|----------|
|dhrystone | 186031   |
|median    | 4659     |
|memcpy    | 5525     |
|mm        | 24744    |
|mt-matmul | 30325    |
|mt-memcpy | 14674    |
|mt-vvadd  | 20824    |
|multiply  | 42503    |
|pmp       | None     |
|qsort     | 123506   |
|rsort     | 171154   |
|spmv      | 34466    |
|towers    | 4562     |
|vec-daxpy | Failed   |
|vec-memcpy| Failed   |
|vec-sgemm | Not Know |
|vec-strcmp| Not Know |
|vvadd     | 2416     |


|Test Name | Minstret |
|----------|----------|
|pingd     |0         |
|accum     |0         |
|big-blkdev|0         |
|blkdev    |0         |
|charcount |0         |
|fft       |0         |