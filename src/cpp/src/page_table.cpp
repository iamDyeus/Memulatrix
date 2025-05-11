#include "page_table.h"
#include <cmath>
#include <sstream>
#include <algorithm>

PageTable::PageTable(uint64_t num_pages, uint64_t page_size_bytes, int entry_size, const std::string& allocation_type,
                     uint64_t ram_frames, uint64_t ram_size_bytes, double frame_percent, const std::string& process_id)
    : num_pages_(num_pages), page_size_bytes_(page_size_bytes), entry_size_(entry_size),
      allocation_type_(allocation_type), ram_frames_(ram_frames), ram_size_bytes_(ram_size_bytes),
      process_id_(process_id) {
    max_frames_ = static_cast<uint64_t>(ram_frames * frame_percent / 100.0);
    pages_per_frame_ = page_size_bytes / entry_size;
    entries_per_table_ = page_size_bytes / entry_size; // e.g., 2048 for 4 KB page, 2-byte PTE
    bits_per_level_ = static_cast<int>(log2(entries_per_table_)); // e.g., 11 bits
    levels_ = calculate_levels();
    initialize_page_tables();
    log_page_table_creation();
}

PageTable::~PageTable() {
    for (auto* table : second_level_tables_) {
        delete table;
    }
    for (auto* table : third_level_tables_) {
        delete table;
    }
    for (auto* table : fourth_level_tables_) {
        delete table;
    }
}

int PageTable::calculate_levels() {
    int offset_bits = static_cast<int>(log2(page_size_bytes_));
    int index_bits = static_cast<int>(log2(num_pages_)); // log2(total pages)
    int levels = std::max(1, static_cast<int>(ceil(static_cast<double>(index_bits) / bits_per_level_)));
    return std::min(levels, 4); // Cap at 4 levels
}

void PageTable::initialize_page_tables() {
    std::ofstream debug("debug.txt", std::ios::app);
    if (levels_ == 1) {
        single_level_table_.resize(num_pages_, {0, false});
        debug << "Process " << process_id_ << ": Initialized single-level table with " 
              << num_pages_ << " entries\n";
    } else {
        top_level_table_.resize(entries_per_table_, {0, false});
        second_level_tables_.resize(entries_per_table_, nullptr);
        if (levels_ >= 3) {
            third_level_tables_.resize(entries_per_table_ * entries_per_table_, nullptr);
        }
        if (levels_ == 4) {
            fourth_level_tables_.resize(entries_per_table_ * entries_per_table_ * entries_per_table_, nullptr);
        }
        debug << "Process " << process_id_ << ": Initialized top-level table with " 
              << top_level_table_.size() << " entries\n";
    }
    debug.close();
}

uint64_t PageTable::get_unique_frame(std::vector<uint64_t>& available_frames, std::mt19937& gen) {
    if (available_frames.empty()) {
        return UINT64_MAX; // No frames available
    }
    std::uniform_int_distribution<size_t> frame_dist(0, available_frames.size() - 1);
    size_t idx = frame_dist(gen);
    uint64_t frame = available_frames[idx];
    available_frames.erase(available_frames.begin() + idx);
    return frame;
}

