#include "memory_allocation.h"
#include "page_table.h"
#include <algorithm>
#include <fstream>
#include <sstream>

uint64_t NextFitStrategy::last_search_frame_ = 0;

NextFitStrategy::NextFitStrategy() {}

QuickFitStrategy::QuickFitStrategy() : predefined_sizes_({1, 4, 16}) {}

void QuickFitStrategy::initialize_size_lists(std::vector<uint64_t>& available_frames) {
    size_lists_.clear();
    std::sort(available_frames.begin(), available_frames.end());
    std::vector<uint64_t> current_block;
    for (uint64_t frame : available_frames) {
        if (current_block.empty() || frame == current_block.back() + 1) {
            current_block.push_back(frame);
        } else {
            for (uint64_t size : predefined_sizes_) {
                if (current_block.size() >= size) {
                    size_lists_[size].push_back(current_block);
                }
            }
            current_block.clear();
            current_block.push_back(frame);
        }
    }
    if (!current_block.empty()) {
        for (uint64_t size : predefined_sizes_) {
            if (current_block.size() >= size) {
                size_lists_[size].push_back(current_block);
            }
        }
    }
}

bool FirstFitStrategy::allocate(PageTable& page_table, uint64_t num_pages,
                               std::vector<uint64_t>& available_frames,
                               std::vector<uint64_t>& available_swap_frames,
                               std::mt19937& gen,
                               std::vector<uint64_t>& allocated_frames,
                               std::vector<uint64_t>& allocated_swap_frames) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << page_table.get_process_id() << ": First Fit allocating " << num_pages << " pages\n";

    std::sort(available_frames.begin(), available_frames.end());
    uint64_t ram_pages = std::min(num_pages, static_cast<uint64_t>(available_frames.size()));
    uint64_t swap_pages = num_pages - ram_pages;

    // Allocate RAM pages
    for (size_t i = 0; i < available_frames.size() && allocated_frames.size() < ram_pages; ) {
        uint64_t start = available_frames[i];
        size_t j = i;
        while (j < available_frames.size() && available_frames[j] == start + (j - i)) {
            ++j;
        }
        uint64_t block_size = j - i;
        if (block_size >= ram_pages - allocated_frames.size()) {
            for (uint64_t k = 0; k < ram_pages - allocated_frames.size(); ++k) {
                allocated_frames.push_back(start + k);
            }
            available_frames.erase(available_frames.begin() + i, available_frames.begin() + i + (ram_pages - allocated_frames.size()));
            break;
        }
        i = j;
    }

    if (allocated_frames.size() < ram_pages) {
        debug << "Process " << page_table.get_process_id() << ": Insufficient contiguous RAM for " << ram_pages << " pages\n";
        debug.close();
        return false;
    }

    // Allocate swap pages
    if (swap_pages > 0) {
        std::sort(available_swap_frames.begin(), available_swap_frames.end());
        if (available_swap_frames.size() < swap_pages) {
            debug << "Process " << page_table.get_process_id() << ": Insufficient swap frames for " << swap_pages << " pages\n";
            debug.close();
            return false;
        }
        for (uint64_t i = 0; i < swap_pages; ++i) {
            allocated_swap_frames.push_back(available_swap_frames[i]);
        }
        available_swap_frames.erase(available_swap_frames.begin(), available_swap_frames.begin() + swap_pages);
    }

    debug << "Process " << page_table.get_process_id() << ": Allocated " << allocated_frames.size() << " RAM frames, "
          << allocated_swap_frames.size() << " swap frames\n";
    debug.close();
    return true;
}

