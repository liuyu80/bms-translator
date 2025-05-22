# 更新版本号脚本
# 将src/ui.py中的version = '<version>'替换为最新的git tag版本

# 检查git是否可用
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "错误: git命令不可用，请确保已安装git并添加到PATH" -ForegroundColor Red
    exit 1
}

Write-Host "信息: git命令可用。" -ForegroundColor Green

# 检查当前目录是否是git仓库
try {
    $gitRoot = git rev-parse --show-toplevel
    Write-Host "信息: 当前目录是git仓库，根目录为 '$gitRoot'" -ForegroundColor Green
} catch {
    Write-Host "错误: 当前目录不是git仓库。请在git仓库中运行此脚本。" -ForegroundColor Red
    exit 1
}

# 获取最新的git tag
Write-Host "信息: 正在获取最新的git tag..." -ForegroundColor Cyan
$latestTag = git describe --tags --abbrev=0
if (-not $latestTag) {
    Write-Host "错误: 没有找到git tag。请确保至少有一个git tag存在。" -ForegroundColor Red
    exit 1
}
Write-Host "信息: 获取到最新的git tag: '$latestTag'" -ForegroundColor Green

# 替换ui.py中的版本号
$uiPath = Join-Path $gitRoot "src/ui.py"
Write-Host "信息: 正在检查文件路径: '$uiPath'" -ForegroundColor Cyan
if (-not (Test-Path $uiPath)) {
    Write-Host "错误: 找不到ui.py文件。请确保文件存在于 '$uiPath'" -ForegroundColor Red
    exit 1
}
Write-Host "信息: 找到ui.py文件: '$uiPath'" -ForegroundColor Green

# 读取文件内容并替换版本号
try {
    $content = Get-Content $uiPath -Raw
    Write-Host "信息: 成功读取文件内容。" -ForegroundColor Green

    $versionPattern = "version\s*=\s*['`"].*?['`"]"
    $newVersionString = "version = '$latestTag'"
    
    if ($content -notmatch $versionPattern) {
        Write-Host "警告: ui.py中未找到版本字符串（例如 'version = \"v1.2.3\"'）。请检查src/ui.py文件内容。" -ForegroundColor Yellow
    } else {
        $newContent = $content -replace $versionPattern, $newVersionString
        
        if ($newContent -eq $content) {
            Write-Host "警告: 版本号替换操作未生效，可能是因为版本号已是最新或模式不匹配。当前版本可能已经是 '$latestTag'。" -ForegroundColor Yellow
        } else {
            # 写入新内容
            Set-Content -Path $uiPath -Value $newContent -NoNewline
            Write-Host "成功: 已将版本号更新为 '$latestTag'。" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "错误: 处理ui.py文件时发生异常: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}