---
title: "关于AI编程协助模式的思考心得"
date: 2026-06-22
tags: [AI编程, Codex, GPT, Gemini, NotebookLM, Continue, OpenCode]
summary: >-
  多工具协作的AI编程工作流设计：从框架讨论到代码审查的完整闭环
---
 
 

| 阶段      | 工具组合                        | 核心用途                    | 产出               |
| ------- | --------------------------- | ----------------------- | ---------------- |
| 1. 架构构思 | Gemini + GPT                | 方案比较、系统设计、代码骨架、技术路线     | 架构草案、模块划分、接口设计   |
| 2. 认知校验 | NotebookLM                  | 基于资料发现矛盾点、遗漏点、假设风险      | 风险清单、盲点列表、待确认问题  |
| 3. 任务规划 | Codex                       | 拆解开发任务、形成执行路径、像导师一样指导实现 | Todo、开发顺序、关键实现建议 |
| 4. 深度推演 | Continue                    | 结合代码库上下文做技术细化、局部方案咨询    | 具体实现方案、边界条件、重构建议 |
| 5. 闭环执行 | OpenCode → Continue → Codex | 脚本生成、上下文摘录、代码审查、修复迭代    | 可运行代码、审查意见、修复补丁  |

我会建议把第 5 步明确成一个闭环：

**OpenCode：执行与生成**
负责快速生成脚本、批量修改、跑命令、提取上下文。

**Continue：上下文理解与技术咨询**
负责读项目、解释代码关系、判断方案是否合理。

**Codex：任务收敛与代码审查**
负责把问题拆成可执行任务，并做最终 review、测试建议和修复指令。

可以压缩成一句方法论：

> **Gemini/GPT 定方向，NotebookLM 查漏洞，Codex 拆任务，Continue 做深度上下文咨询，OpenCode 执行落地，再用 Continue + Codex 完成审查闭环。**

更工程化一点，可以写成：

> **框架层：Gemini + GPT**
> **校验层：NotebookLM**
> **规划层：Codex**
> **咨询层：Continue**
> **执行层：OpenCode**
> **闭环层：OpenCode → Continue → Codex**
 


## 完整工作流示例

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI编程协作工作流（完整版）                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 需求分析阶段                                                     │
│     └─ Gemini + GPT：讨论方案，产出框架思路                           │
│                                                                     │
│  2. 方案验证阶段                                                     │
│     └─ NotebookLM：矛盾点分析，盲点检测                              │
│                                                                     │
│  3. 任务拆解阶段                                                     │
│     └─ Codex：任务分解，输出MD指导文档                               │
│                                                                     │
│  4. 脚本生成阶段                                                     │
│     ├─ OpenCode + MiMo-V2.5：编写具体脚本                           │
│     ├─ Continue：上下文摘录与适配                                    │
│     └─ Codex：代码审查与优化建议                                     │
│                                                                     │
│  5. 执行开发阶段                                                     │
│     └─ Continue + LLM：基于MD指导，进行细粒度咨询和编码               │
│                                                                     │
│  6. 质量保证阶段                                                     │
│     └─ NotebookLM：代码审查，安全漏洞检测                            │
│     └─ Codex：自动化测试，迭代修复                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
Codex负责将宏观的“框架骨架”转化为可执行的“原子化任务流”，并以资深工程师的视角提供设计模式选择与技术选型建议。

NotebookLM基于 RAG（检索增强生成）的严格闭源知识库模式。通过输入架构文档与业务需求，利用其强行对齐源文本的能力，发现设计逻辑中的“幻觉”、前后矛盾或未覆盖的边缘case（Edge Cases）。

### 工具协作矩阵

| 阶段 | 主要工具 | 辅助工具 | 输出物 |
|------|----------|----------|--------|
| 需求分析 | Gemini + GPT | - | 框架文档、架构图 |
| 方案验证 | NotebookLM | - | 矛盾点清单、盲点报告 |
| 任务拆解 | Codex | NotebookLM | MD任务文档 |
| 脚本生成 | OpenCode | Continue | 初版代码 |
| 上下文适配 | Continue | - | 适配后代码 |
| 代码审查 | Codex | Continue | 审查意见 |
| 开发执行 | Continue | OpenCode | 完整代码 |
| 质量保证 | Codex + NotebookLM | - | 测试报告、最终代码 |

---

## 核心协作思路

### 1. Gemini + GPT：框架思路与代码骨架

**做什么：** 讨论方案，给出框架思路和代码骨架

**怎么用：**
- 用Gemini/GPT进行需求分析和技术选型讨论
- 让它们输出项目的整体架构文档
- 生成代码骨架（核心模块结构、接口定义、数据模型）

