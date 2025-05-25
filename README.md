# Memulatrix
Virtual Memory Simulator for educational purposes, built with C++ and Python.

![image](https://github.com/user-attachments/assets/7fbccc8c-8262-4e11-be8e-b35b4d3bf632)
![image](https://github.com/user-attachments/assets/a04b9f59-9654-4394-9fde-f0ac333c812b)



> [!IMPORTANT]  
We are currently working on the project. Please check back later for updates and better documentation.

## Proposed Project Structure
The project is organized into the following directories:
```
Memulatrix/
│── docs/                      # Documentation (README, architecture diagrams, API docs)
│── src/                       # Source code
│   ├── cpp/                   # C++ core simulation
│   │   ├── include/           # Header files (.h)
│   │   ├── src/               # C++ source files (.cpp)
│   │   ├── tests/             # Unit tests for C++ modules
│   │   ├── CMakeLists.txt     # CMake configuration for C++ build system
│   ├── python/                # Python UI & visualization
│   │   ├── ui/                # Tkinter UI components
│   │   ├── visualization/     # Matplotlib-based visualizations
│   │   ├── bridge/            # C++-Python communication layer
│   │   ├── main.py            # Entry point for the UI
│   │   ├── requirements.txt   # Python dependencies
│── build/                     # Compiled binaries & intermediate build files
│── tests/                     # End-to-end tests & integration tests
│── examples/                  # Sample test cases for simulation
│── logs/                      # Runtime logs, memory usage stats
│── Makefile                   # Alternative to CMake for build automation
│── .gitignore                 # Ignore compiled files, logs, etc.
│── README.md                  # Project overview
```
## Installation
### Prerequisites
- C++ compiler (g++) - version 14
- Python 3.8 or higher

### Build CPP Core

1. Create the `bin` folder in the root directory:
   ```bash
   mkdir bin
   ```
   you'll get something like `Memulatrix/bin`
2. Navigate to the `src/cpp` directory:
   ```bash
   cd src/cpp
   ```
   you'll be in something like `Memulatrix/src/cpp`
3. Run the build command:
    ```bash
    g++ -std=c++14 -Iinclude -DCPPHTTPLIB_NO_UNIX_SOCKETS src/virtual_memory_simulator.cpp src/page_table.cpp src/socket_handler.cpp -o D:\projects\Memulatrix\bin\virtual_memory_simulator.exe -lWs2_32
    ```
    Manually verify that the `virtual_memory_simulator.exe` file is created in the `bin` directory.
4. Run the Python UI from the root directory:
   ```bash
   python src/python/main.py
   ```
