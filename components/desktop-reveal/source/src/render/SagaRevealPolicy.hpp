#pragma once

#include <algorithm>
#include <charconv>
#include <chrono>
#include <optional>
#include <string_view>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

// Pure visual policy; it has no authority to authenticate or release a lock.
namespace SagaReveal {
    inline std::optional<int> duration(std::string_view text) {
        if (!text.empty() && text.back() == '\n')
            text.remove_suffix(1);
        int ms                  = 0;
        const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), ms);
        if (error != std::errc{} || end != text.data() + text.size() || ms < 350 || ms > 700)
            return std::nullopt;
        return ms;
    }

    inline std::optional<int> readDuration(const char* path, uid_t owner) {
        const int fd = open(path, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
        if (fd < 0)
            return std::nullopt;
        struct stat st       = {};
        char        text[32] = {};
        const bool  valid    = fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_uid == owner && !(st.st_mode & 0022);
        const auto  size     = valid ? read(fd, text, sizeof(text)) : -1;
        close(fd);
        if (size <= 0 || size >= static_cast<ssize_t>(sizeof(text)))
            return std::nullopt;
        return duration(std::string_view(text, size));
    }

    // OutCubic desktop reveal = 1 - (1-t)^3. The safe cover fades oppositely.
    inline float coverAlpha(double elapsedMs, int durationMs) {
        const auto remaining = 1.0 - std::clamp(elapsedMs / durationMs, 0.0, 1.0);
        return static_cast<float>(remaining * remaining * remaining);
    }

    struct Timeline {
        using Clock = std::chrono::steady_clock;
        std::optional<Clock::time_point> firstFrame;

        float                            alpha(Clock::time_point now, int ms) {
            if (!firstFrame)
                firstFrame = now; // Always cover the first desktop frame completely.
            return coverAlpha(std::chrono::duration<double, std::milli>(now - *firstFrame).count(), ms);
        }
    };
}
