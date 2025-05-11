#ifndef PAGE_TABLE_H
#define PAGE_TABLE_H

#include <vector>
#include <unordered_map>
#include <string>
#include <random>
#include <fstream>
#include "json.hpp"

using json = nlohmann::json;

class PageTable {
public:
    PageTable(uint64_t num_pages, uint64_t page_size_bytes, int entry_size, const std::string& allocation_type,
              uint64_t ram_frames, uint64_t ram_size_bytes, double frame_percent, const std::string& process_id);
    ~PageTable();

    bool allocate(uint64_t block_size_bytes, std::vector<uint64_t>& available_frames, std::mt19937& gen);
    bool access(uint64_t virtual_address);
    json export_json() const;
    uint64_t size_bytes() const;
    uint64_t lookup(uint64_t page_number) const; // 1-based page number

private:
    int calculate_levels();
    void initialize_page_tables();
    void set_page_entry(uint64_t page_number, uint64_t frame_number, bool in_ram);
    void log_page_table_creation();
    uint64_t get_unique_frame(std::vector<uint64_t>& available_frames, std::mt19937& gen);

    uint64_t num_pages_;
    uint64_t page_size_bytes_;
    int entry_size_;
    std::string allocation_type_;
    uint64_t ram_frames_;
    uint64_t ram_size_bytes_;
    uint64_t max_frames_;
    uint64_t pages_per_frame_;
    int levels_;
    int bits_per_level_;
    uint64_t entries_per_table_;
    std::string process_id_;
    std::unordered_map<uint64_t, std::string> ram_; // Frame to purpose (e.g., "page_1", "table_0")
    std::unordered_map<uint64_t, uint64_t> entries_; // Page (1-based) to frame
    std::vector<std::pair<uint64_t, bool>> single_level_table_;
    std::vector<std::pair<uint64_t, bool>> top_level_table_; // Frame number, valid
    std::vector<std::vector<std::pair<uint64_t, bool>>*> second_level_tables_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> third_level_tables_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> fourth_level_tables_;
};

#endif