**输出物：** 架构文档、模块划分、伪代码/骨架代码

---

### 2. NotebookLM：矛盾点分析与盲点检测

**做什么：** 提供矛盾点分析和盲点分析，整合系统组织框架和线索

**怎么用：**
- 将Gemini/GPT产出的架构文档和骨架代码上传
- 提问："分析这套方案的潜在矛盾点和设计盲点"
- 要求整合所有分析结果，给出改进建议

**输出物：** 矛盾点清单、盲点报告、改进建议

---

### 3. Codex：任务拆解与导师指导

**做什么：** 作为小白的导师，指导手动操作命令和任务拆解、细化

**怎么用：**
- 给Codex整体需求和架构，让它拆解成可执行的任务
- 每个任务包含：具体步骤、验收标准、验证命令
- 让它输出步骤式的操作指导（适合新手跟着做）

**输出物：** 任务拆解文档（MD格式）、操作步骤指导

---

### 4. Continue：深度咨询与技术细化

**做什么：** 利用Continue中的LLM，拆解更细更多技术问题和思路

**怎么用：**
- 把Codex的指导内容保存为MD文件
- 在Continue中用`@file`引用该MD，进行更细粒度的咨询
- 针对具体技术问题深入讨论（API选型、算法实现、异常处理等）

**输出物：** 技术方案细节、具体实现思路

---

### 5. OpenCode + Continue + Codex：脚本生成与审查闭环

**做什么：** 根据Continue的反馈，用OpenCode写脚本，Continue摘录适配，Codex审查

**流程：**

```
┌─────────────────────────────────────────────────────────────────┐
│                  脚本生成与审查闭环                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Continue反馈意见                                                │
│       ↓                                                         │
│  OpenCode + MiMo-V2.5-Free                                      │
│  → 根据反馈编写具体脚本                                          │
│       ↓                                                         │
│  Continue                                                        │
│  → 按照上下文环境，摘录合适的脚本内容                             │
│  → 调整为项目统一风格                                            │
│       ↓                                                         │
│  Codex                                                           │
│  → 审查是否合理                                                  │
│  → 是否需要优化思路                                              │
│       ↓                                                         │
│  [满意] → 输出最终代码                                           │
│  [不满意] → 回到OpenCode继续修改                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**具体操作：**

```bash
# Step 1: OpenCode生成脚本
opencode
> 根据以下需求编写Python脚本：[粘贴需求]

# Step 2: Continue上下文摘录
@file: src/xxx.py  # 引用项目现有代码
> OpenCode生成的代码中，xxx部分与项目现有风格不一致，请帮我适配

# Step 3: Codex审查
> 请审查这段代码：[粘贴适配后的代码]
> 检查：逻辑是否正确？是否有优化空间？是否符合最佳实践？
```

---

针对这两个具体工程点的落地实施，以下是基于当前主流开源工具链与 API 架构的工程实现方案：

---

## 一、 数据平面的统一：自动化反馈链的工程实现

NotebookLM 目前缺乏开放的 API，因此该链路的自动化需要结合**半自动导出/结构化转换**与 **Continue 的配置文件动态加载**。

### 1. 资产提取与标准化（NotebookLM → Markdown）

1. **导出：** 在 NotebookLM 的右侧笔记栏中，将"盲点分析"或"矛盾点提示"集成导出为单份 Google Docs，然后下载为本地 Markdown 文件（假设命名为 `notebook_blindspots.md`）。
2. **结构化清洗：** 使用一个简单的 Python 本地脚本，将非结构化的文本转化为符合大模型上下文格式的结构化 YAML/Markdown：

```python
# clean_assets.py
import re

def format_blindspots(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取核心矛盾点与盲点，转化为大模型易读的规约格式
    formatted_text = f"## 业务盲点与架构对抗规约\n\n> 注意：以下为 NotebookLM 审计出的业务盲点与逻辑矛盾，开发时必须严格绕开：\n\n{content}"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_text)

format_blindspots("notebook_blindspots.md", "system_rules.md")

```

### 2. 注入 Continue 上下文

Continue 支持通过 `.continuerc.json` 或 `config.json` 配置 `systemMessage`，也可以利用其自定义的 `ContextProviders` 动态读取文件。

**方案 A：动态 System Prompt 注入**
修改项目根目录下的 `.continue/config.json`，将清洗后的 `system_rules.md` 作为系统级约束常驻：

```json
{
  "models": [ ... ],
  "systemMessage": "你是一个严谨的资深开发导师。在编写和审计代码时，必须严格遵守项目根目录下 'system_rules.md' 中定义的业务盲点规约，防止引入相同的逻辑漏洞。"
}

