#include <iostream>
#include <vector>
#include <set>
#include <random>
#include <string>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <iomanip>
#include <direct.h>
#include "../include/virtual_memory_simulator.h"

VirtualMemorySimulator::VirtualMemorySimulator(const std::string &bin_path)
    : bin_directory(bin_path), total_hits(0), total_misses(0), total_faults(0), tlb_capacity(0)
{
    std::ofstream debug("debug.txt", std::ios::out);
    debug << "Virtual Memory Simulator initialized with bin directory: " << bin_directory << "\n";
    debug.close();

    _mkdir(bin_directory.c_str());
}

VirtualMemorySimulator::~VirtualMemorySimulator()
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Virtual Memory Simulator destroyed\n";
    debug.close();
}

bool VirtualMemorySimulator::load_settings()
{
    try
    {
        std::ifstream env_file(bin_directory + "/environment.json");
        std::ifstream proc_file(bin_directory + "/processes.json");

        if (!env_file.is_open() || !proc_file.is_open())
        {
            std::cerr << "Failed to open JSON files in " << bin_directory << std::endl;
            return false;
        }

        json env_settings;
        json proc_settings;
        env_file >> env_settings;
        proc_file >> proc_settings;

        // Load environment settings
        ram_size_bytes = env_settings["ram_size_gb"].get<int64_t>() * 1024ULL * 1024 * 1024;
        page_size_bytes = env_settings["page_size_kb"].get<int64_t>() * 1024;
        tlb_size = env_settings["tlb_size"].get<int>();
        tlb_enabled = env_settings["tlb_enabled"].get<bool>();
        virtual_address_size = env_settings["virtual_address_size"].get<std::string>();
        rom_size = env_settings["rom_size"].get<std::string>();
        swap_percent = static_cast<int>(env_settings["swap_percent"].get<double>());
        allocation_type = env_settings["allocation_type"].get<std::string>();

        int entry_size = (virtual_address_size == "16-bit") ? 2 : (virtual_address_size == "32-bit") ? 4
                                                                                                     : 8;
        tlb_capacity = (tlb_size * 1024) / entry_size;

        // Load process settings
        processes.clear();
        if (!proc_settings.empty() && proc_settings.is_array())
        {
            for (const auto &proc : proc_settings)
            {
                Process process;
                process.id = proc["id"].get<std::string>();
                process.name = proc["name"].get<std::string>();
                process.size_gb = proc["size_gb"].get<int>();
                process.type = proc["type"].get<std::string>();
                process.has_priority = proc["has_priority"].get<bool>();
                process.is_process_stop = proc["is_process_stop"].get<bool>();

                // Parse virtual address from hex string if it's a string
                if (proc["virtual_address"].is_string())
                {
                    std::string va_str = proc["virtual_address"].get<std::string>();
                    if (va_str.substr(0, 2) == "0x")
                    {
                        process.virtual_address = std::stoull(va_str.substr(2), nullptr, 16);
                    }
                    else
                    {
                        process.virtual_address = std::stoull(va_str);
                    }
                }
                else
                {
                    process.virtual_address = proc["virtual_address"].get<uint64_t>();
                }

                processes.push_back(process);
            }
        }

        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Settings loaded successfully\n";
        debug.close();
        return true;
    }
    catch (const std::exception &e)
    {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Error loading settings: " << e.what() << "\n";
        debug.close();
        std::cerr << "Error loading settings: " << e.what() << std::endl;
        return false;
    }
}

bool VirtualMemorySimulator::save_results(const json &results)
{
    try
    {
        std::ofstream results_file(bin_directory + "/simulation_results.json");
        if (!results_file.is_open())
        {
            std::cerr << "Failed to open results file for writing" << std::endl;
            return false;
        }
        results_file << std::setw(4) << results << std::endl;
        return true;
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error saving results: " << e.what() << std::endl;
        return false;
    }
}

json VirtualMemorySimulator::export_results()
{
    json result;
    result["tlb_stats"]["hits"] = tlb_hits;
    result["tlb_stats"]["misses"] = tlb_misses;
    result["tlb_stats"]["hit_rate"] = tlb_hit_rate;
    result["tlb_stats"]["total_hits"] = total_hits;
    result["tlb_stats"]["total_misses"] = total_misses;
    result["page_faults"] = page_faults;
    result["total_faults"] = total_faults;

    json pts;
    for (const auto &pt : page_tables)
    {
        if (pt.second.flag == -1)
            continue;
        json pt_entry;
        pt_entry["process_id"] = pt.first;
        pt_entry["base_address"] = pt.second.top_level_frame;
        pt_entry["table"] = pt.second.page_table.export_json();
        pt_entry["flag"] = pt.second.flag;
        pt_entry["last_executed_page"] = pt.second.last_executed_page;
        pts.push_back(pt_entry);
    }
    result["page_tables"] = pts;

    return result;
}

