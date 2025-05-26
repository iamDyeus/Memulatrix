# Memulatrix Memory Simulation Concepts

This document explains the key memory simulation concepts implemented in the Memulatrix system.

## Core Memory Concepts

### Virtual Memory

Virtual memory is an abstraction that provides each process with the illusion of having its own large, contiguous memory space regardless of physical memory constraints. The Memulatrix simulator implements this by:

- Translating virtual addresses to physical addresses
- Managing page tables per process
- Handling page faults when a requested page isn't available in RAM

### Page Tables

Page tables map virtual pages to physical frames:

- Each process has its own page table structure
- The simulator supports multiple page table levels based on the virtual address size
- Page table entries track whether pages are in RAM or swap space

## Translation Lookaside Buffer (TLB)

### Purpose and Function

The TLB is a specialized cache that stores recent virtual-to-physical address translations to speed up memory access. Instead of traversing the entire page table hierarchy for every memory access, the CPU first checks the TLB.

### Implementation in Memulatrix

The TLB is implemented with these key components:

```cpp
// TLB Entry structure
struct TLBEntry {
    std::string process_id;   // Process identifier
    uint64_t page_no;         // Virtual page number
    uint64_t virtual_address; // Virtual address
    uint64_t frame_no;        // Physical frame number
    int process_status;       // Status of the process
};

// TLB storage
std::unordered_map<std::string, TLBEntry> tlb;
std::queue<std::string> tlb_fifo;  // For replacement policy
```

### TLB Access Pattern

Memory accesses follow this pattern:

1. First check the TLB for a quick translation
2. On TLB miss, walk the page table to find the translation
3. Update the TLB with new translations for future use

### TLB Replacement Policy

When the TLB reaches capacity, the simulator uses a FIFO (First-In-First-Out) replacement policy:

- New entries evict the oldest entries
- The TLB size is configurable via `environment.json`

## Memory Locality

### Temporal and Spatial Locality

Real-world programs exhibit two types of locality:

1. **Temporal Locality**: Recently accessed memory locations are likely to be accessed again soon.

   - Example: Variables inside loops, frequently called functions

2. **Spatial Locality**: Memory locations near recently accessed addresses are likely to be accessed soon.
   - Example: Array elements, sequential instructions

### Importance for TLB Performance

The TLB relies on locality principles to be effective:

- Without locality, TLB hit rates approach zero
- With proper locality modeling, TLB hit rates can exceed 70-80%

### Implementation in Simulator

The simulator implements locality through a weighted probability model:

- 70% of memory accesses exhibit locality (same page or nearby pages)
- 30% of accesses are to random memory locations
- This balanced approach simulates realistic program behavior

## Page Faults

Page faults occur when a process attempts to access a page that is not currently in physical memory (RAM). The simulator handles this by:

1. Detecting when a requested page is not in RAM
2. Allocating a new physical frame if available
3. If no frames are available, implementing a page replacement policy
4. Updating page tables to reflect the new mapping

## Statistics Collection

The simulator tracks important metrics:

- TLB hit rate per process
- Number of page faults per process
- Total number of memory accesses

These statistics are saved to `simulation_results.json` for analysis.

## Interpreting Simulation Results

When analyzing simulation results, consider:

1. **TLB Hit Rate**: Higher is better, typically 60-80% for realistic workloads
2. **Page Faults**: Lower is better, indicates efficient memory management
3. **Process Behavior**: Different applications have different memory access patterns

## Configuration Options

The simulator can be configured through:

- `environment.json`: System-wide settings (RAM size, page size, TLB settings)
- `processes.json`: Process-specific settings (size, type, priority)

## Common Issues

### Zero TLB Hits

If you observe zero TLB hits, check:

1. Whether TLB is enabled in environment settings
2. Memory access patterns (lack of locality)
3. TLB size relative to working set size
4. TLB replacement policy implementation

### Excessive Page Faults

High page fault rates may indicate:

1. Insufficient physical memory
2. Poor page replacement algorithm
3. Inefficient memory access patterns
4. Non-optimal process scheduling