```

**方案 B：利用 Continue 的 `@file` 机制（推荐）**
无需频繁修改配置文件，直接在 Continue 的聊天输入框中使用 **`@system_rules.md`**。这样可以将 NotebookLM 的盲点资产作为上下文切片，直接喂给当前对话。

---

## 二、 上下文裁剪：基于 AST 的类/函数级精简

直接将整个大文件或无关的相邻依赖塞给 Continue 会导致 Token 爆炸并引入噪声。利用 AST（抽象语法树）进行精确裁剪，可以做到"只提供声明、调用链和目标函数实体"。

### 1. 技术选型：Tree-sitter / Python `ast` 库

以 Python 项目为例，利用内置的 `ast` 库（如果是 TypeScript/Go，推荐使用 `tree-sitter` CLI），编写一个上下文剪裁脚本 `ast_clipper.py`。

### 2. 裁剪脚本的核心实现逻辑

该脚本的作用是：输入一个源码文件，**保留类结构、函数签名、Docstring，但剔除其他无关函数的具体实现体**，只完整保留你当前正在修改的那个函数的函数体。

```python
import ast

class ASTTransformer(ast.NodeTransformer):
    def __init__(self, target_function_name):
        self.target_function = target_function_name

    def visit_FunctionDef(self, node):
        # 如果是目标修改函数，保留完整体
        if node.name == self.target_function:
            return node
        
        # 如果是其他函数，只保留签名和文档注释，清空内部具体实现
        docstring = ast.get_docstring(node)
        if docstring:
            node.body = [ast.Expr(value=ast.Constant(value=docstring))]
        else:
            node.body = [ast.Pass()]  # 用 pass 替代具体实现
        return node

def clip_file_context(file_path, target_func):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    tree = ast.parse(source)
    transformer = ASTTransformer(target_func)
    modified_tree = transformer.visit(tree)
    ast.fix_missing_locations(modified_tree)
    
    return ast.unparse(modified_tree)

# 示例：只保留 my_service.py 中 process_data 的具体代码，其余函数只留骨架
clipped_code = clip_file_context("my_service.py", "process_data")
print(clipped_code)

```

### 3. 与 OpenCode → Continue 链条集成

1. **OpenCode 摘录阶段：** 当 OpenCode 在上游分析出需要修改 `my_service.py` 中的 `process_data` 函数时，触发该 Python 裁剪脚本。
2. **生成临时快照：** 脚本输出一份裁剪后的精简上下文，保存为 `.context_cache/my_service_clipped.py`。这份文件的 Token 消耗通常只有原文件的 $10\% \sim 20\%$。
3. **Continue 承接：** 在 IDE 中，通过 Continue 键入：
> `@my_service_clipped.py 请基于此骨架和被保留的 process_data 函数，重构其内部的并发逻辑。`



通过这种方式，Continue 既获得了完整的全局类/函数依赖关系（不会报未定义错误），又免受几千行不相关业务代码的 Token 干扰，精炼度大幅提升。

---

## 三、 数学分析思维的迁移价值

因为**数学分析**不是只教你算题，而是在训练一种可迁移的思维方式：

1. **从定义出发**
   不能凭感觉，要先问：这个概念到底是什么意思？条件是什么？结论是什么？

2. **一步一步推导**
   你必须说明每一步为什么成立，不能跳步、不能"差不多"。这会训练严密性。

3. **拆解复杂问题**
   一个大问题通常要分成几个小命题、引理、条件判断。这种拆解能力以后做研究、写代码、做商业判断都能用。

4. **识别假设和边界**
   数学分析里很多结论只在特定条件下成立，比如连续、可导、收敛、紧致。久了你会习惯问：这个判断依赖什么前提？有没有反例？

5. **培养抽象能力**
   你学到的不是某道题的答案，而是如何把现实问题抽象成结构，再用逻辑处理。

所以这句话的意思是：在伯克利那门数学分析课里，他/她不只是学会了数学，而是学会了**如何严谨地理解、拆解、推导和解决问题**。这种能力后来可以迁移到任何领域，所以他说"真正学会怎么学东西是在伯克利"。

## 总结

这套工作流的核心逻辑：

1. **先宏观后微观**：Gemini/GPT给框架 → Codex拆任务 → OpenCode写代码
2. **多角度验证**：NotebookLM查矛盾 → Codex审代码 → Continue做适配
3. **形成闭环**：每个环节的输出是下一个环节的输入，不满意就迭代
