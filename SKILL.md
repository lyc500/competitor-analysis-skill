---
name: competitor-analysis
description: 根据自然语言需求搜集竞品页面、筛选公开素材、动态分类并生成可点击放大的 HTML 报告。
---

# 竞品分析 Skill

## 使用入口

执行：

```bash
python3 -m competitor_analysis_skill "<自然语言调研需求>" --output reports/<name>
```

输出 `report.html` 和 `materials.json`。HTML 可直接打开，截图可点击放大；无法验证的页面显示 `needs_manual_capture`，不使用替代图片凑数。

## 执行边界

主流程是：需求解析、竞品规划、公开来源采集、质量筛选、统一素材池、动态分类、报告生成。`catalog.py` 中的内置候选只用于首轮任务的候选输入和离线测试，不能代表在线采集成功。在线结果通过素材中的 `provenance: online` 标识；内置离线结果标记为 `builtin_candidate`。

## 扩展规则

新增来源应实现独立采集器并输出统一素材字段，不修改报告消费接口。分类器根据素材差异选择地区、产品类型、页面结构或设计模式等维度，不把任何单一维度作为固定模板。