bool PageTable::allocate(uint64_t block_size_bytes, std::vector<uint64_t>& available_frames, std::mt19937& gen) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Allocating " << num_pages_ << " pages\n";

    // Allocate frame for top-level table
    uint64_t top_level_frame = get_unique_frame(available_frames, gen);
    if (top_level_frame == UINT64_MAX) {
        debug << "Process " << process_id_ << ": Failed to allocate top-level table frame\n";
        debug.close();
        return false;
    }
    ram_[top_level_frame] = "top_level_table_" + process_id_;
    top_level_table_[0] = {top_level_frame, true}; // Mark top-level table as valid
    debug << "Process " << process_id_ << ": Allocated top-level table in frame " 
          << top_level_frame << "\n";

    // Calculate pages per table at each level
    std::vector<uint64_t> pages_per_table(levels_ + 1, 1);
    for (int i = 1; i <= levels_; ++i) {
        pages_per_table[i] = pages_per_table[i - 1] * entries_per_table_;
    }

    // Allocate data pages and leaf tables
    std::vector<std::vector<std::pair<uint64_t, bool>>*> current_level_tables = second_level_tables_;
    uint64_t pages_in_current_table = 0;
    uint64_t current_table_idx = 0;
    std::vector<std::pair<uint64_t, bool>>* leaf_table = nullptr;

    for (uint64_t page = 1; page <= num_pages_; ++page) {
        // Allocate frame for data page
        uint64_t frame = get_unique_frame(available_frames, gen);
        if (frame == UINT64_MAX) {
            debug << "Process " << process_id_ << ": Failed to allocate frame for page " << page << "\n";
            debug.close();
            return false;
        }
        ram_[frame] = "page_" + std::to_string(page) + "_" + process_id_;
        entries_[page] = frame;
        set_page_entry(page - 1, frame, true); // 0-based internally
        debug << "Process " << process_id_ << ": Setting page " << page << " to frame " 
              << frame << ", in RAM: 1\n";

        // Handle leaf table creation
        if (levels_ == 1) {
            continue; // Single-level table handled by set_page_entry
        }
        if (pages_in_current_table == 0) {
            // Start a new leaf table
            leaf_table = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            uint64_t table_frame = get_unique_frame(available_frames, gen);
            if (table_frame == UINT64_MAX) {
                debug << "Process " << process_id_ << ": Failed to allocate frame for leaf table " 
                      << current_table_idx << "\n";
                debug.close();
                delete leaf_table;
                return false;
            }
            ram_[table_frame] = "level_" + std::to_string(levels_) + "_table_" + 
                                std::to_string(current_table_idx) + "_" + process_id_;
            debug << "Process " << process_id_ << ": Allocated level " << levels_ << " table " 
                  << current_table_idx << " in frame " << table_frame << "\n";

            // Link to parent table
            uint64_t parent_idx = current_table_idx;
            if (levels_ == 2) {
                second_level_tables_[parent_idx] = leaf_table;
                top_level_table_[parent_idx] = {table_frame, true};
            } else if (levels_ == 3) {
                uint64_t l2_idx = parent_idx % entries_per_table_;
                uint64_t l1_idx = parent_idx / entries_per_table_;
                third_level_tables_[l1_idx * entries_per_table_ + l2_idx] = leaf_table;
                if (!second_level_tables_[l1_idx]) {
                    second_level_tables_[l1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                    uint64_t l2_frame = get_unique_frame(available_frames, gen);
                    if (l2_frame == UINT64_MAX) {
                        debug << "Process " << process_id_ << ": Failed to allocate frame for level 2 table " 
                              << l1_idx << "\n";
                        debug.close();
                        delete leaf_table;
                        return false;
                    }
                    ram_[l2_frame] = "level_2_table_" + std::to_string(l1_idx) + "_" + process_id_;
                    top_level_table_[l1_idx] = {l2_frame, true};
                    debug << "Process " << process_id_ << ": Allocated level 2 table " 
                          << l1_idx << " in frame " << l2_frame << "\n";
                }
                second_level_tables_[l1_idx]->at(l2_idx) = {table_frame, true};
            } else if (levels_ == 4) {
                uint64_t l3_idx = parent_idx % entries_per_table_;
                uint64_t l2_idx = (parent_idx / entries_per_table_) % entries_per_table_;
                uint64_t l1_idx = parent_idx / (entries_per_table_ * entries_per_table_);
                fourth_level_tables_[l1_idx * entries_per_table_ * entries_per_table_ + l2_idx * entries_per_table_ + l3_idx] = leaf_table;
                if (!third_level_tables_[l1_idx * entries_per_table_ + l2_idx]) {
                    third_level_tables_[l1_idx * entries_per_table_ + l2_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                    uint64_t l3_frame = get_unique_frame(available_frames, gen);
                    if (l3_frame == UINT64_MAX) {
                        debug << "Process " << process_id_ << ": Failed to allocate frame for level 3 table " 
                              << (l1_idx * entries_per_table_ + l2_idx) << "\n";
                        debug.close();
                        delete leaf_table;
                        return false;
                    }
                    ram_[l3_frame] = "level_3_table_" + std::to_string(l1_idx * entries_per_table_ + l2_idx) + "_" + process_id_;
                    if (!second_level_tables_[l1_idx]) {
                        second_level_tables_[l1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                        uint64_t l2_frame = get_unique_frame(available_frames, gen);
                        if (l2_frame == UINT64_MAX) {
                            debug << "Process " << process_id_ << ": Failed to allocate frame for level 2 table " 
                                  << l1_idx << "\n";
                            debug.close();
                            delete leaf_table;
                            return false;
                        }
                        ram_[l2_frame] = "level_2_table_" + std::to_string(l1_idx) + "_" + process_id_;
                        top_level_table_[l1_idx] = {l2_frame, true};
                        debug << "Process " << process_id_ << ": Allocated level 2 table " 
                              << l1_idx << " in frame " << l2_frame << "\n";
                    }
                    second_level_tables_[l1_idx]->at(l2_idx) = {l3_frame, true};
                    debug << "Process " << process_id_ << ": Allocated level 3 table " 
                          << (l1_idx * entries_per_table_ + l2_idx) << " in frame " << l3_frame << "\n";
                }
                third_level_tables_[l1_idx * entries_per_table_ + l2_idx]->at(l3_idx) = {table_frame, true};
            }
        }

        pages_in_current_table++;
        if (pages_in_current_table == entries_per_table_ || page == num_pages_) {
            pages_in_current_table = 0;
            current_table_idx++;
        }
    }

    debug << "Process " << process_id_ << ": Allocated " << entries_.size() << " pages in RAM, " 
          << (num_pages_ - entries_.size()) << " pages in swap\n";
    debug.close();
    return true;
}

bool PageTable::access(uint64_t virtual_address) {
    uint64_t page_number = virtual_address / page_size_bytes_;
    if (page_number >= num_pages_) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id_ << ": Invalid page number " << (page_number + 1) << "\n";
        debug.close();
        return false;
    }

    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Accessing virtual address 0x" 
          << std::hex << virtual_address << ", page " << std::dec << (page_number + 1) << "\n";

    if (levels_ == 1) {
        auto& entry = single_level_table_[page_number];
        debug << "Process " << process_id_ << ": Single-level access, page " << (page_number + 1) 
              << ", in RAM: " << entry.second << "\n";
        debug.close();
        return !entry.second;
    } else if (levels_ == 2) {
        uint64_t level1_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = page_number & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second) {
            debug << "Process " << process_id_ << ": Invalid level 1 table at index " << level1_idx << "\n";
            debug.close();
            return false;
        }
        auto& entry = second_level_tables_[level1_idx]->at(level2_idx);
        debug << "Process " << process_id_ << ": Two-level access, L1 idx " << level1_idx 
              << ", L2 idx " << (level2_idx + 1) << ", in RAM: " << entry.second << "\n";
        debug.close();
        return !entry.second;
    } else if (levels_ == 3) {
        uint64_t level1_idx = (page_number >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level3_idx = page_number & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second || !second_level_tables_[level1_idx]->at(level2_idx).second) {
            debug << "Process " << process_id_ << ": Invalid table at L1 idx " << level1_idx 
                  << ", L2 idx " << level2_idx << "\n";
            debug.close();
            return false;
        }
        auto& entry = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx);
        debug << "Process " << process_id_ << ": Three-level access, L1 idx " << level1_idx 
              << ", L2 idx " << level2_idx << ", L3 idx " << (level3_idx + 1) << ", in RAM: " << entry.second << "\n";
        debug.close();
        return !entry.second;
    } else {
        uint64_t level1_idx = (page_number >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level3_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level4_idx = page_number & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second || 
            !second_level_tables_[level1_idx]->at(level2_idx).second ||
            !third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second) {
            debug << "Process " << process_id_ << ": Invalid table at L1 idx " << level1_idx 
                  << ", L2 idx " << level2_idx << ", L3 idx " << level3_idx << "\n";
            debug.close();
            return false;
        }
        auto& entry = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ + 
                                           level2_idx * entries_per_table_ + level3_idx)]->at(level4_idx);
        debug << "Process " << process_id_ << ": Four-level access, L1 idx " << level1_idx 
              << ", L2 idx " << level2_idx << ", L3 idx " << level3_idx << ", L4 idx " << (level4_idx + 1) 
              << ", in RAM: " << entry.second << "\n";
        debug.close();
        return !entry.second;
    }
}

