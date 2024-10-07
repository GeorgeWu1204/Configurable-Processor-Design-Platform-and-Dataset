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

## [CVA6 RISC-V CPU](https://github.com/openhwgroup/cva6)

### Prerequisites

- Verilator 5.008.

### Configure

at line 99 of ```cva6/makefile```

### Problem

The Simulation Results of the benchmarks such as Dhrystone are currently not supported. Hence, it cannot be used as a good candidate for the Bayesian Optimisation.

## [SCR1 RISC-V Core](https://github.com/syntacore/scr1/tree/master)

### Setup

```export RISCV=/home/hw1020/Documents/Installations```

## [Ibex RISC-V Core](https://github.com/lowRISC/ibex)

## [Rocket Chip](https://github.com/chipsalliance/rocket-chip.git)

### Setup
```git clone https://github.com/chipsalliance/rocket-chip.git```
```cd rocket-chip```
```git checkout v1.6```
```git submodule update --init```
```export RISCV=/home/hw1020/Documents/Installations```
Then need to modify according to the issue proposed [GitHub Issue](https://github.com/chipsalliance/rocket-chip/pull/3226)

## [BOOM](https://github.com/riscv-boom/riscv-boom)

### Setup
```git clone https://github.com/ucb-bar/chipyard.git```
```git checkout 1.12.3```
```cd chipyard```
```./build-setup.sh riscv-tools```
```source env.sh```
Benchmark Execution
```cd sims/verilator``
```make run-binary CONFIG=MediumBoomV3Config BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/dhrystone.riscv```


add to direct /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala

//--------------------------------------- Customised Automation ---------------------------------------

class WithNCustomBooms(n: Int = 1) extends Config(
  new WithTAGELBPD ++ // Default to TAGE-L BPD
  new Config((site, here, up) => {
    case TilesLocated(InSubsystem) => {
      val prev = up(TilesLocated(InSubsystem), site)
      val idOffset = up(NumTiles)
      (0 until n).map { i =>
        BoomTileAttachParams(
          tileParams = BoomTileParams(
            core = BoomCoreParams(
              fetchWidth = 1,
              decodeWidth = 32,
              numRobEntries = 64,
              issueParams = Seq(
                IssueParams(issueWidth=1, numEntries=8, iqType=IQT_MEM.litValue, dispatchWidth=1),
                IssueParams(issueWidth=1, numEntries=8, iqType=IQT_INT.litValue, dispatchWidth=1),
                IssueParams(issueWidth=1, numEntries=8, iqType=IQT_FP.litValue , dispatchWidth=1)),
              numIntPhysRegisters = 52,
              numFpPhysRegisters = 48,
              numLdqEntries = 8,
              numStqEntries = 8,
              maxBrCount = 8,
              numFetchBufferEntries = 8,
              ftq = FtqParameters(nEntries=16),
              nPerfCounters = 2,
              fpu = Some(freechips.rocketchip.tile.FPUParams(sfmaLatency=4, dfmaLatency=4, divSqrt=true))
            ),
            dcache = Some(
              DCacheParams(rowBits = 64, nSets=64, nWays=8, nMSHRs=2, nTLBWays=64)
            ),
            icache = Some(
              ICacheParams(rowBits = 64, nSets=64, nWays=4, fetchBytes=2*4)
            ),
            tileId = i + idOffset
          ),
          crossingParams = RocketCrossingParams()
        )
      } ++ prev
    }
    case NumTiles => up(NumTiles) + n
  })
)



//--------------------------------------- Customised Automation ---------------------------------------

class CustomisedBoomV3Config extends Config(
  new boom.v3.common.WithNCustomBooms(1) ++                          // small boom config
  new chipyard.config.AbstractConfig)


