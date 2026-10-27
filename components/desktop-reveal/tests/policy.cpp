#include "../source/src/render/SagaRevealPolicy.hpp"
#include <cassert>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    using namespace SagaReveal;
    using namespace std::chrono;
    for (int ms = 350; ms <= 700; ++ms)
        assert(SagaReveal::duration(std::to_string(ms)) == ms);
    for (const auto invalid : {"", "0", "349", "701", "99999999999999999", "550junk", "550\n\n", "-550", " 550", "+550"})
        assert(!SagaReveal::duration(invalid));
    assert(SagaReveal::duration("550\n") == 550);
    std::cout << "PASS strict duration parsing and bounds\n";

    for (int ms : {350, 550, 700}) {
        Timeline timeline;
        const auto first = Timeline::Clock::time_point{} + hours(100);
        assert(timeline.alpha(first, ms) == 1.F);
        float previous = 1.F;
        for (int elapsed = 0; elapsed <= ms; ++elapsed) {
            const auto a = timeline.alpha(first + milliseconds(elapsed), ms);
            assert(a >= 0.F && a <= previous);
            previous = a;
        }
        assert(previous == 0.F);
        assert(timeline.alpha(first + hours(10), ms) == 0.F);
        Timeline repeated;
        assert(repeated.alpha(first + hours(20), ms) == 1.F);
    }
    assert(std::abs(coverAlpha(275, 550) - .125F) < 0.000001F);
    std::cout << "PASS opaque first frame, monotonic OutCubic, expiry, repeated timeline\n";

    char temp[] = ".local/tmp/saga-reveal-policy-XXXXXX";
    const char* dir = mkdtemp(temp);
    assert(dir);
    const auto flag = std::filesystem::path(dir) / "flag";
    assert(!readDuration(flag.c_str(), getuid()));
    { std::ofstream out(flag); out << "550\n"; }
    chmod(flag.c_str(), 0600);
    assert(readDuration(flag.c_str(), getuid()) == 550);
    assert(!readDuration(flag.c_str(), getuid() + 1));
    chmod(flag.c_str(), 0666);
    assert(!readDuration(flag.c_str(), getuid()));
    chmod(flag.c_str(), 0600);
    const auto link = std::filesystem::path(dir) / "link";
    std::filesystem::create_symlink(flag, link);
    assert(!readDuration(link.c_str(), getuid()));
    const auto fifo = std::filesystem::path(dir) / "fifo";
    assert(mkfifo(fifo.c_str(), 0600) == 0);
    assert(!readDuration(fifo.c_str(), getuid()));
    assert(!readDuration(dir, getuid()));
    { std::ofstream out(flag); out << std::string(4096, '5'); }
    assert(!readDuration(flag.c_str(), getuid()));
    std::filesystem::remove(flag); // The actual kill-switch operation.
    assert(!readDuration(flag.c_str(), getuid()));
    std::filesystem::remove_all(dir);
    std::cout << "PASS kill switch, owner/mode checks, symlink/FIFO/directory/oversize rejection\n";
}