json PageTable::export_json() const {
    json pt;
    for (uint64_t i = 0; i < num_pages_; ++i) {
        uint64_t frame_number = 0;
        bool in_ram = false;
        if (levels_ == 1) {
            frame_number = single_level_table_[i].first;
            in_ram = single_level_table_[i].second;
        } else if (levels_ == 2) {
            uint64_t level1_idx = (i >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level2_idx = i & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second) {
                frame_number = second_level_tables_[level1_idx]->at(level2_idx).first;
                in_ram = second_level_tables_[level1_idx]->at(level2_idx).second;
            }
        } else if (levels_ == 3) {
            uint64_t level1_idx = (i >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level2_idx = (i >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level3_idx = i & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second && second_level_tables_[level1_idx]->at(level2_idx).second) {
                frame_number = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).first;
                in_ram = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second;
            }
        } else {
            uint64_t level1_idx = (i >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level2_idx = (i >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level3_idx = (i >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level4_idx = i & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second && 
                second_level_tables_[level1_idx]->at(level2_idx).second &&
                third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second) {
                frame_number = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ + 
                                                   level2_idx * entries_per_table_ + level3_idx)]->at(level4_idx).first;
                in_ram = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ + 
                                             level2_idx * entries_per_table_ + level3_idx)]->at(level4_idx).second;
            }
        }
        std::stringstream ss;
        if (in_ram) {
            ss << "0x" << std::hex << frame_number;
        } else {
            ss << "1x" << std::hex << frame_number;
        }
        pt.push_back({{"virtual_page", i + 1}, {"physical_frame", ss.str()}, {"in_ram", in_ram}});
    }
    return pt;
}

