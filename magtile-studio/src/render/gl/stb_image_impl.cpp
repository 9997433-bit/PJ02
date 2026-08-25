// =============================================================
// MagTile Studio - stb_image 实现单元
//
// 只编译 PNG 解码路径 (模型库卡片缩略图 data/thumbnails/*.png)。
// stb_image 为公有领域单头库, 实现宏必须且只能在一个 TU 中展开。
// =============================================================

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_NO_LINEAR
#define STBI_NO_HDR

#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsign-conversion"
#pragma GCC diagnostic ignored "-Wcast-qual"
#pragma GCC diagnostic ignored "-Wunused-parameter"
#endif

#include <stb/stb_image.h>

#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic pop
#endif
