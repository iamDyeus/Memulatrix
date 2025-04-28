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


