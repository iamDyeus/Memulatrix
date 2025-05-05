#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include <string>
#include <vector>
#include "json.hpp"

using json = nlohmann::json;

struct Process {
    std::string id;
    std::string name;
    unsigned long long size_bytes;
    std::string type;
    bool has_priority;
    unsigned long long virtual_address;
    bool is_process_stop;
};

class VirtualMemorySimulator {
public:
    VirtualMemorySimulator(const std::string& env_file, const std::string& proc_file);

    void load_environment_settings();
    std::vector<Process> load_processes();
    void print_processes(const std::vector<Process>& processes);

private:
    std::string env_file_path;
    std::string proc_file_path;

    // Environment settings
    unsigned long long ram_size_bytes;
    unsigned long long page_size_bytes;
    unsigned long tlb_size;
    bool tlb_enabled;
    std::string virtual_address_size;
    std::string rom_size;
};

#endif