void VirtualMemorySimulator::simulate()
{
    std::ofstream debug_file("debug.txt", std::ios::app);
    debug_file << "\n=== Starting New Simulation ===\n\n";

    // Clear previous state
    tlb_hits.clear();
    tlb_misses.clear();
    tlb_hit_rate.clear();
    page_faults.clear();
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;
    tlb.clear();
    while (!tlb_fifo.empty())
        tlb_fifo.pop();

    // Print initial settings
    debug_file << std::fixed << std::setprecision(2);
    debug_file << "Settings: RAM=" << ram_size_bytes / (1024ULL * 1024 * 1024) << "GB, "
               << "PageSize=" << page_size_bytes / 1024 << "KB, "
               << "TLBSize=" << tlb_size << "KB, "
               << "TLBEnabled=" << tlb_enabled << ", "
               << "VASize=" << virtual_address_size << ", "
               << "ROM=" << rom_size << ", "
               << "Swap=" << swap_percent << "%, "
               << "Allocation=" << allocation_type << "\n\n";

    // Print process information
    debug_file << "Active Processes:\n";
    for (const auto &p : processes)
    {
        debug_file << "Process: ID=" << p.id << ", Name=" << p.name << ", Size="
                   << p.size_gb << "GB, Type=" << p.type << ", Priority=" << p.has_priority
                   << ", Stopped=" << p.is_process_stop << "\n";
    }
    debug_file << "\n";

    // Initialize RNG
    std::random_device rd;
    std::mt19937 gen(rd());

    // Calculate memory sizes
    uint64_t rom_size_bytes;
    std::stringstream ss(rom_size);
    double rom_gb;
    ss >> rom_gb;
    rom_size_bytes = static_cast<uint64_t>(rom_gb * 1024ULL * 1024 * 1024);

    uint64_t total_process_size = 0;
    int active_processes = 0;
    for (const auto &p : processes)
    {
        if (!p.is_process_stop)
        {
            total_process_size += static_cast<uint64_t>(p.size_gb) * 1024ULL * 1024 * 1024;
            active_processes++;
        }
    }

    // Calculate available memory and frames
    uint64_t swap_size_bytes = swap_percent > 0 ? (rom_size_bytes * swap_percent / 100) : 0;
    uint64_t total_swap_frames = swap_size_bytes / page_size_bytes;
    uint64_t total_frames = ram_size_bytes / page_size_bytes;
    uint64_t table_frame_limit = static_cast<uint64_t>(ceil(total_frames * 0.01));

    debug_file << "Memory Configuration:\n"
               << "  Total RAM Frames: " << total_frames << "\n"
               << "  Table Frame Limit: " << table_frame_limit << "\n"
               << "  Swap Frames: " << total_swap_frames << "\n\n";

    // Initialize frame pools if empty
    if (available_frames.empty())
    {
        for (uint64_t i = table_frame_limit; i < total_frames; ++i)
        {
            available_frames.push_back(i);
        }
    }

    if (available_table_frames.empty())
    {
        for (uint64_t i = 0; i < table_frame_limit; ++i)
        {
            available_table_frames.push_back(i);
        }
    }

    if (available_swap_frames.empty() && total_swap_frames > 0)
    {
        for (uint64_t i = 0; i < total_swap_frames; ++i)
        {
            available_swap_frames.push_back(i);
        }
    }

    // Initialize page tables for each active process
    page_tables.clear(); // Clear any existing page tables
    debug_file << "Initializing page tables for processes...\n";

    int entry_size = (virtual_address_size == "16-bit") ? 2 : (virtual_address_size == "32-bit") ? 4
                                                                                                 : 8;
    double frame_percent = active_processes > 1 ? (100.0 / active_processes) : 100.0;

    for (const auto &p : processes)
    {
        if (p.is_process_stop)
            continue;

        debug_file << "\nInitializing page table for Process " << p.id << "...\n";

        uint64_t process_size_bytes = static_cast<uint64_t>(p.size_gb) * 1024ULL * 1024 * 1024;
        uint64_t num_pages = (process_size_bytes + page_size_bytes - 1) / page_size_bytes;

        PageTable pt(num_pages, page_size_bytes, entry_size, allocation_type,
                     total_frames, total_frames, ram_size_bytes, frame_percent,
                     p.id, virtual_address_size);

        if (!pt.allocate(page_size_bytes, available_frames, available_table_frames, gen, available_swap_frames))
        {
            debug_file << "Failed to allocate page table for Process " << p.id << "\n";
            continue;
        }

        debug_file << "Successfully created page table for Process " << p.id << "\n";
        debug_file << "  Number of pages: " << num_pages << "\n";
        debug_file << "  Top level frame: 0x" << std::hex << pt.get_top_level_frame() << std::dec << "\n";

        page_tables.emplace(p.id, PageTableEntry(pt.get_top_level_frame(), std::move(pt), 1, -1));
        tlb_hits.push_back({std::stoi(p.id), 0});
        tlb_misses.push_back({std::stoi(p.id), 0});
        tlb_hit_rate.push_back({std::stoi(p.id), 0.0});
        page_faults.push_back({std::stoi(p.id), 0});
    }

    debug_file << "\nStarting simulation loop...\n";
    debug_file.flush();
    std::cout << "Starting simulation loop...\n";

    std::uniform_int_distribution<> access_dist(0, 1);
    std::uniform_int_distribution<uint64_t> va_dist(0, UINT64_MAX);

    int simulation_duration = 100;
    for (int t = 0; t < simulation_duration; ++t)
    {
        if (t % 10 == 0)
        {
            std::cout << "Simulation progress: " << (t * 100 / simulation_duration) << "%\n";
            debug_file << "\n=== Time step " << t << " ===\n";
            debug_file.flush();
        }

        // Iterate through active processes
        for (const auto &p : processes)
        {
            if (p.is_process_stop)
                continue;

            auto it = page_tables.find(p.id);
            if (it == page_tables.end() || it->second.flag != 1)
            {
                debug_file << "Process " << p.id << ": Page table not found or invalid\n";
                continue;
            }

            // Generate memory access
            uint64_t va = va_dist(gen);
            uint64_t page_number = va / page_size_bytes;
            bool is_write = access_dist(gen) == 1;

            debug_file << "\nProcess " << p.id << ": Accessing VA=0x" << std::hex << va
                       << " (Page " << std::dec << page_number << ") "
                       << "(" << (is_write ? "Write" : "Read") << ")\n";

            // Try TLB lookup first if enabled
            bool tlb_hit = false;
            uint64_t frame = UINT64_MAX;

            if (tlb_enabled)
            {
                frame = tlb_get_frame(p.id, page_number);
                tlb_hit = (frame != UINT64_MAX);

                debug_file << "TLB " << (tlb_hit ? "HIT" : "MISS") << "\n";
                if (tlb_hit)
                {
                    debug_file << "TLB hit - Frame: 0x" << std::hex << frame << std::dec << "\n";
                }
            }

            // If TLB miss or TLB disabled, do page table lookup
            if (!tlb_hit)
            {
                try
                {
                    frame = it->second.page_table.lookup(page_number);
                    debug_file << "Page table lookup - "
                               << "Page: " << std::dec << page_number << ", "
                               << "Frame: " << (frame == UINT64_MAX ? "FAULT" : ("0x" + std::to_string(frame))) << "\n";

                    if (frame == UINT64_MAX)
                    {
                        debug_file << "Page fault occurred - handling...\n";

                        // Update page fault statistics
                        auto pf_it = std::find_if(page_faults.begin(), page_faults.end(),
                                                  [&p](const auto &pair)
                                                  { return pair.first == std::stoi(p.id); });
                        if (pf_it != page_faults.end())
                        {
                            pf_it->second++;
                            total_faults++;
                        }

                        // Try to allocate a new frame
                        if (!it->second.page_table.allocate(page_size_bytes, available_frames,
                                                            available_table_frames, gen, available_swap_frames))
                        {
                            debug_file << "Error: Failed to handle page fault\n";
                            continue;
                        }

                        frame = it->second.page_table.lookup(page_number);
                        if (frame == UINT64_MAX)
                        {
                            debug_file << "Error: Page fault handling failed - still no valid frame\n";
                            continue;
                        }
                        debug_file << "Page fault handled successfully - New frame: 0x"
                                   << std::hex << frame << std::dec << "\n";
                    }

                    // Update TLB
                    if (tlb_enabled && frame != UINT64_MAX)
                    {
                        tlb_insert(p.id, page_number, va, frame, 1);
                        debug_file << "TLB updated with new mapping\n";
                    }
                }
                catch (const std::exception &e)
                {
                    debug_file << "Error during page table lookup: " << e.what() << "\n";
                    continue;
                }
            }

            // Update statistics
            if (tlb_enabled)
            {
                auto stats_update = [this](auto &vec, const std::string &pid, int value)
                {
                    auto it = std::find_if(vec.begin(), vec.end(),
                                           [&pid](const auto &pair)
                                           { return pair.first == std::stoi(pid); });
                    if (it != vec.end())
                        it->second += value;
                };

                if (tlb_hit)
                {
                    stats_update(tlb_hits, p.id, 1);
                    total_hits++;
                }
                else
                {
                    stats_update(tlb_misses, p.id, 1);
                    total_misses++;
                }

                // Update hit rate
                auto hits_it = std::find_if(tlb_hits.begin(), tlb_hits.end(),
                                            [&p](const auto &pair)
                                            { return pair.first == std::stoi(p.id); });
                auto misses_it = std::find_if(tlb_misses.begin(), tlb_misses.end(),
                                              [&p](const auto &pair)
                                              { return pair.first == std::stoi(p.id); });
                auto rate_it = std::find_if(tlb_hit_rate.begin(), tlb_hit_rate.end(),
                                            [&p](const auto &pair)
                                            { return pair.first == std::stoi(p.id); });

                if (hits_it != tlb_hits.end() && misses_it != tlb_misses.end() && rate_it != tlb_hit_rate.end())
                {
                    int total = hits_it->second + misses_it->second;
                    rate_it->second = total > 0 ? (double)hits_it->second / total : 0.0;
                }
            }

            debug_file << "Memory access completed successfully\n";
            debug_file.flush();
        }

        // Print periodic statistics
        if (t % 10 == 0)
        {
            debug_file << "\nStatistics at time " << t << ":\n";
            for (const auto &p : processes)
            {
                if (p.is_process_stop)
                    continue;

                debug_file << "Process " << p.id << ":\n";

                auto pf_it = std::find_if(page_faults.begin(), page_faults.end(),
                                          [&p](const auto &pair)
                                          { return pair.first == std::stoi(p.id); });
                if (pf_it != page_faults.end())
                {
                    debug_file << "  Page Faults: " << pf_it->second << "\n";
                }

                if (tlb_enabled)
                {
                    auto hits_it = std::find_if(tlb_hits.begin(), tlb_hits.end(),
                                                [&p](const auto &pair)
                                                { return pair.first == std::stoi(p.id); });
                    auto misses_it = std::find_if(tlb_misses.begin(), tlb_misses.end(),
                                                  [&p](const auto &pair)
                                                  { return pair.first == std::stoi(p.id); });
                    auto rate_it = std::find_if(tlb_hit_rate.begin(), tlb_hit_rate.end(),
                                                [&p](const auto &pair)
                                                { return pair.first == std::stoi(p.id); });

                    if (hits_it != tlb_hits.end() && misses_it != tlb_misses.end() && rate_it != tlb_hit_rate.end())
                    {
                        debug_file << "  TLB Hits: " << hits_it->second
                                   << ", Misses: " << misses_it->second
                                   << ", Hit Rate: " << std::fixed << std::setprecision(2)
                                   << (rate_it->second * 100) << "%\n";
                    }
                }
            }

            debug_file << "\nTotal Statistics:\n"
                       << "  Page Faults: " << total_faults << "\n";
            if (tlb_enabled)
            {
                debug_file << "  TLB Hits: " << total_hits
                           << ", Misses: " << total_misses
                           << ", Overall Hit Rate: " << std::fixed << std::setprecision(2)
                           << (total_hits + total_misses > 0 ? (total_hits * 100.0 / (total_hits + total_misses)) : 0)
                           << "%\n";
            }
            debug_file << std::string(80, '-') << "\n";
            debug_file.flush();
        }
    }

    debug_file << "\n=== Simulation Complete ===\n";
    debug_file.close();
}

