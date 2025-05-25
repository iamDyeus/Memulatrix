#include "page_table.h"
#include <fstream>
#include <cmath>
#include <sstream>
#include <algorithm>
#include <iomanip>
#include <random>

uint64_t PageTable::last_used_frame_ = 0;

uint64_t PageTable::get_last_used_frame()
{
    return last_used_frame_;
}

PageTable::PageTable(uint64_t num_pages, uint64_t page_size_bytes, int entry_size, const std::string &allocation_type,
                     uint64_t ram_frames, uint64_t total_frames, uint64_t ram_size_bytes, double frame_percent,
                     const std::string &process_id, const std::string &virtual_address_size)
    : num_pages_(num_pages), page_size_bytes_(page_size_bytes), entry_size_(entry_size),
      allocation_type_(allocation_type), ram_frames_(ram_frames), total_frames_(total_frames),
      ram_size_bytes_(ram_size_bytes), process_id_(process_id), virtual_address_size_(virtual_address_size),
      top_level_frame_(0)
{
    std::ofstream debug("debug.txt", std::ios::app);
    max_frames_ = static_cast<uint64_t>(ram_frames * frame_percent / 100.0);
    pages_per_frame_ = page_size_bytes / entry_size;
    entries_per_table_ = page_size_bytes / entry_size;
    bits_per_level_ = static_cast<int>(log2(entries_per_table_));
    levels_ = calculate_levels();

    debug << "Process " << process_id_ << ": Initializing page table\n"
          << "  Num pages: " << num_pages_ << "\n"
          << "  Page size: " << page_size_bytes_ << " bytes\n"
          << "  Entry size: " << entry_size_ << " bytes\n"
          << "  Entries per table: " << entries_per_table_ << "\n"
          << "  Bits per level: " << bits_per_level_ << "\n"
          << "  Number of levels: " << levels_ << "\n";

    // Calculate total entries needed at each level
    uint64_t total_entries = num_pages_;
    std::vector<uint64_t> entries_at_level(levels_);
    for (int i = levels_ - 1; i >= 0; --i)
    {
        entries_at_level[i] = (total_entries + entries_per_table_ - 1) / entries_per_table_;
        total_entries = entries_at_level[i];
    }

    debug << "Table structure:\n";
    for (int i = 0; i < levels_; ++i)
    {
        debug << "  Level " << (i + 1) << ": " << entries_at_level[i] << " tables needed\n";
    }

    initialize_page_tables();
    log_page_table_creation();
    debug.close();
}

PageTable::~PageTable()
{
    for (auto *table : second_level_tables_)
    {
        delete table;
    }
    for (auto *table : third_level_tables_)
    {
        delete table;
    }
    for (auto *table : fourth_level_tables_)
    {
        delete table;
    }
}

int PageTable::calculate_levels()
{
    int offset_bits = static_cast<int>(log2(page_size_bytes_));
    int index_bits = static_cast<int>(log2(num_pages_));
    int levels = std::max(1, static_cast<int>(ceil(static_cast<double>(index_bits) / bits_per_level_)));
    return std::min(levels, 4);
}

void PageTable::initialize_page_tables()
{
    std::ofstream debug("debug.txt", std::ios::app);
    if (levels_ == 1)
    {
        single_level_table_.resize(num_pages_, {0, false});
        debug << "Process " << process_id_ << ": Initialized single-level table with "
              << num_pages_ << " entries\n";
    }
    else
    {
        top_level_table_.resize(entries_per_table_, {0, false});
        second_level_tables_.resize(entries_per_table_, nullptr);
        if (levels_ >= 3)
        {
            third_level_tables_.resize(entries_per_table_ * entries_per_table_, nullptr);
        }
        if (levels_ == 4)
        {
            fourth_level_tables_.resize(entries_per_table_ * entries_per_table_ * entries_per_table_, nullptr);
        }
        debug << "Process " << process_id_ << ": Initialized top-level table with "
              << top_level_table_.size() << " entries\n";
    }
    debug.close();
}

