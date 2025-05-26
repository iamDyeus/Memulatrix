#include "../include/virtual_memory_simulator.h"

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
