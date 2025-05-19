#ifndef MEMORY_ALLOCATION_H
#define MEMORY_ALLOCATION_H

#include <vector>
#include <random>
#include <unordered_map>
#include <string>

class PageTable;

class MemoryAllocationStrategy {
public:
    virtual ~MemoryAllocationStrategy() = default;
    virtual bool allocate(PageTable& page_table, uint64_t num_pages,
                         std::vector<uint64_t>& available_frames,
                         std::vector<uint64_t>& available_swap_frames,
                         std::mt19937& gen,
                         std::vector<uint64_t>& allocated_frames,
                         std::vector<uint64_t>& allocated_swap_frames) = 0;
    virtual std::string get_name() const = 0;
};

class FirstFitStrategy : public MemoryAllocationStrategy {
public:
    bool allocate(PageTable& page_table, uint64_t num_pages,
                  std::vector<uint64_t>& available_frames,
                  std::vector<uint64_t>& available_swap_frames,
                  std::mt19937& gen,
                  std::vector<uint64_t>& allocated_frames,
                  std::vector<uint64_t>& allocated_swap_frames) override;
    std::string get_name() const override { return "First Fit"; }
};

class NextFitStrategy : public MemoryAllocationStrategy {
public:
    NextFitStrategy();
    bool allocate(PageTable& page_table, uint64_t num_pages,
                  std::vector<uint64_t>& available_frames,
                  std::vector<uint64_t>& available_swap_frames,
                  std::mt19937& gen,
                  std::vector<uint64_t>& allocated_frames,
                  std::vector<uint64_t>& allocated_swap_frames) override;
    std::string get_name() const override { return "Next Fit"; }
private:
    static uint64_t last_search_frame_;
};

class BestFitStrategy : public MemoryAllocationStrategy {
public:
    bool allocate(PageTable& page_table, uint64_t num_pages,
                  std::vector<uint64_t>& available_frames,
                  std::vector<uint64_t>& available_swap_frames,
                  std::mt19937& gen,
                  std::vector<uint64_t>& allocated_frames,
                  std::vector<uint64_t>& allocated_swap_frames) override;
    std::string get_name() const override { return "Best Fit"; }
};

class WorstFitStrategy : public MemoryAllocationStrategy {
public:
    bool allocate(PageTable& page_table, uint64_t num_pages,
                  std::vector<uint64_t>& available_frames,
                  std::vector<uint64_t>& available_swap_frames,
                  std::mt19937& gen,
                  std::vector<uint64_t>& allocated_frames,
                  std::vector<uint64_t>& allocated_swap_frames) override;
    std::string get_name() const override { return "Worst Fit"; }
};

class QuickFitStrategy : public MemoryAllocationStrategy {
public:
    QuickFitStrategy();
    bool allocate(PageTable& page_table, uint64_t num_pages,
                  std::vector<uint64_t>& available_frames,
                  std::vector<uint64_t>& available_swap_frames,
                  std::mt19937& gen,
                  std::vector<uint64_t>& allocated_frames,
                  std::vector<uint64_t>& allocated_swap_frames) override;
    std::string get_name() const override { return "Quick Fit"; }
private:
    std::unordered_map<uint64_t, std::vector<std::vector<uint64_t>>> size_lists_; // Size -> List of blocks
    std::vector<uint64_t> predefined_sizes_; // e.g., 1, 4, 16 pages
    void initialize_size_lists(std::vector<uint64_t>& available_frames);
};

#endif // MEMORY_ALLOCATION_H