uint64_t PageTable::get_unique_frame(std::vector<uint64_t> &available_frames, std::mt19937 &gen)
{
    if (available_frames.empty())
    {
        return UINT64_MAX;
    }
    std::uniform_int_distribution<size_t> frame_dist(0, available_frames.size() - 1);
    size_t idx = frame_dist(gen);
    uint64_t frame = available_frames[idx];
    if (frame >= total_frames_)
    {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id_ << ": Invalid frame 0x" << std::hex << frame
              << " exceeds total frames 0x" << total_frames_ << "\n";
        debug.close();
        return UINT64_MAX;
    }
    available_frames.erase(available_frames.begin() + idx);
    return frame;
}

uint64_t PageTable::get_unique_swap_frame(std::vector<uint64_t> &available_swap_frames, std::mt19937 &gen)
{
    if (available_swap_frames.empty())
    {
        return UINT64_MAX;
    }
    std::uniform_int_distribution<size_t> frame_dist(0, available_swap_frames.size() - 1);
    size_t idx = frame_dist(gen);
    uint64_t frame = available_swap_frames[idx];
    available_swap_frames.erase(available_swap_frames.begin() + idx);
    return frame;
}

void PageTable::free_frames(std::vector<uint64_t> &available_frames, std::vector<uint64_t> &available_table_frames)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Freeing frames\n";
    for (auto it = ram_.begin(); it != ram_.end();)
    {
        uint64_t frame = it->first;
        if (it->second.first.find("table_") != std::string::npos)
        {
            available_table_frames.push_back(frame);
            debug << "Freed table frame 0x" << std::hex << frame << "\n";
        }
        else
        {
            available_frames.push_back(frame);
            debug << "Freed data frame 0x" << std::hex << frame << "\n";
        }
        it = ram_.erase(it);
    }
    debug.close();
}

void PageTable::free_swap_frames(std::vector<uint64_t> &available_swap_frames)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Freeing swap frames\n";
    for (auto it = swap_map_.begin(); it != swap_map_.end();)
    {
        std::string key = it->first;
        uint64_t frame = std::stoull(key.substr(2), nullptr, 16);
        available_swap_frames.push_back(frame);
        debug << "Freed swap frame 0x" << std::hex << frame << "\n";
        it = swap_map_.erase(it);
    }
    debug.close();
}

void PageTable::set_frame_availability(bool available)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Setting frame availability to " << (available ? "true" : "false") << "\n";
    for (auto &entry : ram_)
    {
        entry.second.second = available;
    }
    debug.close();
}

