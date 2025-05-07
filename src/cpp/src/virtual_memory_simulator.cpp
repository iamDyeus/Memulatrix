#include <iostream>
#include <fstream>
#include <stdexcept>
#include <vector>
#include <set>
#include <random>
#include "..\include\virtual_memory_simulator.h"

// Simple TLB simulation
class TLB {
public:
    TLB(int size) : size_(size) {
        entries_.resize(size, {0, -1}); // {virtual_address, page_number}
    }

    bool access(uint64_t virtual_address) {
        // Check if the address is in the TLB
        for (const auto& entry : entries_) {
            if (entry.first == virtual_address) {
                return true; // TLB hit
            }
        }
        // TLB miss: Update TLB (simple FIFO replacement)
        entries_[next_entry_] = {virtual_address, 0}; // Dummy page number
        next_entry_ = (next_entry_ + 1) % size_;
        return false;
    }

private:
    int size_;
    std::vector<std::pair<uint64_t, int>> entries_;
    int next_entry_ = 0;
};

// Simple Page Table simulation
class PageTable {
public:
    PageTable(uint64_t ram_size_bytes, uint64_t page_size_bytes)
        : ram_size_bytes_(ram_size_bytes), page_size_bytes_(page_size_bytes) {
        // Initialize page table (simplified)
    }

    bool access(uint64_t virtual_address) {
        uint64_t page_number = virtual_address / page_size_bytes_;
        // Check if the page is in memory (simplified simulation)
        if (pages_in_memory_.find(page_number) != pages_in_memory_.end()) {
            return false; // Page hit
        }
        // Page fault: Add to memory (simplified)
        pages_in_memory_.insert(page_number);
        return true; // Page fault
    }

private:
    uint64_t ram_size_bytes_;
    uint64_t page_size_bytes_;
    std::set<uint64_t> pages_in_memory_;
};

VirtualMemorySimulator::VirtualMemorySimulator(const std::string& env_file, const std::string& proc_file)
    : env_file_path(env_file), proc_file_path(proc_file) {
    if (env_file_path.empty()) {
        throw std::runtime_error("Environment file path is empty");
    }
    if (proc_file_path.empty()) {
        throw std::runtime_error("Processes file path is empty");
    }
    load_environment_settings();
}

void VirtualMemorySimulator::load_environment_settings() {
    std::ifstream file(env_file_path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open environment settings file: " + env_file_path);
    }

    // Check file size to confirm it's not empty
    file.seekg(0, std::ios::end);
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    std::cout << "Environment file size: " << size << " bytes\n";
    std::cout.flush();
    if (size == 0) {
        throw std::runtime_error("Environment settings file is empty: " + env_file_path);
    }

    json settings;
    try {
        file >> settings;
    } catch (const json::parse_error& e) {
        file.close();
        throw std::runtime_error("JSON parse error in " + env_file_path + ": " + e.what());
    }
    file.close();

    try {
        ram_size_bytes = std::stoull(settings["ram_size_gb"].get<std::string>()) * 1024ULL * 1024 * 1024;
        page_size_bytes = std::stoul(settings["page_size_kb"].get<std::string>()) * 1024;
        tlb_size = std::stoul(settings["tlb_size"].get<std::string>());
        tlb_enabled = settings["tlb_enabled"].get<bool>();
        virtual_address_size = settings["virtual_address_size"].get<std::string>();
        rom_size = settings["rom_size"].get<std::string>();
    } catch (const std::exception& e) {
        throw std::runtime_error("Error parsing environment settings: " + std::string(e.what()));
    }

    std::cout << "=== Environment Settings Loaded ===\n"
              << "RAM Size: " << ram_size_bytes / (1024ULL * 1024 * 1024) << " GB\n"
              << "Page Size: " << page_size_bytes / 1024 << " KB\n"
              << "TLB Size: " << tlb_size << "\n"
              << "TLB Enabled: " << (tlb_enabled ? "Yes" : "No") << "\n"
              << "Virtual Address Size: " << virtual_address_size << "\n"
              << "ROM Size: " << rom_size << "\n"
              << "===================================\n\n";
    std::cout.flush();
}

std::vector<Process> VirtualMemorySimulator::load_processes() {
    std::vector<Process> processes;
    std::ifstream file(proc_file_path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open processes file: " + proc_file_path);
    }

    // Check file size to confirm it's not empty
    file.seekg(0, std::ios::end);
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    std::cout << "Processes file size: " << size << " bytes\n";
    std::cout.flush();
    if (size == 0) {
        throw std::runtime_error("Processes file is empty: " + proc_file_path);
    }

    json process_list;
    try {
        file >> process_list;
    } catch (const json::parse_error& e) {
        file.close();
        throw std::runtime_error("JSON parse error in " + proc_file_path + ": " + e.what());
    }
    file.close();

    for (const auto& proc_json : process_list) {
        Process p;
        try {
            p.id = proc_json["id"].get<std::string>();
            p.name = proc_json["name"].get<std::string>();
            p.size_bytes = proc_json["size_gb"].get<int>() * 1024ULL * 1024 * 1024;
            p.type = proc_json["type"].get<std::string>();
            p.has_priority = proc_json["has_priority"].get<bool>();
            p.is_process_stop = proc_json["is_process_stop"].get<bool>();

            std::string va_str = proc_json["virtual_address"].get<std::string>();
            if (va_str.substr(0, 2) == "0x") {
                va_str = va_str.substr(2);
            }
            p.virtual_address = std::stoull(va_str, nullptr, 16);
        } catch (const std::exception& e) {
            std::cerr << "Error parsing process ID " << (p.id.empty() ? "unknown" : p.id) << ": " << e.what() << "\n";
            std::cerr.flush();
            continue;
        }
        processes.push_back(p);
    }

    return processes;
}

