#include <cstdint>
#include <iostream>
#include <limits>
#include <string>

int main(int argc, char** argv) {
    const std::int64_t logs[] = {0, 0, 2977044471LL, 4718503850LL, 5954088943LL};
    std::int64_t result = 0;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string text(argv[i]);
            if (text.size() != 1 || text[0] < '1' || text[0] > '4') return 2;
            const int level = text[0] - '0';
            if (result > std::numeric_limits<std::int64_t>::max() - logs[level]) return 3;
            result += logs[level];
        }
        std::cout << result << '\n';
        return 0;
    } catch (...) { return 4; }
}