bool PageTable::allocate(uint64_t block_size_bytes, std::vector<uint64_t> &available_frames,
                         std::vector<uint64_t> &available_table_frames, std::mt19937 &gen,
                         std::vector<uint64_t> &available_swap_frames)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Allocating " << num_pages_ << " pages\n";

    top_level_frame_ = get_unique_frame(available_table_frames, gen);
    if (top_level_frame_ == UINT64_MAX)
    {
        debug << "Process " << process_id_ << ": Failed to allocate top-level table frame\n";
        debug.close();
        return false;
    }
    ram_[top_level_frame_] = {"top_level_table_" + process_id_, true};
    if (levels_ > 1)
    {
        top_level_table_[0] = {top_level_frame_, true};
    }
    debug << "Process " << process_id_ << ": Allocated top-level table in frame 0x" << std::hex << top_level_frame_ << std::dec << "\n";

    std::vector<uint64_t> pages_per_table(levels_ + 1, 1);
    for (int i = 1; i <= levels_; ++i)
    {
        pages_per_table[i] = pages_per_table[i - 1] * entries_per_table_;
    }

    std::vector<std::vector<std::pair<uint64_t, bool>> *> current_level_tables = second_level_tables_;
    uint64_t pages_in_current_table = 0;
    uint64_t current_table_idx = 0;
    std::vector<std::pair<uint64_t, bool>> *leaf_table = nullptr;

    uint64_t pages_in_swap = 0;
    bool use_swap = !available_swap_frames.empty();

    if (allocation_type_ == "Contiguous")
    {
        uint64_t table_frame_limit = static_cast<uint64_t>(ceil(total_frames_ * 0.01));
        uint64_t start_frame = (last_used_frame_ == 0) ? table_frame_limit : last_used_frame_ + 1;
        if (start_frame < table_frame_limit)
        {
            start_frame = table_frame_limit;
        }
        uint64_t ram_pages = num_pages_;
        bool can_allocate = true;

        if (num_pages_ > available_frames.size())
        {
            ram_pages = available_frames.size();
            pages_in_swap = num_pages_ - ram_pages;
            if (pages_in_swap > available_swap_frames.size())
            {
                debug << "Process " << process_id_ << ": Insufficient swap frames for "
                      << pages_in_swap << " pages\n";
                debug.close();
                return false;
            }
        }

        for (uint64_t i = 0; i < ram_pages; ++i)
        {
            if (std::find(available_frames.begin(), available_frames.end(), start_frame + i) == available_frames.end())
            {
                debug << "Process " << process_id_ << ": Contiguous RAM block from 0x" << std::hex << start_frame
                      << " not available\n";
                debug.close();
                return false;
            }
        }

        for (uint64_t i = 0; i < pages_in_swap; ++i)
        {
            if (std::find(available_swap_frames.begin(), available_swap_frames.end(), i) == available_swap_frames.end())
            {
                debug << "Process " << process_id_ << ": Contiguous swap block from 0x0 not available\n";
                debug.close();
                return false;
            }
        }

        for (uint64_t page = 1; page <= ram_pages; ++page)
        {
            uint64_t frame = start_frame + (page - 1);
            auto it = std::find(available_frames.begin(), available_frames.end(), frame);
            available_frames.erase(it);
            ram_[frame] = {"page_" + std::to_string(page) + "_" + process_id_, true};
            entries_[page] = frame;
            set_page_entry(page, frame, true);
        }

        for (uint64_t page = ram_pages + 1; page <= num_pages_; ++page)
        {
            uint64_t frame = page - ram_pages - 1;
            auto it = std::find(available_swap_frames.begin(), available_swap_frames.end(), frame);
            available_swap_frames.erase(it);
            std::stringstream ss;
            ss << "1x" << std::hex << frame;
            swap_map_[ss.str()] = "PID" + process_id_ + "_page" + std::to_string(page);
            ram_[frame] = {"swap_page_" + std::to_string(page) + "_" + process_id_, true};
            entries_[page] = frame;
            set_page_entry(page, frame, false);
        }

        last_used_frame_ = (ram_pages > 0) ? (start_frame + ram_pages - 1) : last_used_frame_;
        if (pages_in_swap > 0)
        {
            last_used_frame_ = std::max(last_used_frame_, pages_in_swap - 1);
        }
    }
    else
    {
        for (uint64_t page = 1; page <= num_pages_; ++page)
        {
            uint64_t frame = 0;
            bool in_ram = true;
            std::stringstream ss;
            if (use_swap && available_frames.empty())
            {
                frame = get_unique_swap_frame(available_swap_frames, gen);
                if (frame == UINT64_MAX)
                {
                    debug << "Process " << process_id_ << ": Insufficient swap frames for page " << page << "\n";
                    debug.close();
                    return false;
                }
                in_ram = false;
                ss << "1x" << std::hex << frame;
                swap_map_[ss.str()] = "PID" + process_id_ + "_page" + std::to_string(page);
                ram_[frame] = {"swap_page_" + std::to_string(page) + "_" + process_id_, true};
                pages_in_swap++;
            }
            else
            {
                frame = get_unique_frame(available_frames, gen);
                if (frame == UINT64_MAX)
                {
                    if (use_swap)
                    {
                        frame = get_unique_swap_frame(available_swap_frames, gen);
                        if (frame == UINT64_MAX)
                        {
                            debug << "Process " << process_id_ << ": Insufficient swap frames for page " << page << "\n";
                            debug.close();
                            return false;
                        }
                        in_ram = false;
                        ss << "1x" << std::hex << frame;
                        swap_map_[ss.str()] = "PID" + process_id_ + "_page" + std::to_string(page);
                        ram_[frame] = {"swap_page_" + std::to_string(page) + "_" + process_id_, true};
                        pages_in_swap++;
                    }
                    else
                    {
                        debug << "Process " << process_id_ << ": Failed to allocate data frame for page " << page << "\n";
                        debug.close();
                        return false;
                    }
                }
                if (in_ram)
                {
                    ram_[frame] = {"page_" + std::to_string(page) + "_" + process_id_, true};
                }
            }
            entries_[page] = frame;
            set_page_entry(page, frame, in_ram);
            last_used_frame_ = std::max(last_used_frame_, frame);
        }
    }

    if (levels_ > 1)
    {
        for (uint64_t page = 1; page <= num_pages_; ++page)
        {
            if (pages_in_current_table == 0)
            {
                leaf_table = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                uint64_t table_frame = get_unique_frame(available_table_frames, gen);
                if (table_frame == UINT64_MAX)
                {
                    debug << "Process " << process_id_ << ": Failed to allocate frame for leaf table "
                          << current_table_idx << "\n";
                    debug.close();
                    delete leaf_table;
                    return false;
                }
                ram_[table_frame] = {"level_" + std::to_string(levels_) + "_table_" +
                                         std::to_string(current_table_idx) + "_" + process_id_,
                                     true};
                uint64_t parent_idx = current_table_idx;
                if (levels_ == 2)
                {
                    second_level_tables_[parent_idx] = leaf_table;
                    top_level_table_[parent_idx] = {table_frame, true};
                }
                else if (levels_ == 3)
                {
                    uint64_t l2_idx = parent_idx % entries_per_table_;
                    uint64_t l1_idx = parent_idx / entries_per_table_;
                    third_level_tables_[l1_idx * entries_per_table_ + l2_idx] = leaf_table;
                    if (!second_level_tables_[l1_idx])
                    {
                        second_level_tables_[l1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                        uint64_t l2_frame = get_unique_frame(available_table_frames, gen);
                        if (l2_frame == UINT64_MAX)
                        {
                            debug << "Process " << process_id_ << ": Failed to allocate frame for level 2 table "
                                  << l1_idx << "\n";
                            debug.close();
                            delete leaf_table;
                            return false;
                        }
                        ram_[l2_frame] = {"level_2_table_" + std::to_string(l1_idx) + "_" + process_id_, true};
                        top_level_table_[l1_idx] = {l2_frame, true};
                    }
                    second_level_tables_[l1_idx]->at(l2_idx) = {table_frame, true};
                }
                else if (levels_ == 4)
                {
                    uint64_t l3_idx = parent_idx % entries_per_table_;
                    uint64_t l2_idx = (parent_idx / entries_per_table_) % entries_per_table_;
                    uint64_t l1_idx = parent_idx / (entries_per_table_ * entries_per_table_);
                    fourth_level_tables_[l1_idx * entries_per_table_ * entries_per_table_ + l2_idx * entries_per_table_ + l3_idx] = leaf_table;
                    if (!third_level_tables_[l1_idx * entries_per_table_ + l2_idx])
                    {
                        third_level_tables_[l1_idx * entries_per_table_ + l2_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                        uint64_t l3_frame = get_unique_frame(available_table_frames, gen);
                        if (l3_frame == UINT64_MAX)
                        {
                            debug << "Process " << process_id_ << ": Failed to allocate frame for level 3 table "
                                  << (l1_idx * entries_per_table_ + l2_idx) << "\n";
                            debug.close();
                            delete leaf_table;
                            return false;
                        }
                        ram_[l3_frame] = {"level_3_table_" + std::to_string(l1_idx * entries_per_table_ + l2_idx) + "_" + process_id_, true};
                        if (!second_level_tables_[l1_idx])
                        {
                            second_level_tables_[l1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
                            uint64_t l2_frame = get_unique_frame(available_table_frames, gen);
                            if (l2_frame == UINT64_MAX)
                            {
                                debug << "Process " << process_id_ << ": Failed to allocate frame for level 2 table "
                                      << l1_idx << "\n";
                                debug.close();
                                delete leaf_table;
                                return false;
                            }
                            ram_[l2_frame] = {"level_2_table_" + std::to_string(l1_idx) + "_" + process_id_, true};
                            top_level_table_[l1_idx] = {l2_frame, true};
                        }
                        second_level_tables_[l1_idx]->at(l2_idx) = {l3_frame, true};
                    }
                    third_level_tables_[l1_idx * entries_per_table_ + l2_idx]->at(l3_idx) = {table_frame, true};
                }
            }

            pages_in_current_table++;
            if (pages_in_current_table == entries_per_table_ || page == num_pages_)
            {
                pages_in_current_table = 0;
                current_table_idx++;
            }
        }
    }
    debug << "Process " << process_id_ << ": Allocated " << (num_pages_ - pages_in_swap)
          << " pages in RAM, " << pages_in_swap << " pages in swap\n";
    log_swap_map();
    debug.close();
    return true;
}

void PageTable::log_swap_map() const
{
    std::ofstream debug("debug.txt", std::ios::app);
    if (!swap_map_.empty())
    {
        debug << "Process " << process_id_ << ": Swap space map:\n";
        for (const auto &entry : swap_map_)
        {
            debug << entry.first << ": " << entry.second << "\n";
        }
    }
    debug.close();
}

bool PageTable::access(uint64_t virtual_address)
{
    uint64_t page_number = virtual_address / page_size_bytes_ + 1;
    if (page_number < 1 || page_number > num_pages_)
    {
        return false;
    }

    if (levels_ == 1)
    {
        auto &entry = single_level_table_[page_number - 1];
        return !entry.second;
    }
    else if (levels_ == 2)
    {
        uint64_t level1_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second)
        {
            return false;
        }
        auto &entry = second_level_tables_[level1_idx]->at(level2_idx);
        return !entry.second;
    }
    else if (levels_ == 3)
    {
        uint64_t level1_idx = ((page_number - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level3_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second || !second_level_tables_[level1_idx]->at(level2_idx).second)
        {
            return false;
        }
        auto &entry = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx);
        return !entry.second;
    }
    else
    {
        uint64_t level1_idx = ((page_number - 1) >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = ((page_number - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level3_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level4_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!top_level_table_[level1_idx].second ||
            !second_level_tables_[level1_idx]->at(level2_idx).second ||
            !third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second)
        {
            return false;
        }
        auto &entry = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ +
                                            level2_idx * entries_per_table_ + level3_idx)]
                          ->at(level4_idx);
        return !entry.second;
    }
}

json PageTable::export_json() const
{
    json pt;
    int hex_digits = static_cast<int>(ceil(log2(ram_size_bytes_) / 4.0));
    for (uint64_t i = 1; i <= num_pages_; ++i)
    {
        uint64_t frame_number = 0;
        bool in_ram = false;
        if (levels_ == 1)
        {
            frame_number = single_level_table_[i - 1].first;
            in_ram = single_level_table_[i - 1].second;
        }
        else if (levels_ == 2)
        {
            uint64_t level1_idx = ((i - 1) >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level2_idx = (i - 1) & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second)
            {
                frame_number = second_level_tables_[level1_idx]->at(level2_idx).first;
                in_ram = second_level_tables_[level1_idx]->at(level2_idx).second;
            }
        }
        else if (levels_ == 3)
        {
            uint64_t level1_idx = ((i - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level2_idx = ((i - 1) >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level3_idx = (i - 1) & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second && second_level_tables_[level1_idx]->at(level2_idx).second)
            {
                frame_number = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).first;
                in_ram = third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second;
            }
        }
        else
        {
            uint64_t level1_idx = ((i - 1) >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level2_idx = ((i - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
            uint64_t level3_idx = ((i - 1) >> bits_per_level_) & (entries_per_table_ - 1);
            uint64_t level4_idx = (i - 1) & (entries_per_table_ - 1);
            if (top_level_table_[level1_idx].second &&
                second_level_tables_[level1_idx]->at(level2_idx).second &&
                third_level_tables_[level1_idx * entries_per_table_ + level2_idx]->at(level3_idx).second)
            {
                frame_number = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ +
                                                     level2_idx * entries_per_table_ + level3_idx)]
                                   ->at(level4_idx)
                                   .first;
                in_ram = fourth_level_tables_[(level1_idx * entries_per_table_ * entries_per_table_ +
                                               level2_idx * entries_per_table_ + level3_idx)]
                             ->at(level4_idx)
                             .second;
            }
        }
        std::stringstream ss;
        ss << std::noshowbase;
        if (in_ram)
        {
            ss << "0x" << std::hex << frame_number;
        }
        else
        {
            ss << "1x" << std::hex << frame_number;
        }
        std::stringstream va_ss;
        uint64_t virtual_address = (i - 1) * page_size_bytes_;
        if (virtual_address_size_ == "16-bit")
        {
            va_ss << "0x" << std::hex << std::setfill('0') << std::setw(4) << virtual_address;
        }
        else if (virtual_address_size_ == "32-bit")
        {
            va_ss << "0x" << std::hex << std::setfill('0') << std::setw(8) << virtual_address;
        }
        else
        {
            va_ss << "0x" << std::hex << std::setfill('0') << std::setw(16) << virtual_address;
        }
        pt.push_back({{"process_id", process_id_},
                      {"page_number", i},
                      {"virtual_address", va_ss.str()},
                      {"physical_frame", ss.str()},
                      {"in_ram", in_ram}});
    }
    return pt;
}

uint64_t PageTable::size_bytes() const
{
    uint64_t total = 0;
    if (levels_ == 1)
    {
        total = single_level_table_.size() * entry_size_;
    }
    else
    {
        total = top_level_table_.size() * entry_size_;
        for (const auto *table : second_level_tables_)
        {
            if (table)
                total += table->size() * entry_size_;
        }
        for (const auto *table : third_level_tables_)
        {
            if (table)
                total += table->size() * entry_size_;
        }
        for (const auto *table : fourth_level_tables_)
        {
            if (table)
                total += table->size() * entry_size_;
        }
    }
    return total;
}

uint64_t PageTable::lookup(uint64_t page_number) const
{
    if (page_number < 1 || page_number > num_pages_)
    {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id_ << ": Invalid page number " << page_number << "\n";
        debug.close();
        return UINT64_MAX;
    }
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Looking up page " << page_number << "\n";

    auto it = entries_.find(page_number);
    if (it == entries_.end())
    {
        debug << "Process " << process_id_ << ": Page " << page_number << " not found in entries\n";
        debug.close();
        return UINT64_MAX;
    }
    uint64_t frame_number = it->second;
    if (levels_ == 1)
    {
        debug << std::noshowbase << "Process " << process_id_ << ": Single-level table, page " << std::dec
              << page_number << ", frame 0x" << std::hex << frame_number << std::dec << "\n";
    }
    else
    {
        std::vector<uint64_t> indices(levels_);
        uint64_t temp_page = page_number - 1;
        for (int i = levels_ - 1; i >= 0; --i)
        {
            indices[i] = temp_page & (entries_per_table_ - 1);
            temp_page >>= bits_per_level_;
        }
        debug << "Process " << process_id_ << ": Level " << levels_ << " table, ";
        for (int i = 0; i < levels_; ++i)
        {
            debug << "L" << (i + 1) << " idx " << indices[i];
            if (i == levels_ - 1)
            {
                debug << " (offset " << (indices[i] + 1) << ")";
            }
            if (i < levels_ - 1)
                debug << ", ";
        }
        debug << ", frame 0x" << std::hex << frame_number << std::dec << "\n";
    }
    debug.close();
    return frame_number;
}

void PageTable::set_page_entry(uint64_t page_number, uint64_t frame_number, bool in_ram)
{
    if (levels_ == 1)
    {
        single_level_table_[page_number - 1] = {frame_number, in_ram};
    }
    else if (levels_ == 2)
    {
        uint64_t level1_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level2_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx])
        {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        second_level_tables_[level1_idx]->at(level2_idx) = {frame_number, in_ram};
    }
    else if (levels_ == 3)
    {
        uint64_t level1_idx = ((page_number - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level3_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx])
        {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        size_t l3_idx = level1_idx * entries_per_table_ + level2_idx;
        if (!third_level_tables_[l3_idx])
        {
            third_level_tables_[l3_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            second_level_tables_[level1_idx]->at(level2_idx) = {l3_idx, true};
        }
        third_level_tables_[l3_idx]->at(level3_idx) = {frame_number, in_ram};
    }
    else
    {
        uint64_t level1_idx = ((page_number - 1) >> (3 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level2_idx = ((page_number - 1) >> (2 * bits_per_level_)) & (entries_per_table_ - 1);
        uint64_t level3_idx = ((page_number - 1) >> bits_per_level_) & (entries_per_table_ - 1);
        uint64_t level4_idx = (page_number - 1) & (entries_per_table_ - 1);
        if (!second_level_tables_[level1_idx])
        {
            second_level_tables_[level1_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
        }
        size_t l3_idx = level1_idx * entries_per_table_ + level2_idx;
        if (!third_level_tables_[l3_idx])
        {
            third_level_tables_[l3_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            second_level_tables_[level1_idx]->at(level2_idx) = {l3_idx, true};
        }
        size_t l4_idx = (level1_idx * entries_per_table_ * entries_per_table_ +
                         level2_idx * entries_per_table_ + level3_idx);
        if (!fourth_level_tables_[l4_idx])
        {
            fourth_level_tables_[l4_idx] = new std::vector<std::pair<uint64_t, bool>>(entries_per_table_, {0, false});
            third_level_tables_[l3_idx]->at(level3_idx) = {l4_idx, true};
        }
        fourth_level_tables_[l4_idx]->at(level4_idx) = {frame_number, in_ram};
    }
}

void PageTable::log_page_table_creation()
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Initialized ";
    if (levels_ == 1)
    {
        debug << "single-level table with " << num_pages_ << " entries\n";
    }
    else
    {
        debug << "multi-level table with " << entries_per_table_ << " entries\n";
    }
    debug << "Process " << process_id_ << ": Created page table with " << levels_ << " levels, "
          << num_pages_ << " pages, " << entries_per_table_ << " entries per table\n";
    if (levels_ == 1)
    {
        debug << "Process " << process_id_ << ": Single-level table with "
              << single_level_table_.size() << " entries\n";
    }
    else
    {
        debug << "Process " << process_id_ << ": Top-level table with "
              << top_level_table_.size() << " entries\n";
        int second_level_count = 0;
        for (const auto *table : second_level_tables_)
        {
            if (table)
                second_level_count++;
        }
        debug << "Process " << process_id_ << ": " << second_level_count
              << " second-level tables\n";
        if (levels_ >= 3)
        {
            int third_level_count = 0;
            for (const auto *table : third_level_tables_)
            {
                if (table)
                    third_level_count++;
            }
            debug << "Process " << process_id_ << ": " << third_level_count
                  << " third-level tables\n";
        }
        if (levels_ == 4)
        {
            int fourth_level_count = 0;
            for (const auto *table : fourth_level_tables_)
            {
                if (table)
                    fourth_level_count++;
            }
            debug << "Process " << process_id_ << ": " << fourth_level_count
                  << " fourth-level tables\n";
        }
    }
    debug.close();
}

const std::string &PageTable::get_process_id() const
{
    return process_id_;
}

int PageTable::get_levels() const
{
    return levels_;
}

uint64_t PageTable::get_top_level_frame() const
{
    return top_level_frame_;
}

bool PageTable::handle_page_fault(uint64_t page_number, std::vector<uint64_t> &available_frames,
                                  std::vector<uint64_t> &available_swap_frames)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Handling page fault for page " << page_number << "\n";

    uint64_t frame;
    bool in_ram = true;
    std::mt19937 gen{std::random_device{}()};
    if (!available_frames.empty())
    {
        frame = get_unique_frame(available_frames, gen);
        if (frame == UINT64_MAX)
        {
            debug << "Process " << process_id_ << ": Failed to allocate RAM frame for page " << page_number << "\n";
            debug.close();
            return false;
        }
        ram_[frame] = {"page_" + std::to_string(page_number) + "_" + process_id_, true};
    }
    else if (!available_swap_frames.empty())
    {
        frame = get_unique_swap_frame(available_swap_frames, gen);
        if (frame == UINT64_MAX)
        {
            debug << "Process " << process_id_ << ": Failed to allocate swap frame for page " << page_number << "\n";
            debug.close();
            return false;
        }
        in_ram = false;
        std::stringstream ss;
        ss << "1x" << std::hex << frame;
        swap_map_[ss.str()] = "PID" + process_id_ + "_page" + std::to_string(page_number);
        ram_[frame] = {"swap_page_" + std::to_string(page_number) + "_" + process_id_, true};
    }
    else
    {
        debug << "Process " << process_id_ << ": No available frames for page " << page_number << "\n";
        debug.close();
        return false;
    }

    entries_[page_number] = frame;
    set_page_entry(page_number, frame, in_ram);
    debug << "Process " << process_id_ << ": Successfully allocated "
          << (in_ram ? "RAM" : "swap") << " frame 0x" << std::noshowbase << std::hex << frame
          << " for page " << std::dec << page_number << "\n";
    debug.close();
    return true;
}

bool PageTable::allocate_frame(uint64_t page_number, std::vector<uint64_t> &available_frames,
                               std::vector<uint64_t> &available_swap_frames)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << process_id_ << ": Allocating frame for page " << page_number << "\n";

    auto it = entries_.find(page_number);
    if (it != entries_.end())
    {
        uint64_t frame = it->second;
        debug << "Process " << process_id_ << ": Page " << page_number
              << " already has frame 0x" << std::hex << frame << "\n";
        debug.close();
        return true;
    }

    return handle_page_fault(page_number, available_frames, available_swap_frames);
}