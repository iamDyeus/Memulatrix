#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include "..\include\virtual_memory_simulator.h"

std::string VirtualMemorySimulator::trim(const std::string& str) {
    std::string result = str;
    result.erase(0, result.find_first_not_of(" \n\r\t\""));
    result.erase(result.find_last_not_of(" \n\r\t\"") + 1);
    return result;
}

VirtualMemorySimulator::VirtualMemorySimulator(uint64_t ram_size, uint32_t page_size, uint32_t tlb_sz, bool tlb_on)
    : ram_size_bytes(ram_size), page_size_bytes(page_size), tlb_size(tlb_sz), tlb_enabled(tlb_on) {
}

std::vector<Process> VirtualMemorySimulator::load_processes() {
    std::vector<Process> processes;
    std::ifstream file("..\\..\\python\\ui\\processes.json");
    if (!file.is_open()) {
        std::cerr << "Could not open processes.json" << std::endl;
        return processes;
    }

    // Read the entire file into a string
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();
    file.close();

    // Remove outer brackets and whitespace
    content = trim(content);
    if (content.empty() || content[0] != '[' || content[content.size() - 1] != ']') {
        std::cerr << "Invalid JSON format: not a list" << std::endl;
        return processes;
    }
    content = content.substr(1, content.size() - 2); // Remove [ and ]

    // Split into individual process objects
    std::vector<std::string> process_strings;
    int brace_count = 0;
    std::string current_process = "";
    for (char c : content) {
        if (c == '{') brace_count++;
        if (c == '}') brace_count--;
        current_process += c;
        if (brace_count == 0 && !current_process.empty()) {
            process_strings.push_back(current_process);
            current_process = "";
        }
    }

    // Parse each process object
    for (std::string proc_str : process_strings) {
        proc_str = trim(proc_str);
        if (proc_str.empty() || proc_str[0] != '{' || proc_str[proc_str.size() - 1] != '}') continue;
        proc_str = proc_str.substr(1, proc_str.size() - 2); // Remove { and }

        Process p;
        std::stringstream ss(proc_str);
        std::string token;
        while (std::getline(ss, token, ',')) {
            token = trim(token);
            size_t colon = token.find(':');
            if (colon == std::string::npos) continue;
            std::string key = trim(token.substr(0, colon));
            std::string value = trim(token.substr(colon + 1));

            if (key == "id") p.id = value;
            else if (key == "name") p.name = value;
            else if (key == "size_gb") p.size_bytes = std::stoi(value) * 1024ULL * 1024 * 1024;
            else if (key == "type") p.type = value;
            else if (key == "priority") p.priority = value;
        }
        processes.push_back(p);
    }

    return processes;
}

int main() {
    VirtualMemorySimulator sim(1ULL * 1024 * 1024 * 1024, 4096, 16, true);
    auto processes = sim.load_processes();
    for (const auto& proc : processes) {
        std::cout << "Process ID: " << proc.id << ", Name: " << proc.name << ", Size: " << proc.size_bytes / (1024ULL * 1024 * 1024) << "GB, Type: " << proc.type << ", Priority: " << proc.priority << std::endl;
    }
    return 0;
}