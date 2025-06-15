# 实现“发送到”功能的详细计划

## 1. 修改 `src/ui.py` 以处理命令行参数 (已完成)

在 `src/ui.py` 的入口点（`if __name__ == "__main__":` 块）中，我们已经添加了代码来检查程序启动时是否带有命令行参数。

*   如果检测到命令行参数（即文件路径），程序将自动把该路径填充到文件路径输入框中，并立即触发文件解析过程，而无需用户手动点击“选择文件”和“开始解析”按钮。
*   如果没有命令行参数，程序将正常启动 GUI 界面，用户可以像往常一样手动选择文件进行操作。

**修改内容：**

```python
import sys

if __name__ == "__main__":
    bms_config = {}
    root = Tk()
    root.resizable(False, False)
    not_config_path()
    if os.path.exists('./config/bms.ico'):
        root.iconbitmap('./config/bms.ico')
    bms_config = read_bms_config('./config/bmsConfig.yaml') # type: ignore
    bms_config_backup = bms_config.copy()
    config = read_config('./config/config')
    win_width, win_height = creat_window()
    id_place, data_place, split_entry, valid_entry, file_path_entry, protocols_entry = creat_entry()

    set_config(config)
    creat_btn()
    
    bms_config = read_bms_config('./config/bmsConfig.yaml') # type: ignore

    # 检查命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        file_path_entry.delete(0, END)
        file_path_entry.insert(0, file_path)
        parse_file() # 自动解析文件
    
    root.mainloop()
```

## 2. 创建 Windows “发送到”快捷方式 (待您执行)

这一步需要在您的 Windows 系统上手动完成，以便将 `bms-translator` 添加到“发送到”菜单中。

### 步骤 A：找到“发送到”文件夹

1.  按下 `Win + R` 键打开“运行”对话框。
2.  输入 `shell:sendto` 并按回车。这将打开 Windows 的“发送到”文件夹。

### 步骤 B：创建快捷方式

1.  在该文件夹中，右键点击空白处，选择 `新建(N)` -> `快捷方式(S)`。
2.  在“创建快捷方式”向导中，点击 `浏览(B)...`。
3.  导航到您的 `bms-translator` 应用程序的可执行文件。
    *   如果您已经使用 PyInstaller 打包了项目，它通常位于项目的 `dist` 文件夹中，例如 `c:\Users\Windows\Desktop\openCode\bms-translator\dist\ui\ui.exe`。
    *   如果您是直接运行 Python 脚本，则需要指向 Python 解释器和 `src/ui.py` 脚本，例如 `C:\Python\Python39\python.exe "c:\Users\Windows\Desktop\openCode\bms-translator\src\ui.py"` (请根据您的 Python 安装路径和项目路径进行调整)。
4.  选择可执行文件后，点击 `确定`，然后点击 `下一步`。
5.  为快捷方式输入一个名称，例如 `bms-translator`。这个名称将显示在“发送到”菜单中。
6.  点击 `完成`。

## 流程图：

```mermaid
graph TD
    A[用户右键点击文件] --> B[选择发送到bms-translator]
    B --> C[Windows启动 bms-translator.exe 并传入文件路径作为参数]
    C --> D[bms-translator 应用程序启动]
    D --> E[检查 sys.argv 参数]
    E -- 有文件路径 --> F[将文件路径填充到UI界面]
    E -- 无文件路径 --> G[显示文件选择对话框]
    F --> H[自动触发文件解析]
    G --> I[用户手动选择文件并解析]
    H --> J[显示解析结果]
    I --> J