#ifndef PROCESS_H
#define PROCESS_H

#include <string>
#include <cstdint>

struct Process
{
    std::string id;
    std::string name;
    int size_gb;
    std::string type;
    bool has_priority;
    bool is_process_stop;
    uint64_t virtual_address;
};

#endif // PROCESS_H