# SIRUI AI Website Growth Agent 项目介绍

## 这是什么项目

SIRUI AI Website Growth Agent 是一个面向海外 B2B 获客的独立站智能运营系统。它在网站旁边充当一支可重复工作的“AI 增长团队”：读取经过授权的网站页面，检查品牌定位、SEO 基础、产品发现路径和询盘转化，然后把发现的问题转化为带证据、严重程度、优先级和修改建议的任务。

当前系统只读分析网站，不会自动发布内容、提交表单或修改线上页面。

## 当前功能

- 输入一个网站 URL，分析单个页面。
- 自动发现同域的重要页面，并限制抓取数量。
- 优先审计 Homepage、Products、Product Detail、Factory、OEM/ODM、Private Label 和 Inquiry 页面。
- 根据页面的业务类型使用不同检查标准。
- 检查 Title、Meta Description、Canonical、语言、H1、产品入口、询盘 CTA、表单和直接联系方式。
- 检查 HTTP 状态、robots.txt、XML Sitemap、Sitemap 页面覆盖、JSON-LD Schema 和 Canonical 主域一致性。
- 输出页面级结果和全站问题汇总。
- 为每个问题提供证据、high/medium/low 严重程度、P1/P2/P3 优先级和建议动作。
- 保存 JSON 报告，供运营、SEO、销售和开发团队共同使用。

## 可以如何应用

1. **网站发布验收**：上线后快速检查关键页面是否具备基本 SEO 和 B2B 获客条件。
2. **每周健康检查**：定期生成报告，发现新出现的标题、canonical、导航或询盘路径问题。
3. **SEO 任务清单**：把技术问题直接转化为开发或内容团队的优先任务。
4. **B2B 转化检查**：确认进口商、分销商和 private-label 买家能理解服务并找到询盘入口。
5. **产品内容 QA**：发布产品前检查产品名称、Title、H1、相关产品路径和询盘动作。
6. **团队协作**：让销售、运营、SEO 和开发基于同一份证据报告讨论问题。
7. **服务其他工厂独立站**：更换行业规则后，可以用于其他制造业 B2B 网站的发布验收和持续优化。

## 15 秒介绍

> 这是一个面向海外 B2B 独立站的 AI 增长审计系统。它会根据首页、产品页、工厂页和询盘页的不同职责自动检查 SEO 与转化问题，并输出有证据和优先级的修改清单。

## 1 分钟介绍

> SIRUI AI Website Growth Agent 是我们为海外 B2B 获客建立的独立站智能运营系统。传统网站检查依赖人工逐页查看，而且 SEO、销售和开发往往使用不同标准。这个系统可以自动发现网站的重要页面，根据页面类型检查定位、SEO、产品路径和询盘转化，把每个问题整理成包含页面 URL、证据、严重程度、P1/P2/P3 优先级和修改建议的报告。当前版本只读，不会修改网站，适合用于网站发布验收、每周健康检查、SEO backlog 和跨团队协作。后续还会加入关键词、内容和开发 Agent，形成完整的多 Agent 增长工作流。

## 演示方式

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

生成多页面报告：

```bash
python3 -m workflow.main audit https://www.siruitool.com \
  --max-pages 8 \
  --output reports/sirui_demo_audit.json
```

演示时重点展示报告中的：

- `summary`：页面数量、通过项和问题数量。
- `page_types`：系统识别出的页面业务类型。
- `prioritized_issues`：按 P1/P2/P3 排序的问题、证据和建议。
- `pages`：每一个页面的详细检查结果。
