#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include <string>
#include <vector>
#include "json.hpp"

// Using nlohmann::json as the json type (assumed from your code)
using json = nlohmann::json;

struct Process {
    std::string id;
    std::string name;
    uint64_t size_bytes;
    std::string type;
    bool has_priority;
    bool is_process_stop;
    uint64_t virtual_address;
};

class VirtualMemorySimulator {
public:
    VirtualMemorySimulator(const std::string& env_file, const std::string& proc_file);

    void load_environment_settings();
    std::vector<Process> load_processes();
    void print_processes(const std::vector<Process>& processes);
    void simulate();
    void export_results(const std::string& output_path);
    static bool wait_for_trigger(); // Changed to static

    // Member variables (assumed from your code)
    std::string env_file_path;
    std::string proc_file_path;
    uint64_t ram_size_bytes;
    uint64_t page_size_bytes;
    int tlb_size;
    bool tlb_enabled;
    std::string virtual_address_size;
    std::string rom_size;
    std::vector<std::pair<int, int>> tlb_hits;
    std::vector<std::pair<int, int>> tlb_misses;
    std::vector<std::pair<int, double>> tlb_hit_rate;
    std::vector<std::pair<int, int>> page_faults;
    int total_hits;
    int total_misses;
    int total_faults;
};

#endif // VIRTUAL_MEMORY_SIMULATOR_H