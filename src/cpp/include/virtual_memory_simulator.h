#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include <string>
#include <vector>
#include <unordered_map>
#include "json.hpp"
#include "process.h"
#include "page_table.h"

using json = nlohmann::json;

class SocketHandler;

class VirtualMemorySimulator {
public:
    VirtualMemorySimulator(SocketHandler* handler);
    ~VirtualMemorySimulator();
    void load_settings(const json& settings);
    void simulate();
    json export_results();
    void reset();
    std::string read_socket();
    bool write_socket(const std::string& data);
    bool accept_connection();

private:
    SocketHandler* socket_handler;
    uint64_t ram_size_bytes;
    uint64_t page_size_bytes;
    int tlb_size;
    bool tlb_enabled;
    std::string virtual_address_size;
    std::string rom_size;
    int swap_percent;
    std::string allocation_type;
    std::vector<Process> processes;
    std::vector<std::pair<int, int>> tlb_hits;
    std::vector<std::pair<int, int>> tlb_misses;
    std::vector<std::pair<int, double>> tlb_hit_rate;
    std::vector<std::pair<int, int>> page_faults;
    int total_hits;
    int total_misses;
    int total_faults;
    std::unordered_map<std::string, std::pair<uint64_t, PageTable>> page_tables;
};

#endif