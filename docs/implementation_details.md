# Memulatrix Implementation Details

This document provides implementation-specific details about the Memulatrix memory simulator components and the logical flow of their operation.

## Key Components

### VirtualMemorySimulator Class

The primary simulation engine, responsible for:

- Loading configuration from JSON files
- Creating and managing page tables
- Handling TLB operations
- Simulating memory accesses
- Tracking and recording statistics

```cpp
class VirtualMemorySimulator {
private:
    // Storage structures
    std::unordered_map<std::string, TLBEntry> tlb;
    std::queue<std::string> tlb_fifo;
    std::unordered_map<std::string, PageTableEntry> page_tables;
    std::string bin_directory;

    // Statistics
    std::vector<std::pair<int, int>> tlb_hits;
    std::vector<std::pair<int, int>> tlb_misses;
    std::vector<std::pair<int, double>> tlb_hit_rate;
    std::vector<std::pair<int, int>> page_faults;
    int total_hits;
    int total_misses;
    int total_faults;

    // Configuration parameters
    uint64_t ram_size_bytes;
    uint64_t page_size_bytes;
    int tlb_size;  // Size in KB
    int tlb_capacity;  // Number of entries
    bool tlb_enabled;
    // ...
};
```

### PageTable Class

Handles the details of page table management:

- Multi-level page table operations
- Page allocation strategies
- Page table walks for address translation
- Frame management

## Memory Access Simulation

### Memory Access Workflow

1. **TLB Lookup**:

   ```cpp
   uint64_t frame = tlb_get_frame(p.id, page_number);
   bool tlb_hit = (frame != UINT64_MAX);
   ```

2. **Page Table Walk** (on TLB miss):

   ```cpp
   if (!tlb_hit) {
       frame = page_table.lookup(page_number);
       // Handle page faults if necessary
       // ...

       // Update TLB after successful lookup
       if (tlb_enabled && frame != UINT64_MAX) {
           tlb_insert(p.id, page_number, va, frame, 1);
       }
   }
   ```

3. **Statistics Update**:
   ```cpp
   if (tlb_hit) {
       stats_update(tlb_hits, p.id, 1);
       total_hits++;
   } else {
       stats_update(tlb_misses, p.id, 1);
       total_misses++;
   }
   ```

### Memory Access Pattern Implementation

The simulator implements realistic memory access patterns with temporal and spatial locality:

```cpp
// Generate memory access with locality
if (locality_dist(gen) < 0.7) {
    // Use temporal/spatial locality
    int offset = std::uniform_int_distribution<>(-3, 3)(gen);
    page_number = static_cast<int64_t>(last_accessed_pages[process_index]) + offset;
    page_number = std::max(uint64_t(0), std::min(page_number, max_pages[process_index]));
} else {
    // Random access (no locality)
    page_number = page_distributions[process_index](gen);
}

// Save this page as the last accessed page
last_accessed_pages[process_index] = page_number;
```

## TLB Implementation Details

### TLB Insertion

When a new mapping is added to the TLB:

```cpp
void VirtualMemorySimulator::tlb_insert(const std::string &pid, uint64_t page_no,
                                        uint64_t virtual_address, uint64_t frame_no,
                                        int process_status) {
    if (tlb_capacity <= 0)
        return; // Don't insert if TLB is disabled or has no capacity

    std::string key = pid + "_" + std::to_string(page_no);

    // Use FIFO replacement if TLB is full
    if (tlb.size() >= static_cast<size_t>(tlb_capacity)) {
        std::string old_key = tlb_fifo.front();
        tlb_fifo.pop();
        tlb.erase(old_key);
    }

    // Add the new entry
    TLBEntry entry = {pid, page_no, virtual_address, frame_no, process_status};
    tlb[key] = entry;
    tlb_fifo.push(key);
}
```

### TLB Lookup

Retrieving a mapping from the TLB:

```cpp
uint64_t VirtualMemorySimulator::tlb_get_frame(const std::string &pid, uint64_t page_no) {
    std::string key = pid + "_" + std::to_string(page_no);
    auto it = tlb.find(key);
    if (it != tlb.end() && it->second.process_status == 1) {
        return it->second.frame_no;
    }
    return UINT64_MAX;  // TLB miss
}
```

## JSON Configuration Details

### environment.json

This file contains system-wide settings for the simulation:

```json
{
  "ram_size_gb": 16, // Physical memory size
  "page_size_kb": 256, // Page/frame size
  "tlb_size": 16, // TLB size in KB
  "tlb_enabled": true, // Whether TLB is active
  "virtual_address_size": "64-bit", // Address width
  "rom_size": "32 GB", // Storage disk size
  "swap_percent": 5.0, // Percentage of ROM for swap
  "allocation_type": "Contiguous" // Memory allocation strategy
}
```

### processes.json

Defines the processes to be simulated:

```json
[
  {
    "id": "1001",
    "name": "1",
    "size_gb": 3,
    "type": "User",
    "has_priority": false,
    "is_process_stop": false,
    "virtual_address": "0x0000000246a06f55"
  }
]
```

## Simulation Results

The `simulation_results.json` contains performance statistics:

```json
{
  "page_faults": [
    [1001, 0],
    [1002, 0]
  ],
  "tlb_stats": {
    "hit_rate": [
      [1001, 0.7], // After fix: ~70% hit rate
      [1002, 0.65] // After fix: ~65% hit rate
    ],
    "hits": [
      [1001, 70], // After fix: ~70 hits
      [1002, 65] // After fix: ~65 hits
    ],
    "misses": [
      [1001, 30], // After fix: ~30 misses
      [1002, 35] // After fix: ~35 misses
    ],
    "total_hits": 135,
    "total_misses": 65
  },
  "total_faults": 0
}
```

## Optimization Strategies

### Improving TLB Performance

1. **Increase TLB size**: More entries means higher hit rate, but with diminishing returns
2. **Optimize locality**: Arrange memory accesses to maximize spatial and temporal locality
3. **Use different replacement policies**: FIFO, LRU, or Random can perform differently depending on the workload

### Reducing Page Faults

1. **Increase physical memory**: More RAM = fewer page faults
2. **Adjust page size**: Larger pages can improve spatial locality but may increase fragmentation
3. **Optimize process scheduling**: Group processes with complementary memory access patterns
