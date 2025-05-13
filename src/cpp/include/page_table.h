#ifndef PAGE_TABLE_H
#define PAGE_TABLE_H

#include <vector>
#include <random>
#include <unordered_map>
#include <string>
#include "json.hpp"

using json = nlohmann::json;

class PageTable {
public:
    PageTable(uint64_t num_pages, uint64_t page_size_bytes, int entry_size, const std::string& allocation_type,
              uint64_t ram_frames, uint64_t total_frames, uint64_t ram_size_bytes, double frame_percent,
              const std::string& process_id, const std::string& virtual_address_size);
    ~PageTable();

    bool allocate(uint64_t block_size_bytes, std::vector<uint64_t>& available_frames,
                 std::vector<uint64_t>& available_table_frames, std::mt19937& gen,
                 std::vector<uint64_t>& available_swap_frames);
    bool access(uint64_t virtual_address);
    json export_json() const;
    uint64_t size_bytes() const;
    uint64_t lookup(uint64_t page_number) const;
    int get_levels() const;
    const std::string& get_process_id() const;
    static uint64_t get_last_used_frame();
    uint64_t get_top_level_frame() const;
    void free_frames(std::vector<uint64_t>& available_frames, std::vector<uint64_t>& available_table_frames);
    void set_frame_availability(bool available);
    void free_swap_frames(std::vector<uint64_t>& available_swap_frames);

private:
    uint64_t num_pages_;
    uint64_t page_size_bytes_;
    int entry_size_;
    std::string allocation_type_;
    uint64_t ram_frames_;
    uint64_t total_frames_;
    uint64_t ram_size_bytes_;
    std::string process_id_;
    std::string virtual_address_size_;
    uint64_t max_frames_;
    uint64_t pages_per_frame_;
    uint64_t entries_per_table_;
    int bits_per_level_;
    int levels_;
    static uint64_t last_used_frame_;
    uint64_t top_level_frame_;
    std::vector<std::pair<uint64_t, bool>> single_level_table_;
    std::vector<std::pair<uint64_t, bool>> top_level_table_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> second_level_tables_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> third_level_tables_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> fourth_level_tables_;
    std::unordered_map<uint64_t, std::pair<std::string, bool>> ram_; // {content, available}
    std::unordered_map<std::string, std::string> swap_map_;
    std::unordered_map<uint64_t, uint64_t> entries_;

    int calculate_levels();
    void initialize_page_tables();
    uint64_t get_unique_frame(std::vector<uint64_t>& available_frames, std::mt19937& gen);
    uint64_t get_unique_swap_frame(std::vector<uint64_t>& available_swap_frames, std::mt19937& gen);
    void set_page_entry(uint64_t page_number, uint64_t frame_number, bool in_ram);
    void log_page_table_creation();
    void log_swap_map() const;
};
#endif