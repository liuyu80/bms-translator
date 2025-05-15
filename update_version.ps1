# 更新版本号脚本
# 将src/ui.py中的version = '<version>'替换为最新的git tag版本

# 检查git是否可用
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "错误: git命令不可用，请确保已安装git并添加到PATH"
    exit 1
}

# 检查当前目录是否是git仓库
try {
    $gitRoot = git rev-parse --show-toplevel
} catch {
    Write-Host "错误: 当前目录不是git仓库"
    exit 1
}

# 获取最新的git tag
$latestTag = git describe --tags --abbrev=0
if (-not $latestTag) {
    Write-Host "错误: 没有找到git tag"
    exit 1
}

# 替换ui.py中的版本号
$uiPath = Join-Path $gitRoot "src/ui.py"
if (-not (Test-Path $uiPath)) {
    Write-Host "错误: 找不到ui.py文件"
    exit 1
}

# 读取文件内容并替换版本号
$content = Get-Content $uiPath -Raw
$newContent = $content -replace "version = '<version>'", "version = '$latestTag'"

# 写入新内容
Set-Content -Path $uiPath -Value $newContent -NoNewline

Write-Host "成功: 已将版本号更新为 $latestTag"