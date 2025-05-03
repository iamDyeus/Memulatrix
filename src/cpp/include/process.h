#include <string>

struct Process {
    std::string id;
    std::string name;
    uint64_t size_bytes;
    std::string type;
    bool has_priority;  // Boolean to indicate if the process has priority
    uint64_t virtual_address;  // Single virtual address (parsed from hex)
    std::string virtual_address_size;  // "16-bit", "32-bit", or "64-bit"
    bool is_process_stop;  // Flag to indicate if the process is stopped
};