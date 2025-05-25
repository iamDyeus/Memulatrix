#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include "json.hpp"
#include "page_table.h"
#include "socket_handler.h"
#include "process.h"
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <queue>

using json = nlohmann::json;

struct TLBEntry
{
    std::string pid;
    uint64_t page_no;
    uint64_t virtual_address;
    uint64_t frame_no;
    int process_status;
};

struct PageTableEntry
{
    uint64_t top_level_frame;
    PageTable page_table;
    int flag;
    int64_t last_executed_page;
    PageTableEntry(uint64_t tlf, PageTable &&pt, int f, int64_t lep)
        : top_level_frame(tlf), page_table(std::move(pt)), flag(f), last_executed_page(lep) {}
};

class VirtualMemorySimulator
{
public:
    VirtualMemorySimulator(SocketHandler *handler);
    ~VirtualMemorySimulator();
    void load_settings(const json &settings);
    void simulate();
    json export_results();
    void reset();
    std::string read_socket();
    bool write_socket(const std::string &data);
    bool accept_connection();
    void lookup(const std::string &process_id, uint64_t page_number);
    uint64_t get_frame_number(const std::string &pid, uint64_t page_number);
    void tlb_insert(const std::string &pid, uint64_t page_no, uint64_t virtual_address, uint64_t frame_no, int process_status);
    void tlb_remove_process(const std::string &pid);
    uint64_t tlb_get_frame(const std::string &pid, uint64_t page_no);

private:
    SocketHandler *socket_handler;
    std::vector<Process> processes;
    uint64_t ram_size_bytes;
    uint64_t page_size_bytes;
    int tlb_size;     // In KB
    int tlb_capacity; // Number of TLB entries
    bool tlb_enabled;
    std::string virtual_address_size;
    std::string rom_size;
    int swap_percent;
    std::string allocation_type;
    std::vector<std::pair<int, int>> tlb_hits;
    std::vector<std::pair<int, int>> tlb_misses;
    std::vector<std::pair<int, double>> tlb_hit_rate;
    std::vector<std::pair<int, int>> page_faults;
    std::map<std::string, PageTableEntry> page_tables;
    int total_hits;
    int total_misses;
    int total_faults;
    std::vector<uint64_t> available_frames;
    std::vector<uint64_t> available_table_frames;
    std::vector<uint64_t> available_swap_frames;
    std::unordered_map<std::string, TLBEntry> tlb;
    std::queue<std::string> tlb_fifo;
};

#endif