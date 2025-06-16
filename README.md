# BMS-translator

## 简介
本项目使用python语言开发, 自动将软件`CANalyst`保存的BMS数据进行翻译。

## 快速使用
1. 点击下载最新软件包 [下载地址](https://github.com/liuyu80/bms-translator/releases/latest)
2. 使用方法：解压后将exe程序添加桌面快捷方式, 双击运行程序, 选择要翻译的文件, 程序会自动使用系统默认应用打开翻译后的文件
3. 警告：**请勿删除移动config文件夹和其中的文件**

## 项目结构

```
.
├── config/                  # 配置文件目录
│   ├── bms.ico              # 应用程序图标
│   └── bmsConfig.yaml       # BMS协议配置，定义了各种报文的解析规则
├── data/                    # 示例数据文件
├── docs/                    # 文档目录
├── image/                   # 图片资源
├── src/                     # 源代码目录
│   ├── check_sys.py         # 系统检查相关函数
│   ├── main.py              # 核心逻辑，BMS数据解析与翻译
│   ├── ui.py                # 用户界面逻辑
│   └── utils.py             # 实用工具函数
├── .gitignore               # Git忽略文件配置
├── LICENSE                  # 许可证文件
├── pyproject.toml           # 项目构建配置
├── README.md                # 项目说明
├── requirements.txt         # Python依赖
├── ui.spec                  # PyInstaller打包配置
└── uv.lock                  # 依赖锁定文件
```

## 配置文件说明

本项目使用 `config/bmsConfig.yaml` 文件来定义BMS协议的解析规则。

### `bmsConfig.yaml` 结构

`bmsConfig.yaml` 文件包含了不同BMS协议（如 `GB2015`、`广州团标`、`宇通协议`、`特来电-车企大电流`）的详细配置。每个协议下定义了多种报文类型，每种报文类型包含以下字段：

- **`describe`**: 报文的描述。
- **`PGN`**: 报文的参数组编号（Parameter Group Number）。
- **`priority`**: 报文的优先级。
- **`total_bytes`**: 报文的总字节数。
- **`receive_send`**: 报文的接收和发送地址。
- **`optional_count`**: 可选计数。
- **`data`**: 报文的具体数据字段定义，每个字段包含：
  - **`bytes/bit`**: 字段的字节/位位置和长度，例如 `[1, 3]` 表示从第1个字节开始，长度为3个字节；`[6.1, 0.2]` 表示从第6个字节的第1位开始，长度为2个位。
  - **`options`**: 可选的枚举值翻译，例如 `'00: 正常; 01: 故障'`。
  - **`ratio`**: 比例因子，用于数值计算。
  - **`offset`**: 偏移量，用于数值计算。
  - **`unit_symbol`**: 单位符号，例如 `V`、`A`、`%`、`℃`、`min`。
  - **`type`**: 数据类型，例如 `int`、`ascii`、`BCD`。
  - **`components`**: 如果字段包含子组件，则在此处定义。
  - **`schema`**: 定义了 `components` 的翻译模板和顺序。

### 自定义协议

如果您需要添加或修改BMS协议，可以直接编辑 `config/bmsConfig.yaml` 文件。请确保遵循上述结构，并正确定义每个报文和字段的解析规则。

## 提交bug
欢迎使用本项目, 有bug请[点击这里](https://github.com/liuyu80/bms-translator/issues)提交