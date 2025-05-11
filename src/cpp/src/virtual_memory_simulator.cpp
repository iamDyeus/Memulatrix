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
#include "../include/virtual_memory_simulator.h"

#pragma comment(lib, "Ws2_32.lib")

class SocketHandler {
public:
    SocketHandler() {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            throw std::runtime_error("WSAStartup failed: " + std::to_string(WSAGetLastError()));
        }

        server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (server_socket == INVALID_SOCKET) {
            WSACleanup();
            throw std::runtime_error("Failed to create socket: " + std::to_string(WSAGetLastError()));
        }

        int opt = 1;
        if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
            closesocket(server_socket);
            WSACleanup();
            throw std::runtime_error("Setsockopt failed: " + std::to_string(WSAGetLastError()));
        }

        sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
        server_addr.sin_port = htons(12345);

        if (bind(server_socket, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
            closesocket(server_socket);
            WSACleanup();
            throw std::runtime_error("Bind failed: " + std::to_string(WSAGetLastError()));
        }

        if (listen(server_socket, 1) == SOCKET_ERROR) {
            closesocket(server_socket);
            WSACleanup();
            throw std::runtime_error("Listen failed: " + std::to_string(WSAGetLastError()));
        }

        std::ofstream debug("debug.txt", std::ios::app);
        debug << "TCP server initialized on 127.0.0.1:12345\n";
        debug.close();

        std::cout << "TCP server listening on 127.0.0.1:12345" << std::endl;
    }

    ~SocketHandler() {
        if (client_socket != INVALID_SOCKET) {
            closesocket(client_socket);
        }
        if (server_socket != INVALID_SOCKET) {
            closesocket(server_socket);
        }
        WSACleanup();
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Closed TCP sockets\n";
        debug.close();
        std::cout << "Closed TCP sockets" << std::endl;
    }

    bool accept_connection() {
        std::cout << "Waiting for client connection..." << std::endl;
        client_socket = accept(server_socket, NULL, NULL);
        if (client_socket == INVALID_SOCKET) {
            std::cerr << "Accept failed: " << WSAGetLastError() << std::endl;
            std::ofstream debug("debug.txt", std::ios::app);
            debug << "Accept failed: " << WSAGetLastError() << "\n";
            debug.close();
            return false;
        }
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Client connected\n";
        debug.close();
        std::cout << "Client connected" << std::endl;
        return true;
    }

    std::string read() {
        char buffer[1024 * 1024];
        int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received == SOCKET_ERROR) {
            int error = WSAGetLastError();
            std::ofstream debug("debug.txt", std::ios::app);
            debug << "Read failed: " << error << "\n";
            debug.close();
            if (error == WSAECONNRESET || error == WSAECONNABORTED) {
                std::cout << "Client disconnected, error: " << error << ". Waiting for new connection..." << std::endl;
                closesocket(client_socket);
                client_socket = INVALID_SOCKET;
                return "";
            }
            std::cerr << "Read failed: " << error << std::endl;
            return "";
        }
        if (bytes_received == 0) {
            std::ofstream debug("debug.txt", std::ios::app);
            debug << "Client closed connection\n";
            debug.close();
            std::cout << "Client closed connection. Waiting for new connection..." << std::endl;
            closesocket(client_socket);
            client_socket = INVALID_SOCKET;
            return "";
        }
        buffer[bytes_received] = '\0';
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Received: " << std::string(buffer).substr(0, 50) << "...\n";
        debug.close();
        std::cout << "Received: " << std::string(buffer).substr(0, 50) << "..." << std::endl;
        return std::string(buffer);
    }

    bool write(const std::string& data) {
        int bytes_sent = send(client_socket, data.c_str(), data.size(), 0);
        if (bytes_sent == SOCKET_ERROR) {
            int error = WSAGetLastError();
            std::ofstream debug("debug.txt", std::ios::app);
            debug << "Write failed: " << error << "\n";
            debug.close();
            if (error == WSAECONNRESET || error == WSAECONNABORTED) {
                std::cout << "Client disconnected during write, error: " << error << ". Waiting for new connection..." << std::endl;
                closesocket(client_socket);
                client_socket = INVALID_SOCKET;
                return false;
            }
            std::cerr << "Write failed: " << error << std::endl;
            return false;
        }
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Sent: " << data.substr(0, 50) << "...\n";
        debug.close();
        std::cout << "Sent: " << data.substr(0, 50) << "..." << std::endl;
        return true;
    }

private:
    SOCKET server_socket = INVALID_SOCKET;
    SOCKET client_socket = INVALID_SOCKET;
};

class TLB {
public:
    TLB(int size) : size_(size) {
        entries_.resize(size, {0, -1});
    }
    bool access(uint64_t virtual_address) {
        std::ofstream debug("debug.txt", std::ios::app);
        for (const auto& entry : entries_) {
            if (entry.first == virtual_address) {
                debug << "TLB: Hit for virtual address 0x" << std::hex << virtual_address << "\n";
                debug.close();
                return true;
            }
        }
        entries_[next_entry_] = {virtual_address, 0};
        debug << "TLB: Miss for virtual address 0x" << std::hex << virtual_address 
              << ", added to entry " << next_entry_ << "\n";
        debug.close();
        next_entry_ = (next_entry_ + 1) % size_;
        return false;
    }
private:
    int size_;
    std::vector<std::pair<uint64_t, int>> entries_;
    int next_entry_ = 0;
};

