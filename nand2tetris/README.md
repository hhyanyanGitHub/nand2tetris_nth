# nand2tetris：从 NAND 门到 Pong 的完整计算机系统实现

> **从最底层的逻辑门出发，亲手构建一台能够运行高级语言程序的计算机。**

本仓库是我完整实现 _nand2tetris_（《计算机系统要素》）课程所有核心项目的工程化成果，覆盖：

- 硬件（逻辑门 / CPU / 内存）
- 汇编器
- 虚拟机（VM）
- 高级语言编译器（Jack）
- 端到端系统验证（Pong 游戏）

最终结果：**Jack → VM → Hack 汇编 → Hack 二进制 → CPU Emulator → Pong 正常运行**。

---

## 项目结构

```text
nand2tetris/
├── nand2tetris/
│   ├── asm/        # Hack 汇编器（Project 6）
│   ├── vm/         # VM 翻译器（Project 7–8）
│   ├── jack/       # Jack 编译器（Project 10–11）
│   └── cli.py      # 统一命令行入口
├── tests/          # Jack / VM 测试程序
├── README.md
└── pyproject.toml
```

统一入口：

```bash
python3 -m nand2tetris.cli <asm|vm|jack> <path>
```

---

## 1️⃣ 硬件层（Projects 1–5）

### 从 NAND 门开始

- 所有逻辑门（NOT / AND / OR / XOR）均由 NAND 构造
- 基于逻辑门实现：
  - HalfAdder / FullAdder
  - ALU（算术逻辑单元）

### 时序与状态

- Register（A / D / PC）
- RAM（分层实现）
- Clock 驱动的状态变化

> 在这一阶段，我第一次真正理解了“状态机”的物理含义。

### Hack CPU

- A / C 指令
- ALU 控制位
- Jump 条件逻辑

**成果**：一台可运行汇编程序的 Hack CPU。

---

## 2️⃣ 汇编层：Hack Assembler（Project 6）

### 两遍扫描架构

- Pass 1：构建符号表（label）
- Pass 2：变量分配与指令翻译

### 核心能力

- 符号解析
- 十进制 → 二进制
- dest / comp / jump 精确映射

这是第一次将**文本语言映射为确定的机器状态**。

---

## 3️⃣ 虚拟机层：VM Translator（Projects 7–8）

VM 层是整个系统中**工程含金量极高**的一部分。

### 为什么需要 VM

- 解耦高级语言与硬件
- 提供统一抽象：
  - stack
  - memory segment
  - function call

### Stack Arithmetic

- add / sub / neg
- eq / gt / lt（基于条件跳转）

> 比较指令本质是“条件跳转 + 布尔规范化”。

### Memory Access

| VM Segment | Hack 映射  |
| ---------- | ---------- |
| local      | LCL        |
| argument   | ARG        |
| this       | THIS       |
| that       | THAT       |
| temp       | R5–R12     |
| static     | 文件级符号 |

### 函数调用协议（重点）

完整实现：

- call
- function
- return

包含：

- 返回地址
- 调用者状态保存
- ARG / LCL 重定位

> VM 层已经完整实现了一个“软件级调用栈”。

---

## 4️⃣ 高级语言层：Jack 编译器（Projects 10–11）

这是整个项目的**压轴部分**。

### 4.1 Tokenizer（词法分析）

- keyword / symbol / identifier
- integer / string constant
- comment / whitespace 清洗

### 4.2 Compilation Engine（递归下降编译器）

核心原则：

> **每一个非终结符 → 一个 `compileXxx()`**
> **每一个终结符 → 一个 `eat()`**

这让我真正理解：

> 语法树并不是神秘结构，而是递归函数调用本身。

### 4.3 SymbolTable（符号表）

- class scope
- subroutine scope
- kind → VM segment 映射

SymbolTable 是语言语义与内存模型之间的桥梁。

### 4.4 VMWriter（代码生成）

- push / pop
- arithmetic
- label / goto / if-goto
- call / return

编译结果直接输出 VM 指令，由前一阶段 VM Translator 执行。

---

## 5️⃣ 系统验证：Pong 游戏

### 编译链路

```text
Jack
 ↓
VM
 ↓
Hack Assembly
 ↓
Hack Binary
 ↓
CPU Emulator
```

### 为什么 Pong 是终极验证

- 对象与方法
- 数组操作
- 控制流
- 函数调用
- I/O

> 如果编译器、VM 或调用协议有任何细微错误，Pong 都无法运行。

**结果：Pong 正常运行，系统闭环完成。**

---

## 6️⃣ 工程层面的收获

- 编译器并非魔法，而是协议的组合
- 抽象层可以被亲手构建
- 正确性来自严格定义与边界
- Debug 能力显著提升

---

## 7️⃣ 总结

> 这次实现让我第一次真正理解了：程序在机器上是如何存在和运行的。

这不是“课程作业”，而是一次**完整计算机系统的工程实现**。

---

## 8️⃣ 使用示例

```bash
# 汇编器
python3 -m nand2tetris.cli asm Prog.asm

# VM 翻译器
python3 -m nand2tetris.cli vm Prog.vm

# Jack 编译器
python3 -m nand2tetris.cli jack Prog.jack
```

---

## License

Educational / Personal Use
