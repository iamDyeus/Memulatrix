#ifndef PAGE_TABLE_H
#define PAGE_TABLE_H

#include <vector>
#include <set>
#include <random>
#include <string>
#include <cmath>
#include "json.hpp"

using json = nlohmann::json;

class PageTable {
public:
    PageTable(uint64_t num_pages, uint64_t page_size_bytes, int entry_size, const std::string& allocation_type, uint64_t ram_frames, uint64_t ram_size_bytes, double frame_percent)
        : num_pages_(num_pages), page_size_bytes_(page_size_bytes), entry_size_(entry_size), allocation_type_(allocation_type), ram_frames_(ram_frames), ram_size_bytes_(ram_size_bytes) {
        max_frames_ = static_cast<uint64_t>(ram_frames * frame_percent / 100.0);
        pages_per_frame_ = page_size_bytes / entry_size;
        entries_per_table_ = page_size_bytes / entry_size; // e.g., 1024 for 4 KB page, 4-byte PTE
        bits_per_level_ = static_cast<int>(log2(entries_per_table_)); // e.g., 10 bits
        levels_ = calculate_levels();
        initialize_page_tables();
    }

    ~PageTable() {
        for (auto* table : second_level_tables_) {
            delete table;
        }
    }

    bool allocate(uint64_t block_size_bytes, std::vector<uint64_t>& available_frames, std::mt19937& gen) {
        uint64_t needed_frames = (num_pages_ + pages_per_frame_ - 1) / pages_per_frame_;
        uint64_t used_frames = std::min(needed_frames, max_frames_);

        if (allocation_type_ == "Contiguous") {
            uint64_t start_frame = 0;
            for (uint64_t i = 0; i < available_frames.size(); ++i) {
                if (i == 0 || available_frames[i] == available_frames[i-1] + 1) {
                    if (i - start_frame + 1 >= num_pages_) {
                        for (uint64_t j = 0; j < num_pages_; ++j) {
                            set_page_entry(j, available_frames[start_frame + j], true);
                        }
                        available_frames.erase(available_frames.begin() + start_frame, available_frames.begin() + start_frame + num_pages_);
                        return true;
                    }
                } else {
                    start_frame = i;
                }
            }
            return false;
        } else {
            std::uniform_int_distribution<size_t> frame_dist(0, available_frames.size() - 1);
            std::set<uint64_t> used_frame_numbers;
            uint64_t pages_in_ram = std::min(num_pages_, used_frames * pages_per_frame_);
            for (uint64_t i = 0; i < pages_in_ram; ++i) {
                if (available_frames.empty()) break;
                size_t idx = frame_dist(gen) % available_frames.size();
                uint64_t frame = available_frames[idx];
                set_page_entry(i, frame, true);
                used_frame_numbers.insert(frame);
                if (used_frame_numbers.size() >= used_frames) {
                    available_frames.erase(available_frames.begin() + idx);
                    break;
                }
                available_frames.erase(available_frames.begin() + idx);
            }
            for (uint64_t i = pages_in_ram; i < num_pages_; ++i) {
                set_page_entry(i, i, false); // Swap space
            }
            std::cout << "Allocated " << used_frames << " frames, " << pages_in_ram << " pages in RAM, "
                      << (num_pages_ - pages_in_ram) << " pages in swap\n";
            return true;
        }
    }

    bool access(uint64_t virtual_address) {
        uint64_t page_number = virtual_address / page_size_bytes_;
        if (page_number >= num_pages_) return false;
        uint64_t level1_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = page_number & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second) return false; // Invalid table
        auto& entry = second_level_tables_[level1_idx]->at(level2_idx);
        return !entry.second; // True for page fault (in swap), false for hit (in RAM)
    }

    json export_json() const {
        json pt;
        for (size_t i = 0; i < num_pages_; ++i) {
            uint64_t level1_idx = (i >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level2_idx = i & (entries_per_table_ - 1);
            if (!top_level_table_[level1_idx].second) continue;
            auto& entry = second_level_tables_[level1_idx]->at(level2_idx);
            std::stringstream ss;
            if (entry.second) {
                ss << "0x" << std::hex << entry.first;
            } else {
                ss << "1x" << std::hex << entry.first;
            }
            pt.push_back({{"virtual_page", i}, {"physical_frame", ss.str()}, {"in_ram", entry.second}});
        }
        return pt;
    }

    uint64_t size_bytes() const {
        uint64_t total = top_level_table_.size() * entry_size_;
        for (const auto* table : second_level_tables_) {
            if (table) total += table->size() * entry_size_;
        }
        return total;
    }

private:
    int calculate_levels() {
        int offset_bits = static_cast<int>(log2(page_size_bytes_));
        int index_bits = static_cast<int>(log2(num_pages_)); // log2(total pages)
        return std::max(1, static_cast<int>(ceil(static_cast<double>(index_bits) / bits_per_level_)));
    }

    void initialize_page_tables() {
        top_level_table_.resize(entries_per_table_, {0, false});
        second_level_tables_.resize(entries_per_table_, nullptr);
        for (size_t i = 0; i < num_pages_; ++i) {
            uint64_t level1_idx = (i >> bits_per_level_) & (entries_per_table_ - 1);
            if (!second_level_tables_[level1_idx]) {
                second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                top_level_table_[level1_idx] = {level1_idx, true}; // Mark table as valid
            }
        }
    }

    void set_page_entry(uint64_t page_number, uint64_t frame_number, bool in_ram) {
        uint64_t level1_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = page_number & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx]) {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            top_level_table_[level1_idx] = {level1_idx, true};
        }
        second_level_tables_[level1_idx]->at(level2_idx) = {frame_number, in_ram};
    }

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
    std::vector<std::pair<uint64_t, bool>> top_level_table_;
    std::vector<std::vector<std::pair<uint64_t, bool>>*> second_level_tables_;
};

#endif