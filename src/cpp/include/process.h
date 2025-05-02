#include <string>
#include <vector>

struct Process {
    std::string id;           // Auto-generated, e.g., "1001"
    std::string name;         // e.g., "Process1" or "kernel"
    uint64_t size_bytes;      // Size in bytes (converted from GB)
    std::string type;         // "User" or "System"
    std::string priority;     // e.g., "5" or "N/A"
    std::vector<uint32_t> virtual_addresses; // Generated for simulation
};