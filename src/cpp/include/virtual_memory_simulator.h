#ifndef VIRTUAL_MEMORY_SIMULATOR_H
#define VIRTUAL_MEMORY_SIMULATOR_H

#include "json.hpp"
#include "page_table.h"
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <queue>
#include "process.h"
#include <fstream>
#include <filesystem>
#include <chrono>
#include <thread>

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
    VirtualMemorySimulator(const std::string &bin_path = "bin");
    ~VirtualMemorySimulator();
    bool load_settings();
    void simulate();
    bool save_results(const json &results);
    json export_results();
    void reset();
    void lookup(const std::string &process_id, uint64_t page_number);
    uint64_t get_frame_number(const std::string &pid, uint64_t page_number);
    void tlb_insert(const std::string &pid, uint64_t page_no, uint64_t virtual_address, uint64_t frame_no, int process_status);
    void tlb_remove_process(const std::string &pid);
    uint64_t tlb_get_frame(const std::string &pid, uint64_t page_no);

private:
    static constexpr int SIMULATION_TIMEOUT_MS = 30000; // 30 seconds timeout
    static constexpr int PROGRESS_UPDATE_INTERVAL = 10; // Update progress every 10 time steps
    static constexpr int MAX_INACTIVE_CYCLES = 1000;    // Max cycles without progress before timeout

    std::string bin_directory;
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

    // Time series data for visualization
    std::vector<std::vector<std::pair<int, int>>> tlb_hits_over_time;
    std::vector<std::vector<std::pair<int, int>>> tlb_misses_over_time;
    std::vector<std::vector<std::pair<int, double>>> tlb_hit_rate_over_time;
    std::vector<std::vector<std::pair<int, int>>> page_faults_over_time;
    std::vector<std::pair<int, int>> ram_frames_used_over_time;

    // Summary data
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

    bool initialize_simulation();
    bool handle_process(const Process &process, uint64_t virtual_address, std::mt19937 &gen, std::ofstream &debug_file);
    void update_statistics(const std::string &pid, bool tlb_hit);
    void track_time_series_data(int time_step);
    void print_statistics(int time_step, std::ofstream &debug_file);
    void cleanup_process(const std::string &pid);
    bool should_abort_simulation(const std::chrono::steady_clock::time_point &start_time,
                                 int inactive_cycles);
    void print_page_tables(std::ofstream &debug_file);
};

#endif