uint64_t PageTable::size_bytes() const {
    uint64_t total = 0;
    if (levels_ == 1) {
        total = single_level_table_.size() * entry_size_;
    } else {
        total = top_level_table_.size() * entry_size_;
        for (const auto* table : second_level_tables_) {
            if (table) total += table->size() * entry_size_;
        }
        for (const auto* table : third_level_tables_) {
            if (table) total += table->size() * entry_size_;
        }
        for (const auto* table : fourth_level_tables_) {
            if (table) total += table->size() * entry_size_;
        }
    }
    return total;
}

uint64_t PageTable::lookup(uint64_t page_number) const {
    if (page_number < 1 || page_number > num_pages_) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id_ << ": Invalid page number " << page_number << "\n";
        debug.close();
        return UINT64_MAX;
    }
    uint64_t internal_page = page_number - 1; // Convert to 0-based
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Looking up page " << page_number << "\n";

    uint64_t frame_number = entries_.at(page_number);
    if (levels_ == 1) {
        debug << "Process " << process_id_ << ": Single-level table, page " << page_number 
              << ", frame " << frame_number << "\n";
    } else {
        // Calculate indices for each level
        std::vector<uint64_t> indices(levels_);
        uint64_t temp_page = internal_page;
        for (int i = levels_ - 1; i >= 0; --i) {
            indices[i] = temp_page & (entries_per_table_ - 1);
            temp_page >>= bits_per_level_;
        }
        debug << "Process " << process_id_ << ": Level " << levels_ << " table, ";
        for (int i = 0; i < levels_; ++i) {
            debug << "L" << (i + 1) << " idx " << indices[i];
            if (i == levels_ - 1) {
                debug << " (offset " << (indices[i] + 1) << ")";
            }
            if (i < levels_ - 1) debug << ", ";
        }
        debug << ", frame " << frame_number << "\n";
    }
    debug.close();
    return frame_number;
}

void PageTable::set_page_entry(uint64_t page_number, uint64_t frame_number, bool in_ram) {
    if (levels_ == 1) {
        single_level_table_[page_number] = {frame_number, in_ram};
    } else if (levels_ == 2) {
        uint64_t level1_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = page_number & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx]) {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        second_level_tables_[level1_idx]->at(level2_idx) = {frame_number, in_ram};
    } else if (levels_ == 3) {
        uint64_t level1_idx = (page_number >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level3_idx = page_number & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx]) {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        size_t l3_idx = level1_idx * entries_per_table_ + level2_idx;
        if (!third_level_tables_[l3_idx]) {
            third_level_tables_[l3_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            second_level_tables_[level1_idx]->at(level2_idx) = {l3_idx, true};
        }
        third_level_tables_[l3_idx]->at(level3_idx) = {frame_number, in_ram};
    } else {
        uint64_t level1_idx = (page_number >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level3_idx = (page_number >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level4_idx = page_number & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx]) {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        size_t l3_idx = level1_idx * entries_per_table_ + level2_idx;
        if (!third_level_tables_[l3_idx]) {
            third_level_tables_[l3_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            second_level_tables_[level1_idx]->at(level2_idx) = {l3_idx, true};
        }
        size_t l4_idx = (level1_idx * entries_per_table_ * entries_per_table_ + 
                        level2_idx * entries_per_table_ + level3_idx);
        if (!fourth_level_tables_[l4_idx]) {
            fourth_level_tables_[l4_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            third_level_tables_[l3_idx]->at(level3_idx) = {l4_idx, true};
        }
        fourth_level_tables_[l4_idx]->at(level4_idx) = {frame_number, in_ram};
    }
}

void PageTable::log_page_table_creation() {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Created page table with " << levels_ << " levels, "
          << num_pages_ << " pages, " << entries_per_table_ << " entries per table\n";
    if (levels_ == 1) {
        debug << "Process " << process_id_ << ": Single-level table with " 
              << single_level_table_.size() << " entries\n";
    } else {
        debug << "Process " << process_id_ << ": Top-level table with " 
              << top_level_table_.size() << " entries\n";
        int second_level_count = 0;
        for (const auto* table : second_level_tables_) {
            if (table) second_level_count++;
        }
        debug << "Process " << process_id_ << ": " << second_level_count 
              << " second-level tables\n";
        if (levels_ >= 3) {
            int third_level_count = 0;
            for (const auto* table : third_level_tables_) {
                if (table) third_level_count++;
            }
            debug << "Process " << process_id_ << ": " << third_level_count 
                  << " third-level tables\n";
        }
        if (levels_ == 4) {
            int fourth_level_count = 0;
            for (const auto* table : fourth_level_tables_) {
                if (table) fourth_level_count++;
            }
            debug << "Process " << process_id_ << ": " << fourth_level_count 
                  << " fourth-level tables\n";
        }
    }
    debug.close();
}