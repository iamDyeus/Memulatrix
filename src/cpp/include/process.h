#ifndef PROCESS_H
#define PROCESS_H

#include <string>

struct Process {
    std::string id;
    std::string name;
    uint64_t size_bytes;
    std::string type;
    bool has_priority;
    bool is_process_stop;
};

#endif // PROCESS_H