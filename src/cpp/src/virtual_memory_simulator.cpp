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
#include <algorithm>
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
            std::ofstream debug("debug.txt", std::ios::app);
            debug << "Required configuration files not found. Waiting for UI to create them..." << std::endl;
            debug.close();

            // Create empty default config files
            std::ofstream default_env(bin_directory + "/environment.json");
            if (default_env.is_open())
            {
                default_env << "{\"ram_size_gb\": 1, \"page_size_kb\": 4, \"tlb_size\": 16, \"tlb_enabled\": false, \"virtual_address_size\": \"16-bit\", \"rom_size\": \"32 GB\", \"swap_percent\": 0, \"allocation_type\": \"Contiguous\"}" << std::endl;
                default_env.close();
            }

            std::ofstream default_proc(bin_directory + "/processes.json");
            if (default_proc.is_open())
            {
                default_proc << "[]" << std::endl;
                default_proc.close();
            }

            // Re-open the files
            env_file.open(bin_directory + "/environment.json");
            proc_file.open(bin_directory + "/processes.json");

            if (!env_file.is_open() || !proc_file.is_open())
            {
                std::cerr << "Failed to create or open config files in " << bin_directory << std::endl;
                return false;
            }
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
        tlb_capacity = std::max(1, (tlb_size * 1024) / entry_size); // Ensure minimum capacity of 1

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
    // Static statistics
    result["tlb_stats"]["hits"] = tlb_hits;
    result["tlb_stats"]["misses"] = tlb_misses;
    result["tlb_stats"]["hit_rate"] = tlb_hit_rate;
    result["tlb_stats"]["total_hits"] = total_hits;
    result["tlb_stats"]["total_misses"] = total_misses;
    result["page_faults"] = page_faults;
    result["total_faults"] = total_faults;

    // Time-based metrics
    if (!tlb_hits_over_time.empty())
    {
        result["time_series"]["tlb_hits"] = tlb_hits_over_time;
    }
    if (!tlb_misses_over_time.empty())
    {
        result["time_series"]["tlb_misses"] = tlb_misses_over_time;
    }
    if (!tlb_hit_rate_over_time.empty())
    {
        result["time_series"]["tlb_hit_rate"] = tlb_hit_rate_over_time;
    }
    if (!page_faults_over_time.empty())
    {
        result["time_series"]["page_faults"] = page_faults_over_time;
    }
    if (!ram_frames_used_over_time.empty())
    {
        result["time_series"]["ram_usage"] = ram_frames_used_over_time;
    }

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
               << "Allocation=" << allocation_type << "\n\n"; // Print process information
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

        page_tables.emplace(p.id, PageTableEntry(pt.get_top_level_frame(), std::move(pt), 1, -1)); // Initialize statistics for each active process
        for (const auto &p : processes)
        {
            if (p.is_process_stop)
                continue;

            tlb_hits.push_back({std::stoi(p.id), 0});
            tlb_misses.push_back({std::stoi(p.id), 0});
            tlb_hit_rate.push_back({std::stoi(p.id), 0.0});
            page_faults.push_back({std::stoi(p.id), 0});
        }
    }
    debug_file << "\nStarting simulation loop...\n";

    // Print the initial page tables
    print_page_tables(debug_file);

    debug_file.flush();
    std::cout << "Starting simulation loop...\n";
    std::uniform_int_distribution<> access_dist(0, 1); // Create realistic page distributions for each process with locality
    std::vector<std::uniform_int_distribution<uint64_t>> page_distributions;
    std::vector<uint64_t> last_accessed_pages;                // Track last accessed page for each process to simulate locality
    std::vector<uint64_t> max_pages;                          // Store max page number for each process
    std::uniform_real_distribution<> locality_dist(0.0, 1.0); // For deciding whether to use locality

    for (const auto &p : processes)
    {
        if (p.is_process_stop)
        {
            page_distributions.emplace_back(0, 0); // Dummy distribution for stopped processes
            last_accessed_pages.push_back(0);
            max_pages.push_back(0);
            continue;
        }

        uint64_t process_size_bytes = static_cast<uint64_t>(p.size_gb) * 1024ULL * 1024 * 1024;
        uint64_t max_page = (process_size_bytes + page_size_bytes - 1) / page_size_bytes - 1;
        page_distributions.emplace_back(0, max_page);
        last_accessed_pages.push_back(0); // Initialize with first page
        max_pages.push_back(max_page);
    }
    int simulation_duration = 100;
    for (int t = 0; t < simulation_duration; ++t)
    {
        if (t % 10 == 0)
        {
            std::cout << "Simulation progress: " << (t * 100 / simulation_duration) << "%\n";
            debug_file << "\n=== Time step " << t << " ===\n";
            debug_file.flush();
        }

        // Record time series data at each time step
        track_time_series_data(t);

        // Iterate through active processes
        int process_index = 0;
        for (const auto &p : processes)
        {
            if (p.is_process_stop)
            {
                process_index++;
                continue;
            }

            auto it = page_tables.find(p.id);
            if (it == page_tables.end() || it->second.flag != 1)
            {
                debug_file << "Process " << p.id << ": Page table not found or invalid\n";
                process_index++;
                continue;
            } // Generate realistic memory access with temporal and spatial locality
            uint64_t page_number;

            // 70% chance to use temporal locality (same page or nearby)
            if (locality_dist(gen) < 0.7)
            {
                // Either use the exact same page (temporal locality) or a nearby page (spatial locality)
                int offset = std::uniform_int_distribution<>(-3, 3)(gen); // Small range for locality
                page_number = static_cast<int64_t>(last_accessed_pages[process_index]) + offset;

                // Ensure the page number is within valid range
                page_number = std::max(uint64_t(0), std::min(page_number, max_pages[process_index]));
            }
            else
            {
                // 30% chance to access a completely random page
                page_number = page_distributions[process_index](gen);
            }

            // Save this as the last accessed page for next time
            last_accessed_pages[process_index] = page_number;

            uint64_t va = page_number * page_size_bytes;
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

            process_index++;
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

    // Print final page tables before closing
    debug_file << "\nFinal page tables state:\n";
    print_page_tables(debug_file);

    debug_file.close();
}

void VirtualMemorySimulator::track_time_series_data(int time_step)
{
    // Make sure the vectors are set up to hold data for each time step
    if (time_step == 0)
    {
        // Initialize time series data containers for each process
        tlb_hits_over_time.clear();
        tlb_misses_over_time.clear();
        tlb_hit_rate_over_time.clear();
        page_faults_over_time.clear();
        ram_frames_used_over_time.clear();

        for (const auto &p : processes)
        {
            if (p.is_process_stop)
                continue;

            int pid = std::stoi(p.id);

            // Initialize vectors for each process
            tlb_hits_over_time.push_back(std::vector<std::pair<int, int>>());
            tlb_misses_over_time.push_back(std::vector<std::pair<int, int>>());
            tlb_hit_rate_over_time.push_back(std::vector<std::pair<int, double>>());
            page_faults_over_time.push_back(std::vector<std::pair<int, int>>());
        }
    }

    // Record current state in time series data
    int process_idx = 0;
    for (const auto &p : processes)
    {
        if (p.is_process_stop)
            continue;

        int pid = std::stoi(p.id);

        // Find current stats for this process
        auto hits_it = std::find_if(tlb_hits.begin(), tlb_hits.end(),
                                    [pid](const auto &pair)
                                    { return pair.first == pid; });
        auto misses_it = std::find_if(tlb_misses.begin(), tlb_misses.end(),
                                      [pid](const auto &pair)
                                      { return pair.first == pid; });
        auto rate_it = std::find_if(tlb_hit_rate.begin(), tlb_hit_rate.end(),
                                    [pid](const auto &pair)
                                    { return pair.first == pid; });
        auto faults_it = std::find_if(page_faults.begin(), page_faults.end(),
                                      [pid](const auto &pair)
                                      { return pair.first == pid; });

        // Record data if found
        if (hits_it != tlb_hits.end())
        {
            tlb_hits_over_time[process_idx].push_back({time_step, hits_it->second});
        }
        if (misses_it != tlb_misses.end())
        {
            tlb_misses_over_time[process_idx].push_back({time_step, misses_it->second});
        }
        if (rate_it != tlb_hit_rate.end())
        {
            tlb_hit_rate_over_time[process_idx].push_back({time_step, rate_it->second});
        }
        if (faults_it != page_faults.end())
        {
            page_faults_over_time[process_idx].push_back({time_step, faults_it->second});
        }

        process_idx++;
    }

    // Calculate RAM usage (number of used frames)
    int total_frames = ram_size_bytes / page_size_bytes;
    int used_frames = total_frames - available_frames.size();
    ram_frames_used_over_time.push_back({time_step, used_frames});
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
    if (tlb_capacity <= 0)
        return; // Don't insert if TLB is disabled or has no capacity

    std::string key = pid + "_" + std::to_string(page_no);
    if (tlb.size() >= static_cast<size_t>(tlb_capacity))
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

void VirtualMemorySimulator::print_page_tables(std::ofstream &debug_file)
{
    debug_file << "Page tables for all active processes:\n";
    debug_file << "| Process ID   | Page Number  | Virtual Address    | Physical Frame     | In RAM   |\n";
    debug_file << "| ------------ | ------------ | ------------------ | ------------------ | -------- |\n";

    for (const auto &page_table_entry : page_tables)
    {
        const std::string &process_id = page_table_entry.first;
        const PageTableEntry &pt_entry = page_table_entry.second;

        if (pt_entry.flag != 1)
        {
            // Skip inactive processes
            continue;
        }

        json pt_json = pt_entry.page_table.export_json();
        if (pt_json.find("pages") != pt_json.end() && pt_json["pages"].is_array())
        {
            for (const auto &page_entry : pt_json["pages"])
            {
                if (page_entry.find("page_number") == page_entry.end() ||
                    page_entry.find("frame") == page_entry.end())
                {
                    continue;
                }

                uint64_t page_number = page_entry["page_number"].get<uint64_t>();
                uint64_t frame = page_entry["frame"].get<uint64_t>();
                bool in_ram = true; // Assume all entries are in RAM unless otherwise specified
                if (page_entry.find("in_ram") != page_entry.end())
                {
                    in_ram = page_entry["in_ram"].get<bool>();
                }

                // Calculate virtual address for the page
                uint64_t virtual_address = page_number * page_size_bytes;

                // Format the output to match the desired format exactly
                std::stringstream va_stream, frame_stream;
                va_stream << std::hex << std::setfill('0') << std::setw(8) << virtual_address;
                frame_stream << std::hex << std::setfill('0') << std::setw(9) << frame;

                debug_file << "| " << std::left << std::setw(12) << process_id << " | "
                           << std::right << std::setw(12) << page_number << " | "
                           << "0x" << va_stream.str() << " | "
                           << "0x" << frame_stream.str() << " | "
                           << std::setfill(' ') << std::dec << std::setw(8) << (in_ram ? "1" : "0") << " |\n";
            }
        }
    }
}

int main()
{
    std::ofstream debug("debug.txt", std::ios::out);
    debug << "Starting Virtual Memory Simulator\n";
    debug.close();

    VirtualMemorySimulator simulator("bin");

    std::string command;
    bool should_simulate = false;

    // Check for a special "ready.flag" file that the UI will create when confirming processes
    std::string ready_flag_path = "bin/ready.flag";

    // Add a timeout for waiting for configuration files
    auto start_time = std::chrono::steady_clock::now();
    const int MAX_WAIT_TIME_SEC = 60;

    // Wait for user input from the UI (via file monitoring)
    while (!should_simulate)
    {
        // Check for timeout
        auto current_time = std::chrono::steady_clock::now();
        auto elapsed_time = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();

        if (elapsed_time > MAX_WAIT_TIME_SEC)
        {
            debug.open("debug.txt", std::ios::app);
            debug << "Timeout waiting for processes. Creating default files.\n";
            debug.close();

            // Create default files if we're timing out
            std::ofstream default_env("bin/environment.json");
            if (default_env.is_open())
            {
                default_env << "{\"ram_size_gb\": 1, \"page_size_kb\": 4, \"tlb_size\": 16, \"tlb_enabled\": false, \"virtual_address_size\": \"16-bit\", \"rom_size\": \"32 GB\", \"swap_percent\": 0, \"allocation_type\": \"Contiguous\"}" << std::endl;
                default_env.close();
            }

            std::ofstream default_proc("bin/processes.json");
            if (default_proc.is_open())
            {
                default_proc << "[]" << std::endl;
                default_proc.close();
            }

            // Exit without simulation - we'll wait for user to explicitly start it
            return 0;
        }

        // First check for the ready flag
        if (std::ifstream(ready_flag_path).good())
        {
            should_simulate = true;
            debug.open("debug.txt", std::ios::app);
            debug << "Detected ready flag, starting simulation...\n";
            debug.close();

            // Remove the flag so we don't detect it again later
            std::remove(ready_flag_path.c_str());
            continue;
        }

        // Also check for non-empty process file as a fallback
        try
        {
            std::ifstream env_file("bin/environment.json");
            std::ifstream proc_file("bin/processes.json");

            if (env_file.is_open() && proc_file.is_open())
            {
                // Check if there are processes defined in processes.json
                json proc_settings;
                proc_file >> proc_settings;

                if (proc_settings.is_array() && !proc_settings.empty())
                {
                    should_simulate = true;
                    debug.open("debug.txt", std::ios::app);
                    debug << "Detected processes in configuration, starting simulation...\n";
                    debug.close();
                }
            }
        }
        catch (const std::exception &e)
        {
            // Just wait for valid files
        }

        // Sleep to reduce CPU usage while waiting
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    try
    {
        if (simulator.load_settings())
        {
            // Add simulation timeout
            auto sim_start_time = std::chrono::steady_clock::now();
            const int MAX_SIMULATION_TIME_SEC = 60; // 1 minute max for simulation
                                                    // Set a hard time limit for simulation execution
            auto start_time = std::chrono::steady_clock::now();

            // Run with timeout monitoring
            bool timed_out = false;

            // Run simulation with periodic timeout checks
            std::ofstream status_log("debug.txt", std::ios::app);
            status_log << "Starting simulation with " << MAX_SIMULATION_TIME_SEC << " second timeout\n";
            status_log.close();

            // Create a simple thread status flag
            bool simulation_running = true;

            std::thread simulation_thread([&simulator, &simulation_running]()
                                          {
                try {
                    simulator.simulate();
                    simulation_running = false;
                } catch (const std::exception& e) {
                    std::ofstream error_log("debug.txt", std::ios::app);
                    error_log << "Error in simulation thread: " << e.what() << std::endl;
                    error_log.close();
                    simulation_running = false;
                } });

            // Detach the thread so we don't have to wait for it if it gets stuck
            simulation_thread.detach();

            // Monitor the simulation with timeout
            while (simulation_running)
            {
                auto current_time = std::chrono::steady_clock::now();
                auto elapsed_time = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();

                if (elapsed_time > MAX_SIMULATION_TIME_SEC)
                {
                    std::ofstream timeout_log("debug.txt", std::ios::app);
                    timeout_log << "Simulation timeout after " << MAX_SIMULATION_TIME_SEC << " seconds\n";
                    timeout_log.close();

                    // Create a minimal results file to prevent UI from hanging
                    json minimal_results;
                    minimal_results["status"] = "timeout";
                    minimal_results["message"] = "Simulation timed out after " + std::to_string(MAX_SIMULATION_TIME_SEC) + " seconds";
                    simulator.save_results(minimal_results);

                    timed_out = true;
                    break;
                }

                // Check periodically
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }

            if (timed_out)
            {
                std::cerr << "Simulation timeout, exiting\n";
                return 1;
            }

            // Simulation completed successfully
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
