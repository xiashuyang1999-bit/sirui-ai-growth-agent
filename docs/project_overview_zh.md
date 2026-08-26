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
- 读取审计报告，自动生成保留 URL、证据和优先级的技术 SEO 待办清单。
- 为每个页面生成搜索意图、目标买家、关键词主题和 Metadata 优化方向。
- 对没有可靠数据的搜索量、竞争难度和当前排名统一标记为 `Needs verification`，不虚构数据。
- Developer Agent 将 SEO 任务转换成实施步骤、必要输入、验收标准、风险等级和回滚方案。
- 所有开发任务默认只允许在本地或 Staging/Preview 环境验证，生产权限保持关闭。
- Content Agent 为每个重点页面生成页面目标、关键词分配、内容结构、资料清单和 CTA 草案。
- 内容中的产品参数、认证、价格、MOQ、产能、交期和定制能力必须由负责人核实后才能发布。

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

Website Audit Agent 完成检查后，SEO Agent v0.1 可以继续读取审计 JSON，把问题转成技术任务，并为 Homepage、Products、Product Detail、Factory、OEM/ODM 和 Inquiry 页面生成独立的关键词主题与页面优化计划。Developer Agent v0.1 再把技术任务转成网站人员可执行和验收的交付包，Content Agent v0.1 为相同页面生成基于证据的英文内容 Brief。关键词目前是待验证的规划种子，不代表真实搜索量或当前排名。

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

生成 SEO 计划：

```bash
python3 -m workflow.main seo-plan reports/sirui_demo_audit.json \
  --output reports/sirui_demo_seo_plan.json
```

演示 SEO 计划时重点展示：

- `technical_backlog`：从审计证据转化而来的 P1/P2/P3 任务。
- `page_plans`：不同页面的搜索意图、买家对象、关键词主题和 Metadata 建议。
- `guardrails`：需要人工验证的数据和上线前审批规则。

生成开发交付包：

```bash
python3 -m workflow.main dev-plan reports/sirui_demo_seo_plan.json \
  --output reports/sirui_demo_developer_plan.json
```

开发交付包重点展示：

- `implementation_tasks`：实施步骤、必要输入、验收标准、风险和回滚方案。
- `release_policy`：默认 Staging 验证，生产权限关闭。
- `global_definition_of_done`：上线审批前必须共同满足的完成标准。

生成内容计划：

```bash
python3 -m workflow.main content-plan reports/sirui_demo_seo_plan.json \
  --output reports/sirui_demo_content_plan.json
```

内容计划重点展示：

- `content_briefs`：每个页面的目标、买家、关键词、章节、资料需求和 CTA 草案。
- `required_verified_inputs`：写作和发布前必须核实的事实及素材。
- `publication_gate`：生产发布权限关闭并要求业务、SEO 和网站负责人审批。

## 一键生成完整增长工作包

从已有审计报告生成 SEO、开发、内容和指标总清单：

```bash
python3 -m workflow.main growth-plan reports/sirui_official_audit_v0_4.json \
  --output-dir reports/sirui_growth_package_v0_1
```

工作包包含：

- `manifest.json`：版本、总体结果、审批状态、下一步和增长指标定义。
- `seo_plan.json`：技术 SEO 任务与页面计划。
- `developer_plan.json`：开发步骤、风险、验收和回滚。
- `content_plan.json`：页面内容 Brief、资料要求和发布门槛。

指标框架覆盖网站访问、自然搜索点击、询盘、有效询盘、样品、报价和订单。尚未连接 GA4、Google Search Console、表单后台或 CRM 时，当前数据统一为 `Needs verification`。

## 询盘资格判断

复制空白模板并填写买家真实提供的信息：

```bash
mkdir -p data/inquiries
cp data/inquiry_template.json data/inquiries/new_inquiry.json
python3 -m workflow.main qualify-inquiry data/inquiries/new_inquiry.json
```

Inquiry Qualification Agent v0.1 会输出：

- A/B/C 分数、证据、状态和下一步动作。
- 缺失的公司身份、产品规格与报价资料。
- 最多 5 个英文澄清问题。
- 报价准备清单。
- 需要销售负责人审批的英文回复草稿。

没有明确完成公司核实时，询盘最高只能评为 B 级。真实询盘输入和输出目录被 Git 忽略，系统不会自动发送回复、修改 CRM 或出具报价。

## 销售 Pipeline 周报

复制 Pipeline 模板，填写周期和已确认的销售记录：

```bash
mkdir -p data/pipeline
cp data/pipeline_template.json data/pipeline/weekly_pipeline.json
python3 -m workflow.main pipeline-report data/pipeline/weekly_pipeline.json
```

Sales Pipeline Report Agent v0.1 会汇总：

- 新线索或询盘与 A/B/C 数量。
- 已起草和已发送的开发信、客户回复、有效询盘、样品、报价和订单。
- 当前销售阶段、A/B 优先队列、阻塞事项、负责人和下一步动作。
- 缺失的记录 ID、等级和其他数据质量问题。

系统只统计明确设置为 `true` 的里程碑。即使记录处于 `quotation` 阶段，只要 `quotation_issued` 不是 `true`，就不会计入已发报价。真实 Pipeline 输入和报告目录被 Git 忽略，系统不会修改源记录或 CRM。

## 销售跟进计划

复制跟进模板并填写已审批的 A/B 等级、当前阶段、起始日期、公司、联系人、市场和产品：

```bash
mkdir -p data/followups
cp data/followup_template.json data/followups/lead_001.json
python3 -m workflow.main followup-plan data/followups/lead_001.json
```

Follow-up Agent v0.1 会为合格的 A/B 记录生成：

- 第 3 天：确认产品类别或当前阶段需要补充的信息。
- 第 7 天：确认 OEM 或 Private Label 需求。
- 第 14 天：询问工厂、质量、目录或样品资料是否有帮助。
- 第 21 天：询问下一采购窗口。
- 最终一次：礼貌结束跟进。

每封邮件少于 120 个英文单词，并保持 `sent=false`。只有 `fit_observation_verified=true` 时才会使用公司观察进行个性化。C 级或等级未核实的记录不会生成主动跟进序列。客户回复、退订或机会关闭时必须停止序列。

## 流量与成交转化报告

复制标准化指标模板，填写来自已授权 GA4、Google Search Console、网站表单和销售 Pipeline 导出的数据：

```bash
mkdir -p data/analytics
cp data/analytics_template.json data/analytics/monthly_metrics.json
python3 -m workflow.main analytics-report data/analytics/monthly_metrics.json
```

Analytics & Conversion Report Agent v0.1 会计算：

- 网站参与率与询盘率。
- Google 搜索点击率。
- 网站询盘到有效询盘的转化率。
- 有效询盘到样品、报价和订单的推进率。
- 数据异常、漏斗中断位置和基于证据的下一步建议。

缺失指标必须保留为 `null`，报告中会显示为 `Needs verification`，不会自动当成 0。完全空白的数据集显示为 `insufficient_data`。只有销售数据明确属于网站来源时，才能使用 `website_only` 计算网站询盘到有效询盘的转化率。本版本只读取本地标准化数据，不登录或修改任何外部账户。