void VirtualMemorySimulator::lookup(const std::string &process_id, uint64_t page_number)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "\n=== Page Table Lookup ===\n";
    debug << "Process: " << process_id << ", Page Number: " << page_number << "\n";

    auto it = page_tables.find(process_id);
    if (it != page_tables.end() && it->second.flag == 1)
    {
        it->second.last_executed_page = static_cast<int64_t>(page_number);
        uint64_t frame = it->second.page_table.lookup(page_number);

        if (frame != UINT64_MAX)
        {
            debug << "Result: Success\n"
                  << "  Virtual Address: 0x" << std::hex << (page_number * page_size_bytes) << "\n"
                  << "  Physical Frame: 0x" << frame << "\n"
                  << "  Offset Range: 0x0 to 0x" << std::hex << (page_size_bytes - 1) << "\n"
                  << "  Physical Address Range: 0x" << (frame * page_size_bytes)
                  << " to 0x" << ((frame + 1) * page_size_bytes - 1) << std::dec << "\n";
        }
        else
        {
            debug << "Result: Page not found in page table\n";
        }
    }
    else
    {
        debug << "Result: Process not found or not active\n"
              << "  Status: " << (it != page_tables.end() ? "Found but inactive" : "Not found") << "\n";
    }
    debug << "=====================\n\n";
    debug.close();
}

