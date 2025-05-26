# Debugging Memory Simulation Issues

This guide helps you identify and resolve common issues in the Memulatrix memory simulator.

## Common TLB Issues

### Zero TLB Hit Rate

**Symptoms:**

- TLB hit rate of 0%
- All memory accesses result in TLB misses

**Possible Causes:**

1. **Lack of Memory Access Locality**

   The most common cause of zero TLB hits is random memory access patterns without locality.

   ```cpp
   // Before: Random access without locality
   uint64_t page_number = page_distributions[process_index](gen);

   // After: Access with temporal and spatial locality
   if (locality_dist(gen) < 0.7) {
       int offset = std::uniform_int_distribution<>(-3, 3)(gen);
       page_number = static_cast<int64_t>(last_accessed_pages[process_index]) + offset;
       page_number = std::max(uint64_t(0), std::min(page_number, max_pages[process_index]));
   } else {
       page_number = page_distributions[process_index](gen);
   }
   ```

2. **TLB Not Enabled**

   Check if the TLB is enabled in configuration:

   ```json
   {
     "tlb_enabled": true
   }
   ```

3. **TLB Capacity Too Small**

   If the number of pages accessed exceeds TLB capacity by a large margin, hit rate will be very low.

   ```cpp
   // TLB capacity calculation
   tlb_capacity = std::max(1, (tlb_size * 1024) / entry_size);
   ```

4. **TLB Not Being Updated**

   Check if new translations are being added to the TLB:

   ```cpp
   if (tlb_enabled && frame != UINT64_MAX) {
       tlb_insert(p.id, page_number, va, frame, 1);
   }
   ```

5. **TLB Entries Being Incorrectly Invalidated**

   Check for any code that might be clearing the TLB unnecessarily.

### Unrealistically High TLB Hit Rate

**Symptoms:**

- TLB hit rate close to 100%
- Almost no TLB misses

**Possible Causes:**

1. **Overly Constrained Memory Access Patterns**

   Accessing the same page repeatedly will give artificially high hit rates.

2. **TLB Not Being Properly Cleared Between Context Switches**

   Ensure the TLB is properly managed when switching between processes.

## Page Fault Issues

### Excessive Page Faults

**Symptoms:**

- High number of page faults
- Poor performance

**Possible Causes:**

1. **Insufficient Physical Memory**

   If RAM is too small compared to the working set size of processes.

2. **Poor Page Replacement Algorithm**

   Check the page replacement strategy implementation.

3. **Non-Optimal Process Scheduling**

   Too many active processes competing for memory.

## Debugging Steps

1. **Check Configuration**

   Ensure `environment.json` and `processes.json` have appropriate values:

   ```
   RAM size should be sufficient for process working sets
   Page size should be appropriate (typical ranges: 4KB to 2MB)
   TLB should be enabled and sized appropriately
   ```

2. **Enable Debug Logging**

   The simulator writes to `debug.txt`. Examine this file for detailed operation information:

   ```
   Look for TLB hits/misses
   Check page table operations
   Verify memory access patterns
   ```

3. **Validate Memory Access Patterns**

   Add code to analyze the distribution of memory accesses:

   ```cpp
   // Count accesses per page
   std::map<uint64_t, int> page_access_count;
   // ...
   page_access_count[page_number]++;
   ```

4. **Check TLB Replacement Policy**

   Ensure the FIFO queue is working correctly:

   ```cpp
   if (tlb.size() >= static_cast<size_t>(tlb_capacity)) {
       std::string old_key = tlb_fifo.front();
       tlb_fifo.pop();
       tlb.erase(old_key);
   }
   ```

5. **Validate Statistics Collection**

   Ensure statistics are being properly updated:

   ```cpp
   if (tlb_hit) {
       stats_update(tlb_hits, p.id, 1);
       total_hits++;
   } else {
       stats_update(tlb_misses, p.id, 1);
       total_misses++;
   }
   ```

## Optimizing Simulation Parameters

### TLB Size Considerations

The optimal TLB size depends on the workload:

- **Small programs with good locality**: Smaller TLB (16-64 entries) may be sufficient
- **Large programs with poor locality**: Larger TLB (128-1024 entries) may be needed

Modern CPUs typically have multiple TLBs of different sizes for different page sizes.

### Page Size Trade-offs

- **Smaller pages**: Less internal fragmentation, more page table entries needed
- **Larger pages**: Better for sequential access, higher risk of internal fragmentation

Typical page sizes range from 4KB to 2MB, with some architectures supporting multiple page sizes.

## Testing and Validation

To validate the simulator's accuracy:

1. **Compare with theoretical models**:

   - Calculate expected hit rates based on working set sizes and TLB capacity
   - Verify results match theoretical expectations

2. **Create controlled test scenarios**:

   - Test with extreme cases (all sequential access, all random access)
   - Verify the simulator behaves as expected

3. **Use reference patterns**:
   - Implement standard memory access patterns from literature
   - Compare results with published benchmarks
