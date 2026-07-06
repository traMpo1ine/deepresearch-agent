# TextRank 压缩与引用保护

核心观点：上下文压缩不能只追求短，还要保住可验证证据。

本文可以按这个顺序展开：

1. L1 embedding 粗过滤。
2. L2 TextRank 句子图。
3. L3 citation quote 强制保留。
4. compression_ratio 和 quote preservation 的测试。
5. 过度压缩造成的失败模式。
