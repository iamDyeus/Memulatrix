#include <iostream>
#include <fstream>
#include <stdexcept>
#include "..\include\virtual_memory_simulator.h"

VirtualMemorySimulator::VirtualMemorySimulator(const std::string& env_file, const std::string& proc_file)
    : env_file_path(env_file), proc_file_path(proc_file) {
    load_environment_settings();
}

void VirtualMemorySimulator::load_environment_settings() {
    std::ifstream file(env_file_path);
    if (!file.is_open()) {
        std::cerr << "Could not open " << env_file_path << std::endl;
        // Default values in case the file is missing
        ram_size_bytes = 1ULL * 1024 * 1024 * 1024; // 1GB
        page_size_bytes = 4096; // 4KB
        tlb_size = 16;
        tlb_enabled = true;
        virtual_address_size = "16-bit";
        rom_size = "32 GB";
        return;
    }

    json settings;
    try {
        file >> settings;
    } catch (const json::parse_error& e) {
        std::cerr << "JSON parse error in " << env_file_path << ": " << e.what() << std::endl;
        file.close();
        ram_size_bytes = 1ULL * 1024 * 1024 * 1024;
        page_size_bytes = 4096;
        tlb_size = 16;
        tlb_enabled = true;
        virtual_address_size = "16-bit";
        rom_size = "32 GB";
        return;
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
        std::cerr << "Error parsing environment settings: " << e.what() << std::endl;
        ram_size_bytes = 1ULL * 1024 * 1024 * 1024;
        page_size_bytes = 4096;
        tlb_size = 16;
        tlb_enabled = true;
        virtual_address_size = "16-bit";
        rom_size = "32 GB";
        return;
    }

    std::cout << "Environment Settings Loaded:\n"
              << "RAM Size: " << ram_size_bytes / (1024ULL * 1024 * 1024) << " GB\n"
              << "Page Size: " << page_size_bytes / 1024 << " KB\n"
              << "TLB Size: " << tlb_size << "\n"
              << "TLB Enabled: " << (tlb_enabled ? "Yes" : "No") << "\n"
              << "Virtual Address Size: " << virtual_address_size << "\n"
              << "ROM Size: " << rom_size << "\n\n";
}

std::vector<Process> VirtualMemorySimulator::load_processes() {
    std::vector<Process> processes;
    std::ifstream file(proc_file_path);
    if (!file.is_open()) {
        // Do not print error on startup; just return empty vector
        return processes;
    }

    json process_list;
    try {
        file >> process_list;
    } catch (const json::parse_error& e) {
        std::cerr << "JSON parse error in " << proc_file_path << ": " << e.what() << std::endl;
        file.close();
        return processes;
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
            std::cerr << "Error parsing process ID " << (p.id.empty() ? "unknown" : p.id) << ": " << e.what() << std::endl;
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

    std::cout << "Active Processes:\n";
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
    std::cout << std::endl;
}

int main(int argc, char* argv[]) {
    try {
        // Use command-line arguments for file paths
        if (argc != 3) {
            std::cerr << "Usage: " << argv[0] << " <environment_settings.json> <processes.json>" << std::endl;
            return 1;
        }
        std::string env_file = argv[1];
        std::string proc_file = argv[2];

        // Initialize the simulator
        VirtualMemorySimulator sim(env_file, proc_file);
        auto processes = sim.load_processes();
        sim.print_processes(processes);

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}