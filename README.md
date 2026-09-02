# 竞品分析 Skill V0.1

最小可运行链路：自然语言需求 → 竞品清单 → 公开来源采集 → 质量筛选 → 统一素材池 → 动态分类 → HTML 报告。

`SKILL.md` 是可作为 Skill 使用的入口说明。`catalog.py` 只提供候选输入，`collector.py` 才负责公开来源采集；两者保持解耦。

## 运行

```bash
python3 -m competitor_analysis_skill "帮我搜集一下海内外热门产品的搜索结果页。" --output reports/search-results
```

报告生成在 `reports/search-results/report.html`，素材池在 `reports/search-results/materials.json`。公开页面无法提供可靠图片时，素材会保留 `needs_manual_capture` 状态，不用低质量图片替代。

请以 `materials.json` 的 `provenance` 区分结果：`online` 是真实在线采集，`builtin_candidate` 是内置候选的离线结构验证。

离线结构验证：

```bash
python3 -m competitor_analysis_skill "帮我搜集一下海内外热门产品的搜索结果页。" --offline --output reports/offline
```