void VirtualMemorySimulator::tlb_remove_process(const std::string &pid)
{
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "\n=== TLB Process Removal ===\n";
    debug << "Removing entries for Process ID: " << pid << "\n";

    size_t initial_size = tlb.size();
    std::vector<std::string> keys_to_remove;

    debug << "Initial TLB state:\n"
          << "  Total entries: " << initial_size << "\n"
          << "  Capacity: " << tlb_capacity << "\n\n";

    // Find all TLB entries for this process
    for (const auto &entry : tlb)
    {
        if (entry.second.pid == pid)
        {
            keys_to_remove.push_back(entry.first);
            debug << "Found entry to remove:\n"
                  << "  Key: " << entry.first << "\n"
                  << "  VA: 0x" << std::hex << entry.second.virtual_address << "\n"
                  << "  Frame: 0x" << entry.second.frame_no << std::dec << "\n";
        }
    }

    debug << "\nRemoving " << keys_to_remove.size() << " entries...\n";
    if (!keys_to_remove.empty())
    {
        // Create a new FIFO queue without the removed entries
        std::queue<std::string> new_fifo;
        auto remove_set = std::unordered_set<std::string>(keys_to_remove.begin(), keys_to_remove.end());

        // Copy valid entries to the new queue
        while (!tlb_fifo.empty())
        {
            std::string current = tlb_fifo.front();
            tlb_fifo.pop();
            if (remove_set.find(current) == remove_set.end())
            {
                new_fifo.push(current);
                debug << "Keeping entry in FIFO: " << current << "\n";
            }
            else
            {
                debug << "Removing entry from FIFO: " << current << "\n";
            }
        }

        // Remove entries from TLB
        for (const auto &key : keys_to_remove)
        {
            tlb.erase(key);
        }

        // Replace old queue with new one
        tlb_fifo = std::move(new_fifo);
    }

    debug << "\nFinal TLB state:\n"
          << "  Remaining entries: " << tlb.size() << "\n"
          << "  Entries removed: " << initial_size - tlb.size() << "\n"
          << "  FIFO queue size: " << tlb_fifo.size() << "\n"
          << "=====================\n\n";
    debug.close();
}