bool NextFitStrategy::allocate(PageTable& page_table, uint64_t num_pages,
                              std::vector<uint64_t>& available_frames,
                              std::vector<uint64_t>& available_swap_frames,
                              std::mt19937& gen,
                              std::vector<uint64_t>& allocated_frames,
                              std::vector<uint64_t>& allocated_swap_frames) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << page_table.get_process_id() << ": Next Fit allocating " << num_pages << " pages, starting from frame 0x" << std::hex << last_search_frame_ << std::dec << "\n";

    std::sort(available_frames.begin(), available_frames.end());
    uint64_t ram_pages = std::min(num_pages, static_cast<uint64_t>(available_frames.size()));
    uint64_t swap_pages = num_pages - ram_pages;

    // Find starting index for last_search_frame_
    size_t start_idx = 0;
    for (size_t i = 0; i < available_frames.size(); ++i) {
        if (available_frames[i] >= last_search_frame_) {
            start_idx = i;
            break;
        }
    }

    // Allocate RAM pages
    bool allocated = false;
    for (size_t i = start_idx; i < available_frames.size() && !allocated; ) {
        uint64_t start = available_frames[i];
        size_t j = i;
        while (j < available_frames.size() && available_frames[j] == start + (j - i)) {
            ++j;
        }
        uint64_t block_size = j - i;
        if (block_size >= ram_pages) {
            for (uint64_t k = 0; k < ram_pages; ++k) {
                allocated_frames.push_back(start + k);
            }
            available_frames.erase(available_frames.begin() + i, available_frames.begin() + i + ram_pages);
            last_search_frame_ = start + ram_pages;
            allocated = true;
        }
        i = j;
    }

    // Wrap around if not allocated
    if (!allocated) {
        for (size_t i = 0; i < start_idx && !allocated; ) {
            uint64_t start = available_frames[i];
            size_t j = i;
            while (j < available_frames.size() && available_frames[j] == start + (j - i)) {
                ++j;
            }
            uint64_t block_size = j - i;
            if (block_size >= ram_pages) {
                for (uint64_t k = 0; k < ram_pages; ++k) {
                    allocated_frames.push_back(start + k);
                }
                available_frames.erase(available_frames.begin() + i, available_frames.begin() + i + ram_pages);
                last_search_frame_ = start + ram_pages;
                allocated = true;
            }
            i = j;
        }
    }

    if (!allocated) {
        debug << "Process " << page_table.get_process_id() << ": Insufficient contiguous RAM for " << ram_pages << " pages\n";
        debug.close();
        return false;
    }

    // Allocate swap pages
    if (swap_pages > 0) {
        std::sort(available_swap_frames.begin(), available_swap_frames.end());
        if (available_swap_frames.size() < swap_pages) {
            debug << "Process " << page_table.get_process_id() << ": Insufficient swap frames for " << swap_pages << " pages\n";
            debug.close();
            return false;
        }
        for (uint64_t i = 0; i < swap_pages; ++i) {
            allocated_swap_frames.push_back(available_swap_frames[i]);
        }
        available_swap_frames.erase(available_swap_frames.begin(), available_swap_frames.begin() + swap_pages);
    }

    debug << "Process " << page_table.get_process_id() << ": Allocated " << allocated_frames.size() << " RAM frames, "
          << allocated_swap_frames.size() << " swap frames, new last_search_frame_=0x" << std::hex << last_search_frame_ << std::dec << "\n";
    debug.close();
    return true;
}

bool BestFitStrategy::allocate(PageTable& page_table, uint64_t num_pages,
                              std::vector<uint64_t>& available_frames,
                              std::vector<uint64_t>& available_swap_frames,
                              std::mt19937& gen,
                              std::vector<uint64_t>& allocated_frames,
                              std::vector<uint64_t>& allocated_swap_frames) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << page_table.get_process_id() << ": Best Fit allocating " << num_pages << " pages\n";

    std::sort(available_frames.begin(), available_frames.end());
    uint64_t ram_pages = std::min(num_pages, static_cast<uint64_t>(available_frames.size()));
    uint64_t swap_pages = num_pages - ram_pages;

    // Find smallest block that fits
    uint64_t best_size = UINT64_MAX;
    size_t best_start_idx = 0;
    bool found = false;

    for (size_t i = 0; i < available_frames.size(); ) {
        uint64_t start = available_frames[i];
        size_t j = i;
        while (j < available_frames.size() && available_frames[j] == start + (j - i)) {
            ++j;
        }
        uint64_t block_size = j - i;
        if (block_size >= ram_pages && block_size < best_size) {
            best_size = block_size;
            best_start_idx = i;
            found = true;
        }
        i = j;
    }

    if (!found) {
        debug << "Process " << page_table.get_process_id() << ": Insufficient contiguous RAM for " << ram_pages << " pages\n";
        debug.close();
        return false;
    }

    // Allocate RAM pages
    for (uint64_t k = 0; k < ram_pages; ++k) {
        allocated_frames.push_back(available_frames[best_start_idx + k]);
    }
    available_frames.erase(available_frames.begin() + best_start_idx, available_frames.begin() + best_start_idx + ram_pages);

    // Allocate swap pages
    if (swap_pages > 0) {
        std::sort(available_swap_frames.begin(), available_swap_frames.end());
        if (available_swap_frames.size() < swap_pages) {
            debug << "Process " << page_table.get_process_id() << ": Insufficient swap frames for " << swap_pages << " pages\n";
            debug.close();
            return false;
        }
        for (uint64_t i = 0; i < swap_pages; ++i) {
            allocated_swap_frames.push_back(available_swap_frames[i]);
        }
        available_swap_frames.erase(available_swap_frames.begin(), available_swap_frames.begin() + swap_pages);
    }

    debug << "Process " << page_table.get_process_id() << ": Allocated " << allocated_frames.size() << " RAM frames, "
          << allocated_swap_frames.size() << " swap frames\n";
    debug.close();
    return true;
}

