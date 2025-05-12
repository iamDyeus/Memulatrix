#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include "json.hpp"
#include "page_table.h"
#include <string>
#include <vector>
#include <map>

using json = nlohmann::json;

class SocketHandler;

struct Process {
    std::string id;
    std::string name;
    uint64_t size_bytes;
    std::string type;
    bool has_priority;
    bool is_process_stop;
};

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
    void lookup(const std::string& process_id, uint64_t page_number);
    uint64_t get_frame_number(const std::string& pid, uint64_t page_number);

private:
    SocketHandler* socket_handler;
    std::vector<Process> processes;
    uint64_t ram_size_bytes;
    uint64_t page_size_bytes;
    int tlb_size;
    bool tlb_enabled;
    std::string virtual_address_size;
    std::string rom_size;
    int swap_percent;
    std::string allocation_type;
    std::vector<std::pair<int, int>> tlb_hits;
    std::vector<std::pair<int, int>> tlb_misses;
    std::vector<std::pair<int, double>> tlb_hit_rate;
    std::vector<std::pair<int, int>> page_faults;
    std::map<std::string, std::pair<uint64_t, PageTable>> page_tables;
    int total_hits;
    int total_misses;
    int total_faults;
};

#endif