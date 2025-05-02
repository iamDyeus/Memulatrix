#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include <vector>
#include <string>
#include "process.h"

class VirtualMemorySimulator {
private:
    uint64_t ram_size_bytes;
    uint32_t page_size_bytes;
    uint32_t tlb_size;
    bool tlb_enabled;

    // Helper function to trim whitespace and quotes
    std::string trim(const std::string& str);

public:
    VirtualMemorySimulator(uint64_t ram_size, uint32_t page_size, uint32_t tlb_sz, bool tlb_on);

    std::vector<Process> load_processes();
};

#endif // VIRTUAL_MEMORY_SIMULATOR_H