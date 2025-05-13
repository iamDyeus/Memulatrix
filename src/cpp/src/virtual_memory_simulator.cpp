#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <vector>
#include <set>
#include <random>
#include <string>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <iomanip>
#include "../include/virtual_memory_simulator.h"

#pragma comment(lib, "Ws2_32.lib")

VirtualMemorySimulator::VirtualMemorySimulator(SocketHandler* handler) : socket_handler(handler), total_hits(0), total_misses(0), total_faults(0), tlb_capacity(0) {
    std::ofstream debug("debug.txt", std::ios::out);
    debug << "Virtual Memory Simulator initialized\n";
    debug.close();
}

VirtualMemorySimulator::~VirtualMemorySimulator() {
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Virtual Memory Simulator destroyed\n";
    debug.close();
}

void VirtualMemorySimulator::load_settings(const json& settings) {
    try {
        ram_size_bytes = settings["ram_size_gb"].get<uint64_t>() * 1024ULL * 1024 * 1024;
        page_size_bytes = settings["page_size_kb"].get<uint64_t>() * 1024;
        tlb_size = settings["tlb_size"].get<int>();
        tlb_enabled = settings["tlb_enabled"].get<bool>();
        virtual_address_size = settings["virtual_address_size"].get<std::string>();
        rom_size = settings["rom_size"].get<std::string>();
        swap_percent = settings["swap_percent"].get<int>();
        allocation_type = settings["allocation_type"].get<std::string>();

        int entry_size = (virtual_address_size == "16-bit") ? 2 : (virtual_address_size == "32-bit") ? 4 : 8;
        tlb_capacity = (tlb_size * 1024) / entry_size;

        processes.clear();
        for (const auto& proc_json : settings["processes"]) {
            Process p;
            p.id = proc_json["id"].get<std::string>();
            p.name = proc_json["name"].get<std::string>();
            p.size_bytes = proc_json["size_gb"].get<int>() * 1024ULL * 1024 * 1024;
            p.type = proc_json["type"].get<std::string>();
            p.has_priority = proc_json["has_priority"].get<bool>();
            p.is_process_stop = proc_json["is_process_stop"].get<bool>();
            processes.push_back(p);
        }

        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Settings loaded: RAM=" << ram_size_bytes / (1024ULL * 1024 * 1024) << "GB, "
              << "PageSize=" << page_size_bytes / 1024 << "KB, "
              << "TLBSize=" << tlb_size << "KB, "
              << "TLBEnabled=" << tlb_enabled << ", "
              << "VASize=" << virtual_address_size << ", "
              << "ROM=" << rom_size << ", "
              << "Swap=" << swap_percent << "%, "
              << "Allocation=" << allocation_type << "\n";
        for (const auto& p : processes) {
            debug << "Process: ID=" << p.id << ", Name=" << p.name << ", Size="
                  << p.size_bytes / (1024ULL * 1024 * 1024) << "GB, "
                  << "Type=" << p.type << ", Priority=" << p.has_priority
                  << ", Stopped=" << p.is_process_stop << "\n";
        }
        debug.close();

        std::cout << "Settings loaded: RAM=" << ram_size_bytes / (1024ULL * 1024 * 1024) << "GB, "
                  << "PageSize=" << page_size_bytes / 1024 << "KB, "
                  << "TLBSize=" << tlb_size << ", "
                  << "TLBEnabled=" << tlb_enabled << ", "
                  << "VASize=" << virtual_address_size << ", "
                  << "ROM=" << rom_size << ", "
                  << "Swap=" << swap_percent << "%, "
                  << "Allocation=" << allocation_type << "\n";
        for (const auto& p : processes) {
            std::cout << "Process: ID=" << p.id << ", Name=" << p.name << ", Size="
                      << p.size_bytes / (1024ULL * 1024 * 1024) << "GB\n";
        }
    } catch (const std::exception& e) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Error parsing settings: " << e.what() << "\n";
        debug.close();
        std::cerr << "Error parsing settings: " << e.what() << "\n";
        throw;
    }
}