bool WorstFitStrategy::allocate(PageTable& page_table, uint64_t num_pages,
                               std::vector<uint64_t>& available_frames,
                               std::vector<uint64_t>& available_swap_frames,
                               std::mt19937& gen,
                               std::vector<uint64_t>& allocated_frames,
                               std::vector<uint64_t>& allocated_swap_frames) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << page_table.get_process_id() << ": Worst Fit allocating " << num_pages << " pages\n";

    std::sort(available_frames.begin(), available_frames.end());
    uint64_t ram_pages = std::min(num_pages, static_cast<uint64_t>(available_frames.size()));
    uint64_t swap_pages = num_pages - ram_pages;

    // Find largest block
    uint64_t worst_size = 0;
    size_t worst_start_idx = 0;
    bool found = false;

    for (size_t i = 0; i < available_frames.size(); ) {
        uint64_t start = available_frames[i];
        size_t j = i;
        while (j < available_frames.size() && available_frames[j] == start + (j - i)) {
            ++j;
        }
        uint64_t block_size = j - i;
        if (block_size >= ram_pages && block_size > worst_size) {
            worst_size = block_size;
            worst_start_idx = i;
            found = true;
        }
        i = j;
    }

    if (!found) {
        debug << "Process " << page_table.get_process_id() << ": Insufficient contiguous RAM for " << ram_pages << " pages\n";
        debug.close();
        return false;
    }

    // Allocate RAM pages
    for (uint64_t k = 0; k < ram_pages; ++k) {
        allocated_frames.push_back(available_frames[worst_start_idx + k]);
    }
    available_frames.erase(available_frames.begin() + worst_start_idx, available_frames.begin() + worst_start_idx + ram_pages);

    // Allocate swap pages
    if (swap_pages > 0) {
        std::sort(available_swap_frames.begin(), available_swap_frames.end());
        if (available_swap_frames.size() < swap_pages) {
            debug << "Process " << page_table.get_process_id() << ": Insufficient swap frames for " << swap_pages << " pages\n";
            debug.close();
            return false;
        }
        for (uint64_t i = 0; i < swap_pages; ++i) {
            allocated_swap_frames.push_back(available_swap_frames[i]);
        }
        available_swap_frames.erase(available_swap_frames.begin(), available_swap_frames.begin() + swap_pages);
    }

    debug << "Process " << page_table.get_process_id() << ": Allocated " << allocated_frames.size() << " RAM frames, "
          << allocated_swap_frames.size() << " swap frames\n";
    debug.close();
    return true;
}

bool QuickFitStrategy::allocate(PageTable& page_table, uint64_t num_pages,
                               std::vector<uint64_t>& available_frames,
                               std::vector<uint64_t>& available_swap_frames,
                               std::mt19937& gen,
                               std::vector<uint64_t>& allocated_frames,
                               std::vector<uint64_t>& allocated_swap_frames) {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Process " << page_table.get_process_id() << ": Quick Fit allocating " << num_pages << " pages\n";

    initialize_size_lists(available_frames);
    uint64_t ram_pages = std::min(num_pages, static_cast<uint64_t>(available_frames.size()));
    uint64_t swap_pages = num_pages - ram_pages;

    // Find smallest predefined size that fits
    uint64_t target_size = 0;
    for (uint64_t size : predefined_sizes_) {
        if (size >= ram_pages) {
            target_size = size;
            break;
        }
    }
    if (target_size == 0) {
        debug << "Process " << page_table.get_process_id() << ": No predefined size fits " << ram_pages << " pages\n";
        debug.close();
        return false;
    }

    // Allocate from size list
    if (size_lists_[target_size].empty()) {
        debug << "Process " << page_table.get_process_id() << ": No available block of size " << target_size << "\n";
        debug.close();
        return false;
    }

    std::vector<uint64_t>& block = size_lists_[target_size][0];
    for (uint64_t k = 0; k < ram_pages; ++k) {
        allocated_frames.push_back(block[k]);
        auto it = std::find(available_frames.begin(), available_frames.end(), block[k]);
        if (it != available_frames.end()) {
            available_frames.erase(it);
        }
    }
    size_lists_[target_size].erase(size_lists_[target_size].begin());

    // Allocate swap pages
    if (swap_pages > 0) {
        std::sort(available_swap_frames.begin(), available_swap_frames.end());
        if (available_swap_frames.size() < swap_pages) {
            debug << "Process " << page_table.get_process_id() << ": Insufficient swap frames for " << swap_pages << " pages\n";
            debug.close();
            return false;
        }
        for (uint64_t i = 0; i < swap_pages; ++i) {
            allocated_swap_frames.push_back(available_swap_frames[i]);
        }
        available_swap_frames.erase(available_swap_frames.begin(), available_swap_frames.begin() + swap_pages);
    }

    debug << "Process " << page_table.get_process_id() << ": Allocated " << allocated_frames.size() << " RAM frames, "
          << allocated_swap_frames.size() << " swap frames using size " << target_size << "\n";
    debug.close();
    return true;
}
