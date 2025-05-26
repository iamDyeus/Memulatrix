# Memulatrix Documentation

Welcome to the Memulatrix documentation. This project simulates virtual memory systems, including page tables, TLBs (Translation Lookaside Buffers), and memory management techniques.

## Table of Contents

1. [Memory Concepts](./memory_concepts.md)

   - Core concepts of virtual memory
   - TLB operation and importance
   - Memory locality principles
   - Page fault handling

2. [Implementation Details](./implementation_details.md)

   - VirtualMemorySimulator class structure
   - PageTable class operation
   - Memory access workflow
   - TLB implementation specifics
   - Configuration file formats

3. [Debugging Guide](./debugging_guide.md)
   - Common TLB issues and solutions
   - Page fault troubleshooting
   - Debugging steps
   - Parameter optimization
   - Testing and validation

## Quick Start

1. Configure the environment in `bin/environment.json`
2. Define processes in `bin/processes.json`
3. Run the simulator
4. Analyze results in `bin/simulation_results.json`

## Recent Changes

- Improved memory access pattern simulation to include temporal and spatial locality
- Fixed TLB hit rate calculations to properly reflect realistic memory access patterns
- Enhanced documentation with detailed explanations of memory management concepts

## Further Reading

- "Operating Systems: Three Easy Pieces" - Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau
- "Computer Architecture: A Quantitative Approach" - John L. Hennessy and David A. Patterson