VirtualMemorySimulator::VirtualMemorySimulator(SocketHandler* handler) : socket_handler(handler), total_hits(0), total_misses(0), total_faults(0) {
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
              << "TLBSize=" << tlb_size << ", "
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

void VirtualMemorySimulator::simulate() {
    std::ofstream debug("debug.txt", std::ios::app);
    
    tlb_hits.clear();
    tlb_misses.clear();
    tlb_hit_rate.clear();
    page_faults.clear();
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;
    page_tables.clear();

    debug << "Starting simulation\n";

    // Parse virtual address size
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

    // Parse ROM size
    uint64_t rom_size_bytes;
    std::stringstream ss(rom_size);
    double rom_gb;
    ss >> rom_gb;
    rom_size_bytes = static_cast<uint64_t>(rom_gb * 1024ULL * 1024 * 1024);

    // Check total process size
    uint64_t total_process_size = 0;
    int active_processes = 0;
    for (const auto& p : processes) {
        if (!p.is_process_stop) {
            total_process_size += p.size_bytes;
            active_processes++;
        }
    }
    uint64_t max_size = ram_size_bytes + (rom_size_bytes * swap_percent / 100);
    if (total_process_size > max_size) {
        debug << "Insufficient space: Total process size (" << total_process_size / (1024ULL * 1024 * 1024)
              << "GB) exceeds RAM (" << ram_size_bytes / (1024ULL * 1024 * 1024)
              << "GB) + Swap (" << (rom_size_bytes * swap_percent / 100) / (1024ULL * 1024 * 1024) << "GB)\n";
        debug.close();
        std::cout << "Insufficient space: Total process size (" << total_process_size / (1024ULL * 1024 * 1024)
                  << "GB) exceeds RAM (" << ram_size_bytes / (1024ULL * 1024 * 1024)
                  << "GB) + Swap (" << (rom_size_bytes * swap_percent / 100) / (1024ULL * 1024 * 1024) << "GB)\n";
        return;
    }

    // Determine block size
    uint64_t block_size_bytes;
    if (ram_size_bytes < 16ULL * 1024 * 1024 * 1024) {
        block_size_bytes = 1ULL * 1024 * 1024;
    } else if (ram_size_bytes < 32ULL * 1024 * 1024 * 1024) {
        block_size_bytes = 4ULL * 1024 * 1024;
    } else {
        block_size_bytes = 16ULL * 1024 * 1024;
    }

    // Calculate frames and frame percentage
    uint64_t total_frames = ram_size_bytes / page_size_bytes;
    double frame_percent = active_processes >= 2 ? (100.0 / active_processes - 2) : 100.0;
    if (frame_percent < 1.0) frame_percent = 1.0;

    // Initialize available frames
    std::vector<uint64_t> available_frames(total_frames);
    for (uint64_t i = 0; i < total_frames; ++i) {
        available_frames[i] = i;
    }

    // Create page tables
    std::random_device rd;
    std::mt19937 gen(rd());
    uint64_t current_address = 0;
    for (const auto& p : processes) {
        if (p.is_process_stop) continue;
        uint64_t num_pages = (p.size_bytes + page_size_bytes - 1) / page_size_bytes;
        PageTable pt(num_pages, page_size_bytes, entry_size, allocation_type, total_frames, ram_size_bytes, frame_percent, p.id);
        if (!pt.allocate(block_size_bytes, available_frames, gen)) {
            debug << "Allocation failed for process ID=" << p.id << ", Name=" << p.name << "\n";
            std::cout << "Allocation failed for process ID=" << p.id << ", Name=" << p.name << "\n";
            continue;
        }
        page_tables.emplace(p.id, std::make_pair(current_address, pt));
        current_address += pt.size_bytes();

        // Demonstrate lookup for a sample page (e.g., page 1)
        uint64_t sample_page = 1; // Can be changed to any valid page (e.g., 2050 for large processes)
        if (num_pages >= sample_page) {
            lookup(p.id, sample_page);
        }
    }

    // Log page tables for active processes
    debug << "Page tables for active processes:\n";
    for (const auto& p : processes) {
        if (p.is_process_stop) continue;
        auto it = page_tables.find(p.id);
        if (it != page_tables.end()) {
            json pt_json = it->second.second.export_json();
            debug << "Process ID=" << p.id << ", Name=" << p.name << ":\n";
            for (const auto& entry : pt_json) {
                debug << "  Virtual Page=" << entry["virtual_page"].get<uint64_t>()
                      << ", Physical Frame=" << entry["physical_frame"].get<std::string>()
                      << ", In RAM=" << entry["in_ram"].get<bool>() << "\n";
            }
        }
    }

    // Simulate memory access
    TLB tlb(tlb_size);
    int simulation_duration = 100;
    std::uniform_int_distribution<> access_dist(0, 1);
    std::uniform_int_distribution<uint64_t> va_dist(0, va_max);

    for (int t = 0; t < simulation_duration; t++) {
        for (const auto& p : processes) {
            if (p.is_process_stop) continue;
            if (access_dist(gen) == 0) continue;

            uint64_t virtual_address = va_dist(gen) % p.size_bytes;
            if (tlb_enabled) {
                bool hit = tlb.access(virtual_address);
                if (hit) total_hits++;
                else total_misses++;
            }

            auto it = page_tables.find(p.id);
            if (it != page_tables.end()) {
                bool fault = it->second.second.access(virtual_address);
                if (fault) total_faults++;
            }

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
            json pt_entry;
            pt_entry["process_id"] = pt.first;
            pt_entry["base_address"] = pt.second.first;
            pt_entry["table"] = pt.second.second.export_json();
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
    total_hits = 0;
    total_misses = 0;
    total_faults = 0;

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
    if (it != page_tables.end()) {
        it->second.second.lookup(page_number);
    } else {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Process " << process_id << ": Not found for lookup\n";
        debug.close();
        std::cout << "Process " << process_id << ": Not found for lookup\n";
    }
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