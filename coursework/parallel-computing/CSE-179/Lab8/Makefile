NVCC      = nvcc
NVCCFLAGS = -O2 -arch=sm_70
TARGET    = lab8_GPU
SRC       = lab8_GPU.cu

.PHONY: all clean run perf

# Default target: compile
all: $(TARGET)

# Compile
$(TARGET): $(SRC)
	$(NVCC) $(NVCCFLAGS) -o $@ $<

# Quick smoke test: 6x4 grid, 2 rounds, debug output enabled
run: $(TARGET)
	./$(TARGET) 6 4 2 -d

# Performance benchmarks — results saved to .txt files and summarised on stdout
perf: $(TARGET)
	@echo "--- Running Performance Benchmarks ---"
	@./$(TARGET) 64   64   100 > perf_64x64.txt   2>&1
	@./$(TARGET) 512  512  100 > perf_512x512.txt  2>&1
	@./$(TARGET) 2048 2048 100 > perf_2048x2048.txt 2>&1
	@echo "--- Performance Results ---"
	@grep "^Performance:" perf_64x64.txt perf_512x512.txt perf_2048x2048.txt \
	  | sed 's/^perf_\([^:]*\)\.txt:/[\1] /'

# Remove compiled binary and perf output files
clean:
	rm -f $(TARGET) perf_*.txt