void VirtualMemorySimulator::print_processes(const std::vector<Process>& processes) {
    if (processes.empty()) {
        std::cout << "No active processes.\n";
        return;
    }

    std::cout << "=== Active Processes ===\n";
    for (const auto& proc : processes) {
        std::cout << "Process ID: " << proc.id
                  << ", Name: " << proc.name
                  << ", Size: " << proc.size_bytes / (1024ULL * 1024 * 1024) << "GB"
                  << ", Type: " << proc.type
                  << ", Has Priority: " << (proc.has_priority ? "Yes" : "No")
                  << ", Virtual Address: 0x" << std::hex << proc.virtual_address << std::dec
                  << ", Stopped: " << (proc.is_process_stop ? "Yes" : "No")
                  << std::endl;
    }
    std::cout << "========================\n\n";
    std::cout.flush();
}

void VirtualMemorySimulator::simulate() {
    // Load processes
    auto processes = load_processes();
    print_processes(processes);

    // Initialize simulation state
    tlb_hits.clear();
    tlb_misses.clear();
    tlb_hit_rate.clear();
    page_faults.clear();
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;

    // Initialize TLB and Page Table
    TLB tlb(tlb_size);
    PageTable page_table(ram_size_bytes, page_size_bytes);

    // Simulation parameters
    int simulation_duration = 100; // 100 time steps (e.g., 100ms each)
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> access_dist(0, 1); // Randomly decide to access memory

    // Simulate memory accesses
    for (int t = 0; t < simulation_duration; t++) {
        for (const auto& proc : processes) {
            if (proc.is_process_stop) continue; // Skip stopped processes

            // Simulate a memory access (randomly decide whether to access)
            if (access_dist(gen) == 0) continue;

            uint64_t virtual_address = proc.virtual_address;

            // TLB access (if enabled)
            if (tlb_enabled) {
                bool hit = tlb.access(virtual_address);
                if (hit) total_hits++;
                else total_misses++;
            }

            // Page table access
            bool fault = page_table.access(virtual_address);
            if (fault) total_faults++;

            // Update time-series data
            tlb_hits.push_back({t, total_hits});
            tlb_misses.push_back({t, total_misses});
            double hit_rate = (total_hits + total_misses) > 0
                ? (double)total_hits / (total_hits + total_misses)
                : 0.0;
            tlb_hit_rate.push_back({t, hit_rate});
            page_faults.push_back({t, total_faults});
        }
    }

    // If TLB is disabled, set TLB stats to empty
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
}

void VirtualMemorySimulator::export_results(const std::string& output_path) {
    json result;
    result["tlb_stats"]["hits"] = tlb_hits;
    result["tlb_stats"]["misses"] = tlb_misses;
    result["tlb_stats"]["hit_rate"] = tlb_hit_rate;
    result["page_faults"] = page_faults;

    std::ofstream file(output_path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not write to file: " + output_path);
    }
    file << result.dump(4); // Pretty-print with indentation
    file.close();
}

int main(int argc, char* argv[]) {
    // Check command-line arguments
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <environment_file> <processes_file>\n";
        std::cerr.flush();
        return 1;
    }

    std::string env_path = argv[1];
    std::string proc_path = argv[2];
    const std::string result_path = "D:\\projects\\Memulatrix\\bin\\result.json";

    std::cout << "Starting Virtual Memory Simulator...\n";
    std::cout << "Environment file: " << env_path << "\n";
    std::cout << "Processes file: " << proc_path << "\n";
    std::cout.flush();

    // Validate file existence and non-empty
    std::ifstream env_file(env_path);
    if (!env_file.is_open()) {
        std::cerr << "Could not open environment file: " << env_path << "\n";
        std::cerr.flush();
        return 1;
    }
    env_file.seekg(0, std::ios::end);
    if (env_file.tellg() == 0) {
        std::cerr << "Environment file is empty: " << env_path << "\n";
        std::cerr.flush();
        env_file.close();
        return 1;
    }
    env_file.close();

    std::ifstream proc_file(proc_path);
    if (!proc_file.is_open()) {
        std::cerr << "Could not open processes file: " << proc_path << "\n";
        std::cerr.flush();
        return 1;
    }
    proc_file.seekg(0, std::ios::end);
    if (proc_file.tellg() == 0) {
        std::cerr << "Processes file is empty: " << proc_path << "\n";
        std::cerr.flush();
        proc_file.close();
        return 1;
    }
    proc_file.close();

    try {
        // Initialize the simulator with the provided paths
        VirtualMemorySimulator sim(env_path, proc_path);

        // Run simulation (this will also print the processes)
        sim.simulate();

        // Export results
        sim.export_results(result_path);
        std::cout << "Simulation completed, results exported to " << result_path << "\n";
        std::cout.flush();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        std::cerr.flush();
        // Write an empty result.json with error message
        json error_result;
        error_result["error"] = e.what();
        std::ofstream file(result_path);
        file << error_result.dump(4);
        file.close();
        std::cout << "Error result exported to " << result_path << "\n";
        std::cout.flush();
        return 1;
    }

    return 0;
}