void VirtualMemorySimulator::tlb_insert(const std::string &pid, uint64_t page_no, uint64_t virtual_address, uint64_t frame_no, int process_status)
{
    std::string key = pid + "_" + std::to_string(page_no);
    if (tlb.size() >= tlb_capacity)
    {
        std::string old_key = tlb_fifo.front();
        tlb_fifo.pop();
        tlb.erase(old_key);
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "TLB: Evicted entry " << old_key << "\n";
        debug.close();
    }
    TLBEntry entry = {pid, page_no, virtual_address, frame_no, process_status};
    tlb[key] = entry;
    tlb_fifo.push(key);
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "TLB: Inserted " << key << " (VA=0x" << std::hex << virtual_address << ", Frame=0x" << frame_no << ", Status=" << process_status << ")\n";
    debug.close();
}

uint64_t VirtualMemorySimulator::tlb_get_frame(const std::string &pid, uint64_t page_no)
{
    std::string key = pid + "_" + std::to_string(page_no);
    auto it = tlb.find(key);
    if (it != tlb.end() && it->second.process_status == 1)
    {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "TLB: Hit for " << key << ", Frame=0x" << std::hex << it->second.frame_no << "\n";
        debug.close();
        return it->second.frame_no;
    }
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "TLB: Miss for " << key << "\n";
    debug.close();
    return UINT64_MAX;
}

int main()
{
    std::ofstream debug("debug.txt", std::ios::out);
    debug << "Starting Virtual Memory Simulator\n";
    debug.close();

    VirtualMemorySimulator simulator("bin");

    try
    {
        if (simulator.load_settings())
        {
            simulator.simulate();
            json results = simulator.export_results();
            if (simulator.save_results(results))
            {
                std::cout << "Simulation completed successfully\n";
            }
            else
            {
                std::cerr << "Failed to save simulation results\n";
            }
        }
        else
        {
            std::cerr << "Failed to load settings\n";
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error during simulation: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
