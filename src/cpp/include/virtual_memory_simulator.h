#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include <vector>
#include <string>
#include <utility>
#include "process.h"

class VirtualMemorySimulator {
private:
    uint64_t ram_size_bytes;     // Total RAM size in bytes
    uint32_t page_size_bytes;    // Page size in bytes
    uint32_t tlb_size;           // TLB size (number of entries)
    bool tlb_enabled;            // Whether TLB is enabled
    std::string virtual_address_size; // Virtual address size ("16-bit", "32-bit", "64-bit")

    // Helper function to trim whitespace and quotes
    std::string trim(const std::string& str);

public:
    VirtualMemorySimulator();  // Constructor reads from environment_settings.json

    std::vector<Process> load_processes();
};

#endif // VIRTUAL_MEMORY_SIMULATOR_H