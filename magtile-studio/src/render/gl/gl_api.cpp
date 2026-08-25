#include "gl_api.hpp"

#include <cstdio>

namespace magtile::render::glapi {

#define MAGTILE_GL_DEFINE(ret, name, params) ret(*name) params = nullptr;
MAGTILE_GL_FUNCTION_LIST(MAGTILE_GL_DEFINE)
#undef MAGTILE_GL_DEFINE

bool loadFunctions(ProcResolver resolver) {
    bool ok = true;

    // 函数指针类型间的 reinterpret_cast 是所有 GL 加载器的标准做法
#define MAGTILE_GL_LOAD(ret, name, params)                                    \
    name = reinterpret_cast<ret(*) params>(resolver(#name));                  \
    if (name == nullptr) {                                                    \
        std::fprintf(stderr, "[render] 无法解析 OpenGL 入口: %s\n", #name);    \
        ok = false;                                                           \
    }
    MAGTILE_GL_FUNCTION_LIST(MAGTILE_GL_LOAD)
#undef MAGTILE_GL_LOAD

    return ok;
}

}  // namespace magtile::render::glapi