void VirtualMemorySimulator::tlb_insert(const std::string& pid, uint64_t page_no, uint64_t virtual_address, uint64_t frame_no, int process_status) {
    std::string key = pid + "_" + std::to_string(page_no);
    if (tlb.size() >= tlb_capacity) {
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

void VirtualMemorySimulator::tlb_remove_process(const std::string& pid) {
    std::vector<std::string> keys_to_remove;
    for (const auto& entry : tlb) {
        if (entry.second.pid == pid) {
            keys_to_remove.push_back(entry.first);
        }
    }
    for (const auto& k : keys_to_remove) {
        tlb.erase(k);
        std::queue<std::string> temp;
        while (!tlb_fifo.empty()) {
            if (tlb_fifo.front() != k) {
                temp.push(tlb_fifo.front());
            }
            tlb_fifo.pop();
        }
        tlb_fifo = temp;
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "TLB: Removed entry " << k << " for process " << pid << "\n";
        debug.close();
    }
}

uint64_t VirtualMemorySimulator::tlb_get_frame(const std::string& pid, uint64_t page_no) {
    std::string key = pid + "_" + std::to_string(page_no);
    auto it = tlb.find(key);
    if (it != tlb.end() && it->second.process_status == 1) {
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

void VirtualMemorySimulator::simulate() {
    std::ofstream debug("debug.txt", std::ios::app);
    
    tlb_hits.clear();
    tlb_misses.clear();
    tlb_hit_rate.clear();
    page_faults.clear();
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;
    tlb.clear();
    while (!tlb_fifo.empty()) tlb_fifo.pop();

    debug << "Starting simulation\n";

    // Clean up deleted processes
    std::vector<std::string> json_pids;
    for (const auto& p : processes) {
        json_pids.push_back(p.id);
    }
    std::vector<std::string> deleted_pids;
    for (auto it = page_tables.begin(); it != page_tables.end();) {
        if (std::find(json_pids.begin(), json_pids.end(), it->first) == json_pids.end()) {
            it->second.flag = -1;
            deleted_pids.push_back(it->first);
            debug << "Process " << it->first << ": Marked as deleted (not in JSON)\n";
            it->second.page_table.free_frames(available_frames, available_table_frames);
            it->second.page_table.free_swap_frames(available_swap_frames);
            tlb_remove_process(it->first);
            it = page_tables.erase(it);
            debug << "Process " << deleted_pids.back() << ": Freed resources and removed from page_tables\n";
        } else {
            ++it;
        }
    }

    int entry_size;
    uint64_t va_max;
    if (virtual_address_size == "16-bit") {
        entry_size = 2;
        va_max = 0xFFFF;
    } else if (virtual_address_size == "32-bit") {
        entry_size = 4;
        va_max = 0xFFFFFFFF;
    } else {
        entry_size = 8;
        va_max = 0xFFFFFFFFFFFFFFFFULL;
    }

    uint64_t rom_size_bytes;
    std::stringstream ss(rom_size);
    double rom_gb;
    ss >> rom_gb;
    rom_size_bytes = static_cast<uint64_t>(rom_gb * 1024ULL * 1024 * 1024);

    uint64_t total_process_size = 0;
    int active_processes = 0;
    for (const auto& p : processes) {
        if (!p.is_process_stop) {
            total_process_size += p.size_bytes;
            active_processes++;
        }
    }
    uint64_t swap_size_bytes = swap_percent > 0 ? (rom_size_bytes * swap_percent / 100) : 0;
    uint64_t total_swap_frames = swap_percent > 0 ? swap_size_bytes / page_size_bytes : 0;
    uint64_t effective_ram = ram_size_bytes * 0.99;
    uint64_t max_size = effective_ram + swap_size_bytes;
    if (total_process_size > max_size) {
        debug << "Insufficient space: Total process size (" << total_process_size / (1024ULL * 1024 * 1024)
              << "GB) exceeds effective RAM (" << effective_ram / (1024ULL * 1024 * 1024)
              << "GB) + Swap (" << swap_size_bytes / (1024ULL * 1024 * 1024) << "GB)\n";
        debug.close();
        std::cout << "Insufficient space: Total process size (" << total_process_size / (1024ULL * 1024 * 1024)
                  << "GB) exceeds effective RAM (" << effective_ram / (1024ULL * 1024 * 1024)
                  << "GB) + Swap (" << swap_size_bytes / (1024ULL * 1024 * 1024) << "GB)\n";
        return;
    }

    uint64_t total_frames = ram_size_bytes / page_size_bytes;
    uint64_t effective_frames = static_cast<uint64_t>(total_frames * 0.99);
    uint64_t table_frame_limit = static_cast<uint64_t>(ceil(total_frames * 0.01));
    debug << std::fixed << std::setprecision(2);
    debug << "Effective RAM: " << effective_ram / (1024.0 * 1024 * 1024) << " GB, "
          << "Effective frames: " << effective_frames << "\n";

    if (available_frames.empty()) {
        if (allocation_type == "Contiguous") {
            uint64_t start_frame = table_frame_limit;
            for (uint64_t i = start_frame; i < total_frames; ++i) {
                available_frames.push_back(i);
            }
        } else {
            for (uint64_t i = table_frame_limit; i < total_frames; ++i) {
                available_frames.push_back(i);
            }
        }
    }
    if (available_table_frames.empty()) {
        available_table_frames.resize(table_frame_limit);
        for (uint64_t i = 0; i < table_frame_limit; ++i) {
            available_table_frames[i] = i;
        }
    }
    if (available_swap_frames.empty() && swap_percent > 0) {
        available_swap_frames.resize(total_swap_frames);
        for (uint64_t i = 0; i < total_swap_frames; ++i) {
            available_swap_frames[i] = i;
        }
    }
    debug << "Total RAM frames: " << total_frames << ", Effective frames: " << effective_frames
          << ", Table frames: " << table_frame_limit << ", Swap frames: " << total_swap_frames << "\n";

    uint64_t total_table_size = 0;
    for (const auto& p : processes) {
        if (p.is_process_stop) continue;
        uint64_t num_pages = (p.size_bytes + page_size_bytes - 1) / page_size_bytes;
        int levels = std::max(1, static_cast<int>(ceil(log2(num_pages) / log2(page_size_bytes / entry_size))));
        uint64_t table_size = num_pages * entry_size;
        if (levels > 1) {
            uint64_t entries_per_table = page_size_bytes / entry_size;
            table_size += entries_per_table * entry_size;
            if (levels > 2) table_size += entries_per_table * entries_per_table * entry_size;
        }
        debug << "Process " << p.id << ": Page table size = " << table_size / 1024.0 << " KB\n";
        total_table_size += table_size;
    }
    if (total_table_size > ram_size_bytes / 100) {
        debug << "Error: Page table size (" << total_table_size / 1024.0 << " KB) exceeds 1% of RAM\n";
        debug.close();
        std::cout << "Error: Page table size exceeds 1% of RAM\n";
        return;
    }
    debug << "Total page table size for all processes = " << total_table_size / 1024.0 << " KB\n";

    uint64_t block_size_bytes;
    if (ram_size_bytes < 16ULL * 1024 * 1024 * 1024) {
        block_size_bytes = 1ULL * 1024 * 1024;
    } else if (ram_size_bytes < 32ULL * 1024 * 1024 * 1024) {
        block_size_bytes = 4ULL * 1024 * 1024;
    } else {
        block_size_bytes = 16ULL * 1024 * 1024;
    }

    double frame_percent = active_processes >= 2 ? (100.0 / active_processes - 2) : 100.0;
    if (frame_percent < 1.0) frame_percent = 1.0;

    std::random_device rd;
    std::mt19937 gen(rd());
    for (const auto& p : processes) {
        if (p.is_process_stop) continue;
        int flag = 1;
        uint64_t num_pages = (p.size_bytes + page_size_bytes - 1) / page_size_bytes;
        uint64_t last_page_va = (num_pages - 1) * page_size_bytes;
        if (last_page_va > va_max) {
            debug << "Process " << p.id << ": Cannot run in " << virtual_address_size
                  << " environment. Last page VA (0x" << std::hex << last_page_va
                  << ") exceeds maximum address (0x" << va_max
                  << "). Requires a larger architecture.\n";
            std::cout << "Process " << p.id << ": Cannot run in " << virtual_address_size
                      << " environment. Last page VA (0x" << std::hex << last_page_va
                      << ") exceeds maximum address (0x" << va_max
                      << "). Requires a larger architecture.\n";
            continue;
        }
        debug << "Process " << p.id << ": Creating page table for " << num_pages << " pages, Flag=" << flag << "\n";
        PageTable pt(num_pages, page_size_bytes, entry_size, allocation_type, total_frames, total_frames, ram_size_bytes, frame_percent, p.id, virtual_address_size);
        if (!pt.allocate(block_size_bytes, available_frames, available_table_frames, gen, available_swap_frames)) {
            debug << "Process " << p.id << ": Allocation failed, Name=" << p.name << "\n";
            std::cout << "Process " << p.id << ": Allocation failed, Name=" << p.name << "\n";
            continue;
        }
        uint64_t top_level_frame = pt.get_top_level_frame();
        page_tables.emplace(p.id, PageTableEntry(top_level_frame, std::move(pt), flag, -1));
        debug << "Process " << p.id << ": Page table allocated, base address=0x"
              << std::hex << top_level_frame << std::dec << ", Flag=" << flag << "\n";

        auto it = page_tables.find(p.id);
        it->second.page_table.set_frame_availability(flag == 1);

        uint64_t sample_page = 1;
        if (num_pages >= sample_page) {
            lookup(p.id, sample_page);
        }
    }

    debug << "Page tables for all active processes:\n";
    debug << "| " << std::left << std::setw(12) << "Process ID"
          << " | " << std::setw(12) << "Page Number"
          << " | " << std::setw(18) << "Virtual Address"
          << " | " << std::setw(18) << "Physical Frame"
          << " | " << std::setw(8) << "In RAM" << " |\n";
    debug << "| " << std::string(12, '-') << " | " << std::string(12, '-')
          << " | " << std::string(18, '-') << " | " << std::string(18, '-')
          << " | " << std::string(8, '-') << " |\n";
    for (const auto& p : processes) {
        if (p.is_process_stop) continue;
        auto it = page_tables.find(p.id);
        if (it != page_tables.end() && it->second.flag == 1) {
            json pt_json = it->second.page_table.export_json();
            for (const auto& entry : pt_json) {
                debug << "| " << std::left << std::setw(12) << entry["process_id"].get<std::string>()
                      << " | " << std::right << std::setw(12) << entry["page_number"].get<uint64_t>()
                      << " | " << std::left << std::setw(18) << entry["virtual_address"].get<std::string>()
                      << " | " << std::setw(18) << entry["physical_frame"].get<std::string>()
                      << " | " << std::setw(8) << (entry["in_ram"].get<bool>() ? "1" : "0") << " |\n";
            }
        } else {
            debug << "Process ID=" << p.id << ", Name=" << p.name << ": No active page table\n";
        }
    }

    int simulation_duration = 100;
    std::uniform_int_distribution<> access_dist(0, 1);
    std::uniform_int_distribution<uint64_t> va_dist(0, va_max);

    for (int t = 0; t < simulation_duration; t++) {
        for (const auto& p : processes) {
            if (p.is_process_stop) continue;
            if (access_dist(gen) == 0) continue;

            uint64_t virtual_address = va_dist(gen) % p.size_bytes;
            uint64_t page_no = virtual_address / page_size_bytes + 1;
            auto it = page_tables.find(p.id);
            if (it == page_tables.end() || it->second.flag != 1) continue;

            it->second.last_executed_page = static_cast<int64_t>(page_no);

            if (tlb_enabled) {
                uint64_t frame = tlb_get_frame(p.id, page_no);
                bool hit = (frame != UINT64_MAX);
                if (hit) {
                    total_hits++;
                } else {
                    total_misses++;
                    frame = it->second.page_table.lookup(page_no);
                    bool in_ram = it->second.page_table.access(virtual_address);
                    if (in_ram) {
                        tlb_insert(p.id, page_no, virtual_address, frame, it->second.flag);
                    }
                }
            }

            bool fault = it->second.page_table.access(virtual_address);
            if (fault) total_faults++;

            tlb_hits.push_back({t, total_hits});
            tlb_misses.push_back({t, total_misses});
            double hit_rate = (total_hits + total_misses) > 0 ? (double)total_hits / (total_hits + total_misses) : 0.0;
            tlb_hit_rate.push_back({t, hit_rate});
            page_faults.push_back({t, total_faults});
        }
    }

    if (!tlb_enabled) {
        tlb_hits.clear();
        tlb_misses.clear();
        tlb_hit_rate.clear();
        for (int t = 0; t < simulation_duration; t++) {
            tlb_hits.push_back({t, 0});
            tlb_misses.push_back({t, 0});
            tlb_hit_rate.push_back({t, 0.0});
        }
    }

    debug << "Simulation completed: Total TLB Hits=" << total_hits << ", Total TLB Misses=" << total_misses
          << ", Total Page Faults=" << total_faults << "\n";
    debug.close();
}

json VirtualMemorySimulator::export_results() {
    json result;
    result["tlb_stats"]["hits"] = tlb_hits;
    result["tlb_stats"]["misses"] = tlb_misses;
    result["tlb_stats"]["hit_rate"] = tlb_hit_rate;
    result["tlb_stats"]["total_hits"] = total_hits;
    result["tlb_stats"]["total_misses"] = total_misses;
    result["page_faults"] = page_faults;
    result["total_faults"] = total_faults;

    if (ram_size_bytes == 0) {
        result["error"] = "Insufficient space";
    } else {
        json pts;
        for (const auto& pt : page_tables) {
            if (pt.second.flag == -1) continue;
            json pt_entry;
            pt_entry["process_id"] = pt.first;
            pt_entry["base_address"] = pt.second.top_level_frame;
            pt_entry["table"] = pt.second.page_table.export_json();
            pt_entry["flag"] = pt.second.flag;
            pt_entry["last_executed_page"] = pt.second.last_executed_page;
            pts.push_back(pt_entry);
        }
        result["page_tables"] = pts;
    }

    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Exporting results: " << result.dump().substr(0, 50) << "...\n";
    debug.close();

    return result;
}

void VirtualMemorySimulator::reset() {
    processes.clear();
    tlb_hits.clear();
    tlb_misses.clear();
    tlb_hit_rate.clear();
    page_faults.clear();
    page_tables.clear();
    tlb.clear();
    while (!tlb_fifo.empty()) tlb_fifo.pop();
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;
    available_frames.clear();
    available_table_frames.clear();
    available_swap_frames.clear();

    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Simulator reset\n";
    debug.close();
}

std::string VirtualMemorySimulator::read_socket() {
    return socket_handler->read();
}

bool VirtualMemorySimulator::write_socket(const std::string& data) {
    return socket_handler->write(data);
}

bool VirtualMemorySimulator::accept_connection() {
    return socket_handler->accept_connection();
}

void VirtualMemorySimulator::lookup(const std::string& process_id, uint64_t page_number) {
    auto it = page_tables.find(process_id);
    if (it != page_tables.end() && it->second.flag == 1) {
        it->second.last_executed_page = static_cast<int64_t>(page_number);
        it->second.page_table.lookup(page_number);
    } else {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id << ": Not found or not active for lookup\n";
        debug.close();
        std::cout << "Process " << process_id << ": Not found or not active for lookup\n";
    }
}

uint64_t VirtualMemorySimulator::get_frame_number(const std::string& pid, uint64_t page_number) {
    auto it = page_tables.find(pid);
    if (it == page_tables.end() || it->second.flag != 1) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Invalid or inactive process ID: " << pid << "\n";
        debug.close();
        return UINT64_MAX;
    }
    return it->second.page_table.lookup(page_number);
}

int main() {
    std::ofstream debug("debug.txt", std::ios::out);
    debug << "Starting Virtual Memory Simulator\n";
    debug.close();

    SocketHandler* socket_handler = nullptr;
    try {
        socket_handler = new SocketHandler();
        VirtualMemorySimulator sim(socket_handler);

        while (true) {
            if (!sim.accept_connection()) {
                std::cerr << "Connection failed, retrying..." << std::endl;
                Sleep(1000);
                continue;
            }

            while (true) {
                std::string config_str = sim.read_socket();
                if (config_str.empty()) {
                    break;
                }

                json settings;
                try {
                    settings = json::parse(config_str);
                    std::ofstream debug("debug.txt", std::ios::app);
                    debug << "Parsed JSON settings: " << settings.dump().substr(0, 50) << "...\n";
                    debug.close();
                    std::cout << "Parsed JSON settings: " << settings.dump().substr(0, 50) << "..." << std::endl;
                } catch (const json::parse_error& e) {
                    std::ofstream debug("debug.txt", std::ios::app);
                    debug << "JSON parse error: " << e.what() << "\n";
                    debug.close();
                    std::cerr << "JSON parse error: " << e.what() << "\n";
                    continue;
                }

                try {
                    sim.load_settings(settings);
                    sim.simulate();
                    json result = sim.export_results();
                    std::string result_str = result.dump();
                    if (!sim.write_socket(result_str)) {
                        std::ofstream debug("debug.txt", std::ios::app);
                        debug << "Failed to send results, client may have disconnected\n";
                        debug.close();
                        std::cerr << "Failed to send results, client may have disconnected..." << std::endl;
                        break;
                    } else {
                        std::ofstream debug("debug.txt", std::ios::app);
                        debug << "Simulation completed and results sent\n";
                        debug.close();
                        std::cout << "Simulation completed and results sent" << std::endl;
                    }
                } catch (const std::exception& e) {
                    std::ofstream debug("debug.txt", std::ios::app);
                    debug << "Simulation error: " << e.what() << "\n";
                    debug.close();
                    std::cerr << "Simulation error: " << e.what() << "\n";
                }

                sim.reset();
            }
        }
    } catch (const std::exception& e) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Fatal error: " << e.what() << "\n";
        debug.close();
        std::cerr << "Fatal error: " << e.what() << "\n";
        if (socket_handler) {
            delete socket_handler;
        }
        return 1;
    }
    return 0;
}